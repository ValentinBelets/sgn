#!/usr/bin/env python3
"""
embed_signs.py  –  Pre-compute CLIP image embeddings for all catalogue signs.

Reads:   traffic_signs/nsw_traffic_signs_unified.json   (see DATA_FILE below)
         traffic_signs/images/*                          (local images preferred; falls back to URL)
Writes:  traffic_signs/sign_embeddings.js               (JS constant file, loaded by the browser)

Run from repo root:
    pip install transformers torch pillow requests tqdm
    python traffic_signs/embed_signs.py

The output JS file defines a global constant SIGN_EMBEDDINGS — a mapping from
sign id to a Float32Array-compatible flat array of 512 normalised floats.
Add to your HTML with:
    <script src="sign_embeddings.js"></script>
before image_search.js.
"""

from __future__ import annotations

import json
import os
import sys
import base64
import struct
import io
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — adjust these if your paths or field names differ
# ---------------------------------------------------------------------------

REPO_ROOT   = Path(__file__).resolve().parent.parent
DATA_FILE   = REPO_ROOT / "traffic_signs" / "nsw_traffic_signs_unified.json"
IMAGES_DIR  = REPO_ROOT / "traffic_signs" / "images"
OUTPUT_FILE = REPO_ROOT / "traffic_signs" / "sign_embeddings.js"

# Field names in your JSON records — adjust if needed
FIELD_ID        = "sign_no"      # unique sign identifier
FIELD_IMAGE_URL = "image_url"    # remote image URL fallback
# Local image lookup tries: IMAGES_DIR/{sign_no}.{ext}, then the URL-derived filename

# CLIP model — must match the browser-side model in image_search.js
MODEL_ID = "openai/clip-vit-base-patch32"

# Batch size for GPU/MPS; reduce to 1 if you hit memory errors
BATCH_SIZE = 16

# ---------------------------------------------------------------------------

def load_data(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Handle both a bare list and {"signs": [...]} wrapper
    if isinstance(data, list):
        return data
    for key in ("signs", "data", "records", "items"):
        if key in data and isinstance(data[key], list):
            print(f"  Using data['{key}'] ({len(data[key])} records)")
            return data[key]
    raise ValueError(f"Could not find a list of sign records in {path}. "
                     "Adjust the load_data() function for your JSON shape.")


def open_image(sign: dict) -> "Image.Image | None":
    """Try local file first, then fall back to URL download."""
    from PIL import Image

    sign_id = sign.get(FIELD_ID, "")

    # 1. Try local image files
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        local = IMAGES_DIR / f"{sign_id}{ext}"
        if local.exists():
            if ext == ".svg":
                return rasterise_svg(local)
            try:
                return Image.open(local).convert("RGB")
            except Exception as e:
                print(f"    Warning: could not open {local}: {e}")

    # 2. Try the filename derived from image_url (local images are named this way)
    url = sign.get(FIELD_IMAGE_URL, "")
    if url:
        url_filename = url.split("/")[-1].split("?")[0]
        local_by_url = IMAGES_DIR / url_filename
        if local_by_url.exists():
            ext = Path(url_filename).suffix.lower()
            if ext == ".svg":
                return rasterise_svg(local_by_url)
            try:
                return Image.open(local_by_url).convert("RGB")
            except Exception as e:
                print(f"    Warning: could not open {local_by_url}: {e}")

    # 3. Fall back to URL download
    if url:
        try:
            import requests
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            print(f"    Warning: could not fetch {url}: {e}")

    return None


def rasterise_svg(path: Path) -> "Image.Image | None":
    """Rasterise an SVG to PIL Image. Requires cairosvg or Inkscape."""
    try:
        import cairosvg
        from PIL import Image
        png_bytes = cairosvg.svg2png(url=str(path), output_width=224, output_height=224)
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except ImportError:
        pass
    # Fallback: Inkscape CLI
    try:
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            subprocess.run(
                ["inkscape", "--export-type=png", f"--export-filename={tmp.name}",
                 "--export-width=224", str(path)],
                check=True, capture_output=True
            )
            from PIL import Image
            return Image.open(tmp.name).convert("RGB")
    except Exception:
        pass
    print(f"    Warning: SVG rasterisation failed for {path} (install cairosvg or Inkscape)")
    return None


def compute_embeddings(signs: list[dict]) -> dict[str, list[float]]:
    """Return {sign_id: [512 floats]} for every sign with a loadable image."""
    import torch
    from transformers import CLIPProcessor, CLIPModel
    from tqdm import tqdm

    print(f"\nLoading CLIP model ({MODEL_ID})...")
    device = (
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"  Device: {device}")

    model     = CLIPModel.from_pretrained(MODEL_ID).to(device).eval()
    processor = CLIPProcessor.from_pretrained(MODEL_ID)

    embeddings: dict[str, list[float]] = {}
    skipped = 0

    # Process in batches
    batch_ids:   list[str]           = []
    batch_imgs:  list["Image.Image"] = []

    def flush_batch():
        nonlocal batch_ids, batch_imgs
        if not batch_imgs:
            return
        inputs = processor(images=batch_imgs, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            feats = model.get_image_features(**inputs)
            # transformers 5.x may return a model output object instead of a tensor
            if not isinstance(feats, torch.Tensor):
                if hasattr(feats, 'image_embeds'):
                    feats = feats.image_embeds
                elif hasattr(feats, 'pooler_output'):
                    feats = feats.pooler_output
                else:
                    feats = feats[0]
            feats = feats / feats.norm(dim=-1, keepdim=True)  # L2 normalise
        for i, sid in enumerate(batch_ids):
            embeddings[sid] = feats[i].cpu().tolist()
        batch_ids.clear()
        batch_imgs.clear()

    for sign in tqdm(signs, desc="Embedding signs"):
        sid = str(sign.get(FIELD_ID, ""))
        if not sid:
            skipped += 1
            continue

        img = open_image(sign)
        if img is None:
            print(f"  Skipping {sid} — no image found")
            skipped += 1
            continue

        batch_ids.append(sid)
        batch_imgs.append(img)

        if len(batch_imgs) >= BATCH_SIZE:
            flush_batch()

    flush_batch()

    print(f"\nEmbedded: {len(embeddings)}  |  Skipped: {skipped}")
    return embeddings


def embeddings_to_base64(emb_map: dict[str, list[float]]) -> dict[str, str]:
    """
    Pack each 512-float embedding into a base64 string of 512×4 = 2048 bytes.
    In the browser this is unpacked with new Float32Array(base64decode(str).buffer).
    At ~1000 signs this keeps the JS file around 1.5 MB vs ~4 MB as plain JSON.
    """
    out: dict[str, str] = {}
    for sid, floats in emb_map.items():
        packed = struct.pack(f"{len(floats)}f", *floats)
        out[sid] = base64.b64encode(packed).decode("ascii")
    return out


def write_js(b64_map: dict[str, str], path: Path) -> None:
    payload = json.dumps(b64_map, separators=(",", ":"))
    js = (
        "// Auto-generated by embed_signs.py — do not edit manually.\n"
        "// Each value is a base64-encoded Float32Array (512 dims, L2-normalised).\n"
        f"var SIGN_EMBEDDINGS={payload};\n"
    )
    path.write_text(js, encoding="utf-8")
    size_kb = path.stat().st_size / 1024
    print(f"Wrote {path}  ({size_kb:.0f} KB)")


def main() -> None:
    if not DATA_FILE.exists():
        sys.exit(f"Data file not found: {DATA_FILE}\nAdjust DATA_FILE in this script.")

    print(f"Reading {DATA_FILE} ...")
    signs = load_data(DATA_FILE)
    print(f"  {len(signs)} sign records loaded.")

    t0 = time.time()
    emb_map = compute_embeddings(signs)
    print(f"Embedding took {time.time() - t0:.1f}s")

    b64_map = embeddings_to_base64(emb_map)
    write_js(b64_map, OUTPUT_FILE)

    print("\nDone. Add these two lines to your HTML (before </body>):")
    print('  <script src="sign_embeddings.js"></script>')
    print('  <script src="image_search.js"></script>')


if __name__ == "__main__":
    main()
