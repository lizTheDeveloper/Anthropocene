# Anthropocene — Federal Data Acquisition & EDA Plan

Soil health, pesticide use and residues, micronutrient decline, and toxicology.
Acquisition is ordered by value-per-hour, not by the order of the source list.

**Working branch:** `claude/laughing-franklin-tpm5d9`
**Retrieval convention:** every artifact is mirrored to `data/raw/<agency>/<dataset>/<retrieval-date>/`
with a SHA-256 in `data/manifests/<dataset>.sha256` and a row in `data/provenance.csv`.

## Step index

| Step | Pillar | File | Status |
|------|--------|------|--------|
| 01 | Acquisition infrastructure & provenance | [step-01](plans/step-01-infrastructure.md) | done |
| 02 | Pesticide use (PNSP, CA PUR, NASS) | [step-02](plans/step-02-pesticide-use.md) | done |
| 03 | Residues in food (PDP, FDA, TDS) | [step-03](plans/step-03-residues.md) | in progress |
| 04 | Soil (NRI, RaCA, NCSS, SSURGO, LTAR) | [step-04](plans/step-04-soil.md) | in progress |
| 05 | Nutrition (FDC, Handbook No. 8, NHANES) | [step-05](plans/step-05-nutrition.md) | in progress |
| 06 | Toxicology (ECOTOX, CompTox, dockets, AHS) | [step-06](plans/step-06-toxicology.md) | in progress |
| 07 | Farming practice adoption | [step-07](plans/step-07-practice-adoption.md) | partial |
| 08 | Water & environmental fate | [step-08](plans/step-08-water.md) | not started |
| 09 | Regulatory corpus | [step-09](plans/step-09-regulatory.md) | partial |
| 10 | Archives & mirrors | [step-10](plans/step-10-archives.md) | not started |
| 11 | Exploratory data analysis | [step-11](plans/step-11-eda.md) | not started |

## The four ways this analysis dies

Design around these now; they are cheaper to avoid than to repair.

1. **The dilution effect.** Declining mineral concentration in crops is
   conventionally attributed to cultivar selection for yield and size, not soil
   depletion (Davis, Epp & Riordan 2004; and read the critiques). Any
   soil-depletion claim must first rule out cultivar change — same-cultivar
   comparison or archived-sample reanalysis.
2. **Analytical method drift.** 1950 and 2018 nutrient values were produced by
   different methods with different recoveries. Restrict comparisons to
   nutrients where the method is comparable or the bias is characterizable.
3. **SSURGO is not a time series, and NRI back-updates its history.** Do not
   diff SSURGO vintages. Do not compare the 2022 NRI against the published 2017
   NRI — use the 2022 release for both current and historical values.
4. **Correlation across mismatched sampling frames.** PNSP is modeled
   county-level use; PDP is a rotating commodity sample; NRI is a land-point
   panel; FDC is a reference table. Joining them yields descriptive association,
   not causation, unless an explicit causal design says otherwise. Label it
   honestly or the opposing comment writes itself.

## Standing constraint

FDA's edge returns HTTP 401 to this network on every data path. Those artifacts
are retrieved from the Internet Archive with the `id_` modifier, which replays
original unmodified bytes. Every such row in `provenance.csv` is tagged
`VIA_WAYBACK` with its capture timestamp — the checksum attests to a
third-party-archived copy at a known time, not to a live agency fetch.
