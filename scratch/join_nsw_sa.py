#!/usr/bin/env python3
"""Throwaway: join NSW (sign_no) and SA (detail[].code) on a canonical AS base key.

Per-source decoration rules reduce each dialect to the shared Australian Standards
base code, then we intersect. Proves how much the two catalogues actually overlap.
"""
import json
import re
import sys
from pathlib import Path

NSW = Path("/Users/valentinbelets/code/_sgn/traffic_signs/nsw_traffic_signs.json")
SA = Path("/tmp/sa_api_signs.json")

AS_LIKE = re.compile(r"^[A-Z]{1,3}\d")  # e.g. R4-1, D4-5-1, GE9-200, W5-230


def strip_common(s: str) -> str:
    s = s.strip().upper()
    s = re.sub(r"\(.*?\)", "", s)   # orientation (L)/(R) or notes
    s = re.sub(r"\[.*?\]", "", s)   # bracketed size [A]
    return s.strip()


def norm_nsw(code: str) -> str:
    s = strip_common(code)
    s = re.sub(r"(?<=\d)N$", "", s)      # NSW variant suffix n -> drop
    return s.strip(" -")


def norm_sa(code: str) -> str:
    s = strip_common(code)
    s = re.sub(r"\s*MOD\s*$", "", s)     # SA "modified" marker G7-1-1A MOD -> G7-1-1A
    # NOTE: do NOT collapse D4-SA… -> ambiguous (SA-local number, not a shared base)
    s = re.sub(r"(?<=\d)[A-Z]+$", "", s) # trailing size letters D4-1-1A -> D4-1-1
    return s.strip(" -")


def collect(path, extract, norm):
    raw = json.loads(path.read_text())
    keys, dropped = {}, 0
    for row in raw:
        for code in extract(row):
            if not code or str(code).lower() == "null":
                continue
            k = norm(str(code))
            if not AS_LIKE.match(k):   # keep only AS-catalogue-style codes
                dropped += 1
                continue
            keys.setdefault(k, str(code))
    return keys, dropped


nsw_keys, nsw_drop = collect(NSW, lambda r: [r.get("sign_no")], norm_nsw)
sa_keys, sa_drop = collect(
    SA, lambda r: [d.get("code") for d in (r.get("detail") or [])], norm_sa
)

nsw_set, sa_set = set(nsw_keys), set(sa_keys)
both = nsw_set & sa_set
nsw_only = nsw_set - sa_set
sa_only = sa_set - nsw_set

print(f"NSW distinct AS base keys : {len(nsw_set):>5}  (non-AS codes dropped: {nsw_drop})")
print(f"SA  distinct AS base keys : {len(sa_set):>5}  (non-AS codes dropped: {sa_drop})")
print(f"MATCH (in both)           : {len(both):>5}")
print(f"  = {100*len(both)/len(nsw_set):.1f}% of NSW   |   {100*len(both)/len(sa_set):.1f}% of SA")
print(f"NSW-only                  : {len(nsw_only):>5}")
print(f"SA-only                   : {len(sa_only):>5}")

print("\n-- sample matches (base key : NSW raw / SA raw) --")
for k in sorted(both)[:20]:
    print(f"  {k:<14} NSW={nsw_keys[k]:<16} SA={sa_keys[k]}")

DRG = re.compile(r"DRG|^\D*\d{5,}")  # SA drawing numbers, not AS signs

def classify(keys, only):
    variant = [k for k in only if "N" == strip_common(keys[k])[-1:] or "SA" in keys[k].upper()]
    drawing = [k for k in only if DRG.search(keys[k].upper())]
    clean = [k for k in only if k not in set(variant) | set(drawing)]
    return variant, drawing, clean

nsw_var, nsw_drg, nsw_clean = classify(nsw_keys, nsw_only)
sa_var, sa_drg, sa_clean = classify(sa_keys, sa_only)

print("\n== GAP CLASSIFICATION ==")
print(f"NSW-only {len(nsw_only)}: state-variant={len(nsw_var)}  drawing-no={len(nsw_drg)}  clean-AS-absent={len(nsw_clean)}")
print(f"SA-only  {len(sa_only)}: state-variant={len(sa_var)}  drawing-no={len(sa_drg)}  clean-AS-absent={len(sa_clean)}")

print("\n-- clean NSW-only (AS codes SA genuinely lacks), sample --")
for k in sorted(nsw_clean)[:20]:
    print(f"  {k:<14} (raw {nsw_keys[k]})")

print("\n-- clean SA-only (AS codes NSW genuinely lacks), sample --")
for k in sorted(sa_clean)[:20]:
    print(f"  {k:<14} (raw {sa_keys[k]})")
