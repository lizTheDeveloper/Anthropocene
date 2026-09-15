# Shared brief for lens analysts

You are producing one rigorous, original analysis of a real federal data mirror,
framed by one named scholar's published analytical framework.

## Ground rules on attribution — read first

You are **not** that person and must not write as them.

- Never write in their voice, never sign anything as them, never invent a quote,
  position, or opinion and attribute it to them.
- Do cite their actual published work, accurately, with real titles. If you are
  not certain a work exists or says what you need, say so rather than assert it.
- Frame every claim as *your* analysis applying *their published framework*.
  "Analysed through the diversified-farming-systems framework developed by
  Kremen and colleagues" — never "Kremen finds that this data shows…".
- Their framework tells you **which question to ask of this data and how to
  judge the answer**. The numbers must come from the mirror, not from them.

If your lens turns out not to be well supported by the available data, say that
plainly. A well-argued "this framework asks a question this data cannot answer,
and here is what it would take" is a genuinely useful result. Do not manufacture
a weak chart to have something to show.

## The data

Repository root: `/Users/annhoward/src/Anthropocene`. Everything is mirrored
locally with SHA-256 provenance in `data/provenance.csv`.

Ready-to-use derived tables in `data/derived/`:

| file | contents |
|---|---|
| `pnsp_county_panel_corrected.parquet` | county x year x compound pesticide use, kg (low/high). **Corrected**: California dropped from every year, aggregate rows removed. Use this one. |
| `pnsp_county_panel.parquet` | the raw uncorrected panel. Only for demonstrating artifacts. |
| `pnsp_national_corrected.csv` | national totals by year, corrected basis |
| `pnsp_compound_year_matrix_noCA.csv` | compound x year matrix |
| `use_vs_monitoring.csv` | per-compound use vs Water Quality Portal site counts |
| `soil_toxicity_vs_use.csv`, `soil_evidence_gap.csv` | ECOTOX soil-fauna endpoint coverage vs applied mass |
| `40cfr180_tolerances.csv` | 15,416 pesticide-commodity tolerances, 2,474 commodities |
| `compound_crosswalk_full.csv` | PNSP name / CA PUR chem_code / 40 CFR 180 section / EPA DTXSID |

Raw sources in `data/raw/` (open with pandas; several are large, chunk them):

- `usda-nass/quickstats-bulk/*/qs.census2022.txt.gz` (and 2002-2017) — Census of
  Agriculture: **cover crop and tillage acreage, crop diversity, farm size,
  land tenure, producer demographics incl. race and ethnicity**, by county.
  Tab-delimited, latin-1, gzipped, large. `VALUE` is a STRING with thousands
  separators and suppression codes — not a number.
- `usda-nass/quickstats-bulk/*/qs.environmental_*.txt.gz` — Agricultural Chemical
  Use: percent acres treated, application rate, pest-management practices.
- `ca-dpr/pur/` — California full-census application records 1974-2023,
  section-level (1 sq mi). The only application-level resolution in the country.
- `epa-usgs-wqp/` — pesticide occurrence in water, 18 compounds. **Read
  `docs/WQP_DATA_QUALITY.md` before touching this.** Most rows are non-detects
  with no numeric value; negative values are below-detection estimates, not
  concentrations.
- `epa/ecotox/` — ECOTOX full release. Join through CAS, not names.
  `ecotox_group` "Worms" includes marine polychaetes.
- `usda-ams/pdp/`, `fda/pesticide-residue-monitoring/` — food residues.
  PDP `*Results.txt` has **no header row**; columns are in the data dictionary
  PDF inside the same zip.
- `usda-nrcs/nri/reports/2022_NRI_Summary_Report.pdf` — erosion by state and
  year, and erosion relative to T. Tables are in the PDF, not offered as CSV.
- `usda-nrcs/raca/` — Rapid Carbon Assessment methodology and regional summaries.
- `usda-ars-fdc/`, `usda-historical/` — food composition, current and historical.

## Established findings you may build on (verified in-repo)

1. **National applied mass is roughly flat.** +14.7% over 26 years, +2.3% on a
   fixed compound roster. What changed is composition: glyphosate 6.9 -> 119.2
   M kg (1.8% -> 26.6% of mass, 17x) while everything else summed *fell*.
2. **The published 2016->2018 "decline" is an artifact** of California's absence
   and double-counted aggregate rows. Corrected: +0.8%.
3. **Water monitoring tracks the market of 1992.** Site count correlates with
   1992 use (rho=+0.545, p=0.019), not 2018 use (rho=-0.141, p=0.58).
   Dedicated-method compounds get a median 2,353 sites vs 28,365 for
   standard-panel compounds (p=0.0025).
4. **79% of applied mass has no comparable acute soil-fauna toxicity record** in
   ECOTOX. Glyphosate has 106 soil-fauna records and zero comparable endpoints.

## The four ways this analysis dies

1. **The dilution effect.** Declining crop mineral concentration is
   conventionally attributed to cultivar selection for yield, not soil
   depletion (Davis, Epp & Riordan 2004). Rule cultivar change out first.
2. **Analytical method drift.** 1950 and 2018 values used different methods with
   different recoveries. A decline can be a method artifact.
3. **SSURGO is not a time series; NRI back-updates its own history.** Never diff
   SSURGO vintages. Never compare the 2022 NRI against figures published in the
   2017 NRI — take both current and historical values from one release.
4. **Joins across mismatched sampling frames.** PNSP is modelled county-level
   use; PDP is a rotating commodity sample; NRI is a land-point panel; FDC is a
   reference table. Joining them yields descriptive association, not causation.
   Label it honestly.

5. **PNSP breaks at 2015: seed treatments were dropped.** The mirror's own
   metadata (`Metadata4PreliminaryPestUse*.xml`, in every preliminary zip) states:
   *"Beginning 2015, the provider of the surveyed pesticide data used to derive
   the county-level use estimates discontinued making estimates for seed
   treatment application of pesticides... Pesticide use estimates prior to 2015
   include estimates with seed treatment application."* Neonicotinoids are
   overwhelmingly seed treatments on corn and soy, so this is not a small
   correction: neonicotinoid EPest-high mass falls 85.3% in one step 2014->2015
   (clothianidin -99.4%, thiamethoxam -80.7%, imidacloprid -66.1%), and total
   insecticide mass drops ~20% across the same step. **Any insecticide trend
   crossing 2014/2015 is measuring a survey decision, not the field.** Confine
   insecticide comparisons to <=2014, or state the break explicitly. Found
   independently by two analysts; verified verbatim in all five metadata files.


## What to produce

Write to `analysis/<your-slug>/`:

1. `FINDING.md` —
   - **The question**, and why this framework makes it the right one (cite the
     actual literature, 2-5 real references).
   - **What you did**: data used, filters, exactly how numbers were computed.
   - **The result**, with real numbers.
   - **Limitations**, honestly. What this cannot show. Which of the four
     landmines applies.
2. `chart.json` — a spec for ONE visualization: `{title, subtitle, chart_type,
   x, y, series, annotations[], source_note, data_file}`. One clear claim per
   chart. The parent assembles the final visual system, so specify *what* to
   show, not CSS.
3. A CSV in `data/derived/lens_<slug>_*.csv` holding exactly the rows your chart
   needs, already aggregated.
4. `compute.py` — the script that produced the CSV, runnable from repo root.

**Verify your numbers before writing them down.** Recompute a headline figure a
second way, or state that you could not. Report what the data says even when it
is inconvenient for the framework you are applying.

Do not commit to git; the parent handles that.
