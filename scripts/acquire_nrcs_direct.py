"""NRCS RaCA and NRI -- direct-from-agency acquisition via wget.

NRCS serves wget but refuses curl and python-requests from the same host (see
fetchlib.fetch_via_wget for the diagnosis). That makes these files retrievable
first-party rather than only as Internet Archive copies, and it is the only way
to get the 2022 NRI Summary Report intact: the single archived capture is
truncated at 5 MiB, while the agency serves the full 12.7 MB.
"""
import sys, time; sys.path.insert(0, 'scripts')
from fetchlib import fetch_via_wget

F = "https://www.nrcs.usda.gov/sites/default/files/"

NRI_REPORTS = [
    (F + "2026-02/2022%20NRI%20Summary%20Report.pdf", "2022_NRI_Summary_Report.pdf",
     "2022 NRI Summary Report (Sept 2025) -- erosion by state/year, erosion relative to T. "
     "Use THIS release for both current and historical values; NRI back-updates prior years."),
    (F + "2022-10/2017NRISummary_Final.pdf", "2017NRISummary_Final.pdf",
     "2017 NRI Summary Report -- superseded by the 2022 release for trend use"),
    (F + "2022-10/2007AlaskaNRI.pdf", "2007AlaskaNRI.pdf", "Alaska NRI 2007"),
    (F + "2022-09/Historical-Changes-In-Soil-Erosion_5.pdf", "Historical-Changes-In-Soil-Erosion.pdf",
     "NRCS historical soil erosion change analysis"),
]
NRI_CODEBOOKS = [
    (F + "2022-10/NRI_glossary.pdf", "NRI_glossary.pdf", "NRI glossary"),
    (F + "2022-10/NRI_history.pdf", "NRI_history.pdf", "NRI programme history and design changes"),
    (F + "2022-10/NRI_data_estimation.pdf", "NRI_data_estimation.pdf",
     "NRI estimation methodology -- documents the backward-update procedure"),
]
SOILS_REFRESH = [
    (F + f"2025-09/{y}-Annual-Soils-Refresh.pdf", f"{y}-Annual-Soils-Refresh.pdf",
     f"SSURGO {y} refresh notes -- non-physical causes of value change")
    for y in (2021, 2022, 2023, 2024, 2025)
]
RACA = [(F + "2022-10/" + n, n, "RaCA methodology / regional summary") for n in
        ["RaCA_Methodology_Sampling_Summary.pdf", "Location_Instructions.pdf",
         "Alter_Site_Location.pdf", "RaCA_Field_Collection_Protocols.pdf",
         "Rapid_Carbon_Assessment_Field_Laboratory_Instructions.pdf",
         "Region_Soil_Components_Groups.xlsx", "Rapid_Carbon_Assessment_Workbook_215.xlsx",
         "RaCA_LUGRmap.pdf", "RaCA_regionmap.pdf", "RaCA_sitesmap.pdf"] +
        [f"RaCA_region{i}.pdf" for i in list(range(1, 17)) + [18]]]

def run(group, agency, dataset, sub):
    ok = fail = 0
    print(f"\n== {dataset}/{sub} ==")
    for url, name, note in group:
        r = fetch_via_wget(url, agency, dataset, filename=name, subdir=sub, notes=note)
        if r["ok"]:
            ok += 1; print(f"  [ok  ] {r['bytes']:>12,}  {name}", flush=True)
        else:
            fail += 1; print(f"  [FAIL] {r['status']}  {name}", flush=True)
        time.sleep(0.6)
    return ok, fail

t_ok = t_fail = 0
for grp, ds, sub in [(NRI_REPORTS, "nri", "reports"), (NRI_CODEBOOKS, "nri", "codebooks"),
                     (SOILS_REFRESH, "nri", "soils-refresh"), (RACA, "raca", "docs")]:
    o, f_ = run(grp, "usda-nrcs", ds, sub); t_ok += o; t_fail += f_
print(f"\nNRCS direct: {t_ok} ok, {t_fail} failed")
