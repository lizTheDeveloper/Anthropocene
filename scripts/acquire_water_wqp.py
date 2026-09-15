"""EPA/USGS Water Quality Portal -- pesticide occurrence in surface and ground water.

WQP federates USGS NWIS, EPA STORET and state monitoring behind one API, which
makes it the cheapest route to national pesticide occurrence data.

The compound list is derived from the PNSP data already in custody (top
agricultural-use compounds by 2012 national high estimate) rather than chosen by
hand, so the water pillar is anchored to the same compounds as the use pillar.
Glyphosate leads use by a factor of four over the next compound, but is
historically under-monitored in water because it needs a dedicated method -- a
low detection count for glyphosate is a monitoring artifact, not an absence, and
must not be read as one.

Results are pulled per compound so a single failure does not lose the batch, and
station metadata is pulled alongside because a Result row without its
MonitoringLocation is not locatable.
"""
import sys, time; sys.path.insert(0, 'scripts')
from fetchlib import fetch, session

AGENCY, DATASET = "epa-usgs-wqp", "pesticide-water-quality"
BASE = "https://www.waterqualitydata.us/data"

# Top agricultural-use compounds from PNSP 2012, restricted to those with
# meaningful water-monitoring coverage (fumigants and oils are omitted -- they
# are not routinely analysed in water and would return empty sets).
COMPOUNDS = [
    "Glyphosate", "Atrazine", "Metolachlor", "2,4-D", "Acetochlor",
    "Pendimethalin", "Chlorothalonil", "Trifluralin", "Chlorpyrifos",
    "Paraquat", "Alachlor", "Dicamba", "Simazine", "Acephate",
    "Glufosinate", "Metribuzin", "Imidacloprid", "Diuron",
]
START = "01-01-2000"

s = session()
ok = fail = 0
for c in COMPOUNDS:
    slug = c.replace(",", "").replace(" ", "_").replace("-", "")
    r = fetch(f"{BASE}/Result/search", AGENCY, DATASET,
              filename=f"wqp_results_{slug}.csv", subdir="results", sess=s, timeout=2400,
              params={"characteristicName": c, "startDateLo": START,
                      "mimeType": "csv", "zip": "no", "dataProfile": "resultPhysChem"},
              notes=f"WQP Result records for {c}, sample date >= {START}",
              license="Public domain (federal) / varies by contributing state agency")
    if r["ok"]:
        ok += 1
    else:
        fail += 1
    print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>12,}  {c}", flush=True)
    time.sleep(3)

print("\n== station metadata ==")
for c in ["Glyphosate", "Atrazine", "Chlorpyrifos"]:
    slug = c.replace(",", "").replace(" ", "_")
    r = fetch(f"{BASE}/Station/search", AGENCY, DATASET,
              filename=f"wqp_stations_{slug}.csv", subdir="stations", sess=s, timeout=1800,
              params={"characteristicName": c, "startDateLo": START, "mimeType": "csv", "zip": "no"},
              notes=f"WQP monitoring locations sampled for {c}")
    print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>12,}  stations/{c}", flush=True)
    time.sleep(3)
print(f"\nWQP: {ok} compound result sets ok, {fail} failed")
