"""NHANES -- does any of this show up in people?

Two linked roles:
  * Laboratory biochemical indicators (ferritin, serum/RBC folate, B12, zinc,
    selenium, copper, vitamin D, carotenoids) -- nutritional STATUS, which is
    the outcome a food-nutrient-density argument ultimately claims to affect.
  * Urinary pesticide metabolites (organophosphate DAPs, pyrethroid 3-PBA,
    glyphosate/AMPA in recent cycles) -- exposure, measured in the SAME
    individuals as the biomarkers above.

That co-measurement is what links the exposure pillar to the health pillar
without a cross-frame join. Note the glyphosate panels (SSGLYP_H/I/J) are
SURPLUS-specimen subsamples, not the full NHANES sample -- they carry their own
weights and cannot be treated as nationally representative without care.

Documentation (.htm) is fetched next to each .XPT; NHANES variable names are
opaque without it.
"""
import json, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch, session

AGENCY, DATASET = "cdc-nhanes", "lab-and-dietary"
rows = json.loads(pathlib.Path("data/raw/cdc-nhanes/_discovery/nhanes_index.json").read_text())

KEY = ["glyphosate", "pesticide", "organophosphate", "pyrethroid", "herbicide",
       "ferritin", "folate", "vitamin", "zinc", "selenium", "copper", "carotenoid",
       "b12", "iron", "dietary interview", "total nutrient"]
sel = [r for r in rows if any(k in (r["name"] + r["xpt"]).lower() for k in KEY)]
print(f"{len(sel)} files selected of {len(rows)} indexed")

s = session()
ok = fail = 0
for r in sel:
    cycle = (r["cycle"] or "unknown").replace(" ", "")
    res = fetch(r["xpt"], AGENCY, DATASET, subdir=f"{cycle}/data", sess=s, timeout=900,
                notes=f"NHANES {r['component']} {cycle}: {r['name']}")
    if res["ok"]:
        ok += 1
    else:
        fail += 1
    print(f"  [{'ok ' if res['ok'] else 'FAIL'}] {res.get('bytes',0):>10,}  {cycle} {r['xpt'].split('/')[-1]}", flush=True)
    if r.get("doc"):
        fetch(r["doc"], AGENCY, DATASET, subdir=f"{cycle}/docs", sess=s, timeout=300,
              notes=f"NHANES codebook for {r['xpt'].split('/')[-1]}")
    time.sleep(0.8)
print(f"\nNHANES: {ok} ok, {fail} failed")
