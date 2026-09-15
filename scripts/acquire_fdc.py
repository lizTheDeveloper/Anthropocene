"""USDA FoodData Central -- current food composition values.

Two products matter here and they are NOT a continuous series:
  * SR Legacy (frozen 2018-04) -- the archived Standard Reference, ~7,800 items,
    many values carried forward from mid-20th-century analyses.
  * Foundation Foods -- forward-going, analytically derived, with per-sample
    provenance and a different sampling design.
Comparing SR Legacy against Foundation as if it were a time series is the
classic error here; every Foundation vintage is pulled so that changes between
vintages can be separated from real change.

Branded Foods is deliberately skipped -- ~1GB of manufacturer label data, not
laboratory measurement, and irrelevant to a micronutrient-density argument.
"""
import sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session

B = "https://fdc.nal.usda.gov/fdc-datasets/"
AGENCY, DATASET = "usda-ars-fdc", "fooddata-central"

core = [
    (B + "FoodData_Central_sr_legacy_food_csv_2018-04.zip", None),
    (B + "FoodData_Central_csv_2026-04-30.zip", None),      # full current release
]
foundation = [
    B + f"FoodData_Central_foundation_food_csv_{v}.zip" for v in
    ["2019-12-17","2020-04-29","2020-10-30","2021-04-28","2021-10-28",
     "2022-04-28","2022-10-28","2023-04-20","2023-10-26","2024-04-18",
     "2024-10-31","2025-04-24","2025-12-18","2026-04-30"]
]
survey = [
    B + f"FoodData_Central_survey_food_csv_{v}.zip" for v in
    ["2020-03-31","2020-10-30","2022-10-28","2024-10-31"]
]
support = [B + "FoodData_Central_Supporting_Data_csv_2022-10-28.zip"]
codebook = [("https://fdc.nal.usda.gov/docs/Download_Field_Descriptions_Oct2020.pdf", None)]

s = session()
print("== FDC core (SR Legacy + full current) ==")
fetch_all(core, AGENCY, DATASET, subdir="core", sess=s, timeout=1800,
          notes="SR Legacy frozen 2018-04; full release 2026-04-30")
print("== FDC Foundation Foods, all vintages ==")
fetch_all(foundation, AGENCY, DATASET, subdir="foundation", sess=s, timeout=900,
          notes="vintage series -- lets release-to-release drift be separated from real change")
print("== FDC Survey (FNDDS) ==")
fetch_all(survey, AGENCY, DATASET, subdir="survey-fndds", sess=s, timeout=900,
          notes="FNDDS survey foods, used with NHANES WWEIA dietary recalls")
print("== FDC supporting + field descriptions ==")
fetch_all(support, AGENCY, DATASET, subdir="supporting", sess=s, timeout=900)
fetch_all(codebook, AGENCY, DATASET, subdir="codebooks", sess=s,
          notes="field descriptions -- the FDC codebook")
