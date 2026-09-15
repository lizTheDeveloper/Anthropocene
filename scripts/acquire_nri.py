"""NRCS National Resources Inventory -- erosion trend backbone.

Statistical panel survey of non-Federal land on a consistent sample since 1982.
Carries sheet-and-rill and wind erosion by state and year, and erosion relative
to T (tolerable soil loss) by land cover/use and year.

CRITICAL METHOD NOTE, from NRI's own documentation: each release
BACKWARD-UPDATES prior years so that observed change is real change rather than
collection-method drift. Never compare a 2022 NRI figure against a figure
published in the 2017 NRI. Take both current and historical values from a
single release, or the trend line is an artifact of the methodology.

NRCS resets connections from this network on every /sites/ path, so bytes come
from the Internet Archive (tagged VIA_WAYBACK).
"""
import sys, time; sys.path.insert(0, 'scripts')
from fetchlib import fetch_via_wayback, session

AGENCY, DATASET = "usda-nrcs", "nri"
B = "https://www.nrcs.usda.gov/sites/default/files/"

reports = [
    (B + "2022-10/2017NRISummary_Final.pdf", "2017NRISummary_Final.pdf",
     "2017 NRI Summary Report -- erosion tables; superseded by 2022 release for trend use"),
    (B + "2022-10/2007AlaskaNRI.pdf", "2007AlaskaNRI.pdf", "Alaska NRI 2007"),
    (B + "2022-09/Historical-Changes-In-Soil-Erosion_5.pdf", "Historical-Changes-In-Soil-Erosion.pdf",
     "NRCS historical soil erosion change analysis"),
]
codebooks = [
    (B + "2022-10/NRI_glossary.pdf", "NRI_glossary.pdf", "NRI glossary -- term definitions"),
    (B + "2022-10/NRI_history.pdf", "NRI_history.pdf", "NRI programme history and design changes"),
    (B + "2022-10/NRI_data_estimation.pdf", "NRI_data_estimation.pdf",
     "NRI estimation methodology -- explains the backward-update procedure"),
]
# The annual Soils Refresh notes document what changed in SSURGO each October.
# They are the evidence that SSURGO vintage differences are editorial, not physical.
refresh = [
    (B + f"2025-09/{y}-Annual-Soils-Refresh.pdf", f"{y}-Annual-Soils-Refresh.pdf",
     f"SSURGO {y} refresh notes -- documents non-physical causes of value change")
    for y in (2021, 2022, 2023, 2024, 2025)
]

s = session()
for group, sub in [(reports, "reports"), (codebooks, "codebooks"), (refresh, "soils-refresh")]:
    print(f"\n== {sub} ==")
    for url, name, note in group:
        r = fetch_via_wayback(url, AGENCY, DATASET, filename=name, subdir=sub, sess=s, notes=note)
        print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>10,}  {name}", flush=True)
        time.sleep(2)
