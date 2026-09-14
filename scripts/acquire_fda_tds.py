"""FDA Total Diet Study -- residues, toxic elements and nutrients in the same samples.

TDS analyses foods PREPARED AS CONSUMED (oranges peeled, noodles cooked) for
pesticides, toxic elements, and nutrients within one sampling frame, at
detection limits 10-100x lower than the regulatory programme (down to 0.1 ppb).

That single-frame property is why this dataset matters more than its size
suggests: it is the only federal source where "residues up, nutrients down" can
be tested without joining two incompatible sampling designs.

Retrieved from the Internet Archive; FDA's edge returns 401 to this network.
"""
import json, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch_via_wayback, session

AGENCY, DATASET = "fda", "total-diet-study"
files = json.loads(pathlib.Path("data/raw/fda/_discovery/tds_file_index.json").read_text())
s = session()

def name_for(f):
    lab = f["label"].replace("&nbsp;", " ").strip()
    mid = f["url"].rstrip("/").split("/")[-2]      # the media id keeps names unique
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in lab)[:60].strip().replace(" ", "_")
    return f"{slug or 'tds_file'}__media{mid}"

ok = fail = 0
for f in files:
    r = fetch_via_wayback(f["url"], AGENCY, DATASET, filename=name_for(f),
                          subdir="FY2018-FY2020", sess=s,
                          notes=f"TDS: {f['label'].replace('&nbsp;',' ')}")
    if r["ok"]:
        ok += 1; print(f"  [ok ] {r['bytes']:>10,}  {name_for(f)}  (capture {r.get('capture')})", flush=True)
    else:
        fail += 1; print(f"  [FAIL] {name_for(f)}: {r['status']}", flush=True)
    time.sleep(2.5)
print(f"\nTDS: {ok} ok, {fail} failed")
