"""USDA Ag Data Commons -- the long-term experiment data the national record lacks.

Every lens that hit a wall hit the same one: the national statistical products
(NRI, RaCA, PNSP, the Census) have breadth and no repeat measurement. The
repeat measurement exists, but it lives in station-scale experiments deposited
as datasets behind DOIs -- smaller n, far higher internal validity, and
invisible to anything that only crawls agency web pages.

Ag Data Commons runs on figshare, so its API is the access path; the
agdatacommons.nal.usda.gov front end answers a Cloudflare challenge and the
NAL CKAN endpoint indexes only part of it.

These specifically answer questions the national record could not:
  * temporal variability as a source of uncertainty in soil carbon measurement
    -- i.e. how many repeats you need before a change is real (Lal's gap)
  * subsurface carbon under long-term no-till -- the sampling-depth problem
    that decides whether no-till carbon gains survive (Six's gap)
  * yield AND profit on diversified vs conventional rotations -- two outcomes
    of the bundle measured on the same plots (Fonte's gap)
  * NUOnet, a nutrient-use outcome network -- an outcome scored as never
    nationally measured
"""
import json, sys, time, urllib.request
sys.path.insert(0, "scripts")
from fetchlib import fetch, session

AGENCY, DATASET = "usda-ars", "agdatacommons"
TARGETS = {
    25719348: "Temporal variability as a source of uncertainty in soil carbon measurement",
    27280725: "Subsurface carbon stocks under long-term no-tillage (sampling-depth problem)",
    32764923: "Multi-decadal grazing effects on soil organic carbon and nitrogen",
    27207915: "Yield and profit, diversified vs conventional rotations (two bundle outcomes, same plots)",
    24660981: "NUOnet -- Nutrient Use and Outcome Network database",
    33158549: "Long-term tillage effects on extractable organic matter fractions",
    26673769: "Tillage and cropping effects on soil quality indicators, northern Great Plains",
    24660822: "Microbial community structure under cropping sequence and poultry litter",
}

def meta(aid):
    try:
        with urllib.request.urlopen(f"https://api.figshare.com/v2/articles/{aid}", timeout=120) as r:
            return json.load(r)
    except Exception as e:
        print(f"  meta ERR {aid}: {type(e).__name__}"); return None

s = session()
ok = fail = 0
for aid, why in TARGETS.items():
    m = meta(aid)
    if not m:
        fail += 1; continue
    title = m.get("title", "")[:70]
    files = m.get("files", [])
    print(f"\n[{aid}] {title}")
    print(f"   doi:{m.get('doi')}  files:{len(files)}")
    print(f"   why: {why}")
    for f in files:
        name = f.get("name", f"file_{f.get('id')}")
        url = f.get("download_url")
        if not url:
            continue
        r = fetch(url, AGENCY, DATASET, filename=name, subdir=str(aid), sess=s, timeout=1800,
                  notes=f"Ag Data Commons {m.get('doi')} — {title} | acquired because: {why}",
                  license="see dataset licence; USDA-funded research data")
        if r["ok"]:
            ok += 1; print(f"     [ok  ] {r['bytes']:>12,}  {name[:64]}")
        else:
            fail += 1; print(f"     [FAIL] {r['status']}  {name[:64]}")
        time.sleep(0.6)
    time.sleep(1)
print(f"\nAg Data Commons: {ok} files retrieved, {fail} failed")
