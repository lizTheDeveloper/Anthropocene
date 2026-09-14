"""NRCS Rapid Carbon Assessment (RaCA) -- methodology and regional summaries.

31,215 pedons across the conterminous US, sampled ~2010-11 under a multilevel
stratified random design, with soil organic carbon, total N, and bulk density.

RaCA is a SINGLE-TIMEPOINT BASELINE, not a time series. It establishes the
2010-11 state of SOC by land use and cannot by itself demonstrate decline. Its
value here is as the stratification frame and as the comparison baseline for
NCSS repeat-sampled pedons.

Use the current NRCS distribution rather than the SoilWeb snapshot: the
soilDB::fetchRaCA() path is deprecated and returns VNIR-spectra-ESTIMATED SOC
rather than Kellogg lab-MEASURED SOC. That distinction decides whether a
measured-carbon claim survives review.

NRCS resets connections from this network on every /sites/ and /resources/
path, so bytes come from the Internet Archive (tagged VIA_WAYBACK).
"""
import sys, time; sys.path.insert(0, 'scripts')
from fetchlib import fetch_via_wayback, session

B = "https://www.nrcs.usda.gov/sites/default/files/2022-10/"
AGENCY, DATASET = "usda-nrcs", "raca"

docs = [
    "RaCA_Methodology_Sampling_Summary.pdf",
    "Location_Instructions.pdf",
    "Alter_Site_Location.pdf",
    "RaCA_Field_Collection_Protocols.pdf",
    "Rapid_Carbon_Assessment_Field_Laboratory_Instructions.pdf",
    "Region_Soil_Components_Groups.xlsx",
    "Rapid_Carbon_Assessment_Workbook_215.xlsx",
    "RaCA_LUGRmap.pdf",
    "RaCA_regionmap.pdf",
    "RaCA_sitesmap.pdf",
] + [f"RaCA_region{i}.pdf" for i in list(range(1, 17)) + [18]]

s = session()
ok = fail = 0
for d in docs:
    r = fetch_via_wayback(B + d, AGENCY, DATASET, filename=d, subdir="docs", sess=s,
                          notes="RaCA methodology / regional summary")
    if r["ok"]:
        ok += 1; print(f"  [ok ] {r['bytes']:>10,}  {d}  (capture {r.get('capture')})", flush=True)
    else:
        fail += 1; print(f"  [FAIL] {d}: {r['status']}", flush=True)
    time.sleep(2)
print(f"\nRaCA docs: {ok} ok, {fail} failed")
