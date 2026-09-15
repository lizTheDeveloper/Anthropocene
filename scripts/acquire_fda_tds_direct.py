"""FDA Total Diet Study -- discover and retrieve direct from the agency.

TDS analyses foods prepared as consumed for pesticides, toxic elements and
nutrients in ONE sampling frame, at detection limits 10-100x below the
regulatory programme. That single-frame property is why it matters more than
its size suggests: it is the only federal source where "residues up, nutrients
down" can be tested without joining two incompatible sampling designs.

Discovery reads the live results page (FDA is reachable from this network), so
the index is reproducible rather than a one-off artifact that dies with the
machine -- which is exactly what happened to its predecessor.
"""
import json, re, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch, session

AGENCY, DATASET = "fda", "total-diet-study"
OUT = pathlib.Path("data/raw/fda/_discovery"); OUT.mkdir(parents=True, exist_ok=True)
PAGES = [
    "https://www.fda.gov/food/fda-total-diet-study-tds/fda-total-diet-study-tds-results",
    "https://www.fda.gov/food/fda-total-diet-study-tds/fda-total-diet-study-tds-analytes-and-analytical-methods",
    "https://www.fda.gov/food/fda-total-diet-study-tds/fda-total-diet-study-tds-design-and-implementation",
    "https://www.fda.gov/food/fda-total-diet-study-tds/fda-total-diet-study-tds-foods-and-dietary-exposure-estimation",
]
s = session()
found = {}
for url in PAGES:
    try:
        r = s.get(url, timeout=120)
    except Exception as e:
        print(f"{url.split('/')[-1]}: ERROR {type(e).__name__}"); continue
    if r.status_code != 200:
        print(f"{url.split('/')[-1]}: HTTP {r.status_code}"); continue
    (OUT / f"tds_{url.split('/')[-1]}.html").write_text(r.text)
    for m in re.finditer(r'href="([^"]*?(?:/media/\d+/download|\.xlsx|\.xls|\.csv|\.zip)[^"]*)"[^>]*>(.{0,180}?)</a>',
                         r.text, re.S):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).replace("\xa0", " ").strip()
        href = m.group(1).split("?")[0]
        if href.startswith("/"):
            href = "https://www.fda.gov" + href
        found.setdefault(href, label or "tds_file")
    print(f"{url.split('/')[-1]}: {len(found)} unique files so far")
    time.sleep(1)

(OUT / "tds_file_index.json").write_text(json.dumps(
    [{"url": u, "label": l} for u, l in found.items()], indent=2))
print(f"\n{len(found)} TDS files discovered\n")

ok = fail = 0
for url, label in found.items():
    mid = url.rstrip("/").split("/")[-2]
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in label)[:55].strip().replace(" ", "_")
    name = f"{slug or 'tds'}__media{mid}"
    r = fetch(url, AGENCY, DATASET, filename=name, subdir="files", sess=s, timeout=900,
              notes=f"TDS: {label} (direct from agency)")
    if r["ok"]:
        ok += 1; print(f"  [ok  ] {r['bytes']:>10,}  {name}")
    else:
        fail += 1; print(f"  [FAIL] {r['status']}  {name}")
    time.sleep(0.8)
print(f"\nTDS: {ok} ok, {fail} failed")
