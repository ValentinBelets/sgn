#!/usr/bin/env python3
"""Non-destructive TfNSW re-scrape: certifi SSL context + output to a temp file,
so we can diff against the committed baseline without clobbering it."""
import ssl, sys, certifi
from pathlib import Path

# Fix macOS "CERTIFICATE_VERIFY_FAILED" without editing the committed scraper.
ssl._create_default_https_context = lambda *a, **k: ssl.create_default_context(cafile=certifi.where())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "traffic_signs"))
import scrape_signs  # noqa: E402

scrape_signs.OUTPUT_PATH = Path("/tmp/nsw_fresh.json")  # do NOT overwrite the baseline
scrape_signs.scrape_all()
