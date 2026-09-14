# Step 04 — Soil (the "strip-mining" claim)

This is the pillar where the data is weakest and the framing most vulnerable.

- [x] **RaCA** — methodology, sampling and summary, field/lab protocols,
      16 regional summaries, land-use/region maps, data workbook
- [x] **NRI** — 2017 Summary Report, Alaska NRI 2007, Historical Changes in
      Soil Erosion, plus NRI glossary / history / estimation methodology
- [x] **Annual Soils Refresh notes 2021–2025** — the record of what changes in
      SSURGO each October and *why*
- [ ] **2022 NRI Summary Report (Sept 2025)** — NOT YET ACQUIRED, see gap below
- [ ] RaCA pedon-level measured data (SOC, total N, bulk density, VNIR)
- [ ] NCSS Kellogg Lab Data Mart — repeat/near-repeat pedon extraction
- [ ] SSURGO / gSSURGO via Soil Data Access (SQL over HTTP)
- [ ] CEAP cropland modelling output
- [ ] ARS LTAR long-term paired-treatment field data

## Access constraint

`www.nrcs.usda.gov` resets the connection from this network on every
`/resources/…` and `/sites/default/files/…` path (fast RST, ~0.2–0.9 s; the site
root returns 200). Everything above came from the Internet Archive instead.

## Gap: the 2022 NRI Summary Report

The report the analysis actually needs — tables 15–18, erosion by state and year
and erosion relative to T — is not retrievable here. It is not in the Wayback
index under any `nrcs.usda.gov/sites/default/files/2025-*` path, and NRCS blocks
direct access. **This needs a manual download from an ordinary browser**, then
drop into `data/raw/usda-nrcs/nri/<date>/reports/` and run
`scripts/verify_mirror.py`. The 2017 report is in custody as an interim.

## Three ways to get this pillar wrong

1. **SSURGO is not a time series.** Its properties are largely mapped and
   modelled representative values, not repeat field measurements, and the annual
   refresh changes values for reasons unrelated to soil change (10–20% of survey
   areas see substantive change each year — the Refresh notes document exactly
   this). Using SSURGO deltas as evidence of degradation is the single most
   likely technical error in this project and the easiest to dismantle.
2. **NRI back-updates its history.** Each release restates prior years so that
   observed change is real change, not collection-method drift. Never compare
   the 2022 release against figures published in the 2017 release.
3. **RaCA is a single timepoint.** It gives the 2010–11 state of SOC by land
   use. It cannot by itself show decline. Use the current NRCS distribution, not
   the SoilWeb/`soilDB::fetchRaCA()` path — that is deprecated and returns
   VNIR-*estimated* SOC rather than Kellogg lab-*measured* SOC.

Where genuine multi-decade measured-SOC comparison is possible at all, it is via
NCSS repeat-sampled pedons (hard, defensible) and LTAR paired treatments
(small n, high internal validity). Pair LTAR with NRI for national scope.
