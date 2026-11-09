#!/usr/bin/env python3
"""Edition / standard-part cross-check on NSW<->SA matched signs.

Finding to confirm: NSW publishes the AS standard *part* (AS1742.2) but no edition
year; SA publishes editions (AS1742.2-2009 vs 2022). So true edition-drift is one-
sided. What IS comparable is the standard *part* each authority assigns to the same
sign. We sample matched signs, fetch SA's references, and compare parts.
"""
import json, re, ssl, urllib.request as U, certifi
from pathlib import Path

ctx = ssl.create_default_context(cafile=certifi.where())
API = "https://d2pagjgnt5.execute-api.ap-southeast-2.amazonaws.com/Production/api/v1"
NSW = Path("/Users/valentinbelets/code/_sgn/traffic_signs/nsw_traffic_signs.json")
SA = Path("/tmp/sa_api_signs.json")
SAMPLE = 80

AS_LIKE = re.compile(r"^[A-Z]{1,3}\d")
def strip_common(s):
    s = re.sub(r"\[.*?\]", "", re.sub(r"\(.*?\)", "", s.strip().upper())); return s.strip()
def norm_nsw(c):
    return re.sub(r"(?<=\d)N$", "", strip_common(c)).strip(" -")
def norm_sa(c):
    s = re.sub(r"\s*MOD\s*$", "", strip_common(c)); return re.sub(r"(?<=\d)[A-Z]+$", "", s).strip(" -")

def as_part(name):  # "AS1742.2 2022" / "AS1742.2-2009" / "AS 1742.2 (Traffic Signals)" -> "AS1742.2"
    m = re.search(r"AS\s?(\d+)\.(\d+)", name.upper())
    return f"AS{m.group(1)}.{m.group(2)}" if m else None
def as_edition(name):
    m = re.search(r"(19|20)\d{2}", name); return m.group(0) if m else None

def get(url):
    try:
        return json.loads(U.urlopen(U.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20, context=ctx).read())
    except Exception as e:
        return {"__err__": str(e)}

# reference id -> name
refs = {r["id"]: r["name"] for r in json.loads(Path("/tmp/sa_refs.json").read_text())}

# NSW: base key -> AS part (from primary_technical_reference)
nsw_part = {}
for r in json.loads(NSW.read_text()):
    c = r.get("sign_no")
    if not c: continue
    k = norm_nsw(str(c))
    if AS_LIKE.match(k):
        nsw_part.setdefault(k, as_part(r.get("primary_technical_reference") or ""))

# SA: base key -> one representative sign id
sa_sign = {}
for r in json.loads(SA.read_text()):
    for d in (r.get("detail") or []):
        c = d.get("code")
        if not c: continue
        k = norm_sa(str(c))
        if AS_LIKE.match(k):
            sa_sign.setdefault(k, r["id"])

matched = sorted(set(nsw_part) & set(sa_sign))
print(f"matched base keys: {len(matched)}  | sampling {min(SAMPLE, len(matched))}")

agree = disagree = nsw_blank = sa_blank = 0
editions_seen = set()
rows = []
for k in matched[:SAMPLE]:
    sign = get(f"{API}/signs/{sa_sign[k]}")
    sa_refs = [refs.get(x["referenceId"], "") for x in (sign.get("signReference") or [])]
    sa_parts = {as_part(n) for n in sa_refs if as_part(n)}
    for n in sa_refs:
        if as_edition(n): editions_seen.add(n)
    np = nsw_part.get(k)
    if not np: nsw_blank += 1
    if not sa_parts: sa_blank += 1
    if np and sa_parts:
        if np in sa_parts: agree += 1
        else:
            disagree += 1
            rows.append((k, np, ",".join(sorted(sa_parts))))

print(f"\nAgree on standard part : {agree}")
print(f"Disagree               : {disagree}")
print(f"NSW part blank         : {nsw_blank}")
print(f"SA refs blank          : {sa_blank}")
print(f"\nSA editions actually published (sample): {sorted(editions_seen)[:12]}")
print("\n-- disagreements (base key | NSW part | SA parts) --")
for k, np, sp in rows[:20]:
    print(f"  {k:<12} NSW={np:<10} SA={sp}")
