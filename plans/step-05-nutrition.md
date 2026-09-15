# Step 05 — Nutrition and micronutrient decline

This pillar has a labour problem, not an availability problem.

- [x] **FoodData Central** — SR Legacy (frozen 2018-04), full current release
      (2026-04-30), all 14 Foundation Foods vintages, 4 FNDDS survey vintages,
      supporting data, field descriptions
- [x] **Atwater & Woods, USDA Bulletin No. 28 (1896/1899)** — the origin point
- [x] **Agriculture Handbook No. 8** scan via govinfo + 6 sectional/related scans
- [x] **NHANES** — laboratory biomarkers and dietary interview files
- [ ] OCR pipeline for Handbook No. 8 tables (the long pole — start early)
- [ ] Per-value page citations for every extracted historical figure
- [ ] Locate remaining AH-8-1 … AH-8-21 sectionals (NAL Digital Collections, HathiTrust)
- [ ] CDC National Report on Human Exposure to Environmental Chemicals tables

## Why SR Legacy and Foundation are not a time series

SR Legacy is frozen at 2018 and carries values from mid-20th-century analyses.
Foundation Foods is the forward-going product with a different sampling design
and per-sample provenance. They are two products, not two points on a line.
Every Foundation vintage was pulled so release-to-release drift can be separated
from real change.

## The two landmines

1. **The dilution effect** is the standard counter-explanation and it is a good
   one. Observed declines in mineral concentration are generally attributed to
   cultivar selection for yield and size — more carbohydrate and water per unit
   mineral — not to soil depletion. Canonical citation: Davis, Epp & Riordan,
   *J Am Coll Nutr* 23(6):669–682 (2004); the critiques matter as much as the
   paper. Rule cultivar change out first: same-cultivar comparison, or archived
   sample reanalysis (Rothamsted Broadbalk is the classic instrument).
2. **Analytical method drift.** 1950 and 2018 values came from different methods
   with different recoveries; a decline can be a method artifact. Handbook No. 8
   documents its methods — read them, and restrict comparisons to nutrients
   where the method is comparable or the bias is characterisable.

## NHANES specifics

Laboratory biomarkers (ferritin, serum/RBC folate, folate forms, B12, iron
status, copper/selenium/zinc, vitamin D, carotenoids) and urinary pesticide
metabolites are measured in the **same individuals**, which links the exposure
pillar to the health pillar without a cross-frame join.

Caution: the glyphosate panels (`SSGLYP_H/I/J`, 2013–2018) are **surplus-specimen
subsamples**, not the full NHANES sample. They carry their own weights and are
not nationally representative without care.
