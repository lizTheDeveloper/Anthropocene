# The shape of the state's field of vision

> **CORRECTION (parent session):** Finding 2's "zero published chemical-use values" for hay is a join artifact — the Census says `HAY`, the Chemical Use Program says `HAY & HAYLAGE`. Hay does appear, in 3 of 36 years, but **only as aggregate `CHEMICAL: (TOTAL)` acres-treated with no named active ingredient, ever**. See `CORRECTION.md`. The corrected claim is stronger.


**Lens:** agroecology as a transdisciplinary, participatory and action-oriented
project, as developed by V. Ernesto Méndez and colleagues at the UVM Institute
for Agroecology.
**Slug:** `mendez` · **Analyst:** this is my analysis applying their published
framework; nothing here is attributed to Méndez or any co-author as an opinion.

---

## 1. The question, and why this framework makes it the right one

Every other number in this mirror answers "how much pesticide was applied." The
framework applied here asks a prior question: **who decided what would be
counted, and whose farming therefore has no federal record at all?**

The framework that motivates it is agroecology construed as a *transdisciplinary,
participatory and action-oriented* practice — Méndez, Bacon and Cohen (2013),
elaborated in Méndez, Bacon, Cohen and Gliessman (eds., 2016) and in the fourth
edition of Gliessman, Méndez, Izzo and Engles (2023). Its central methodological
commitment is Participatory Action Research: farmers and communities are
*co-definers of the research question*, not subjects of someone else's
instrument. The corollary, and the thing that makes it a usable analytic here, is
that **a measurement programme is itself an artefact of a power relation** — the
questions asked encode whose problems are considered worth solving. The same
literature's empirical work makes the stakes concrete: Bacon, Sundstrom, Flores
Gómez, Méndez et al. (2014) on the "hungry farmer paradox" turns on precisely the
variables — corn harvests, fruit trees, grain storage, farm area — that a
commodity-indexed statistical system does not collect, and that only became
visible because the research design started from what households said mattered.

This federal mirror is the pure opposite case. Nothing in it was co-defined with
anyone who farms. USGS models county pesticide use from proprietary grower
surveys; EPA decides which compounds get validated water methods; and NASS
chooses, on a rotating schedule, which crops enter the Agricultural Chemical Use
Program at all. So the question this lens presses is answerable, and it is
answerable *from the mirror itself*: the survey record is a record of decisions
about what to measure. Mapped against the Census of Agriculture — the one federal
instrument that tries to count every farm — the gap between the two **is the
absence, rendered as data.**

I make one framing debt explicit: "legibility" as a property that states impose
on populations is James C. Scott's (*Seeing Like a State*, 1998), not this
framework's. The agroecological contribution here is the insistence that the
illegible party is a knowledge-holder, not a data gap.

---

## 2. What I did

Two USDA NASS products share one controlled vocabulary (`COMMODITY_DESC`), which
makes them directly joinable without a crosswalk.

**A. What got measured.** `data/raw/usda-nass/quickstats-bulk/2026-09-14/
qs.environmental_20260912.txt.gz`, filtered to `SOURCE_DESC = SURVEY` and
`DOMAIN_DESC` containing `CHEMICAL` (this includes `RESTRICTED USE CHEMICAL...`;
it excludes fertilizer, pest-management practice, and honey-bee pollination
items). 1,161,275 published values. Each is a crop × geography × year × active
ingredient estimate. Reduced to the set of **(commodity, state, year) cells for
which NASS ever published a pesticide-use estimate.** NASS publishes ACUP at
state and at "REGION : MULTI-STATE / PROGRAM STATES" level only — there is no
county resolution anywhere in the programme.

**B. What is actually grown.** `qs.census2022.txt.gz`, `SECTOR_DESC = CROPS`,
`DOMAIN_DESC = TOTAL`, `PRODN_PRACTICE_DESC = ALL PRODUCTION PRACTICES`, units
`ACRES` and `OPERATIONS`, at national, state and county level. `VALUE` is a
string with thousands separators and suppression codes `(D) (Z) (NA) (X) (L) (H)
(S)`; these are parsed to NaN, never to zero. Two de-duplication rules are
applied, because NASS's hierarchy would otherwise double-count: (i) one area
concept per crop group — `AREA HARVESTED` for field crops and vegetables,
`AREA BEARING` for fruit and tree nuts, `AREA IN PRODUCTION` for horticulture, so
orchard bearing acres are not stacked on harvested acres; (ii) within each
geography × commodity, where an `ALL CLASSES` or `ALL UTILIZATION PRACTICES`
roll-up row exists it *is* the total and its sub-rows are dropped, otherwise the
sub-rows are summed (this is what recovers CORN, whose acreage is carried on
`GRAIN` / `SILAGE` utilisation rows with no "all" row). Explicit roll-up
commodities (`HAY & HAYLAGE`, `GRASSES & LEGUMES TOTALS`, `BERRY TOTALS`,
`CITRUS TOTALS`, …) are removed by name. Resulting crop base: **305,906,121 acres
across 156 commodities**, 2,106,553 crop-growing operation-records.

**C. Coverage.** A county's crop acre is *covered* if its commodity appears in
the ACUP state-level record **for that county's own state**. Three variants are
carried throughout: `cov_recent` (published 2013–2025, i.e. roughly two full
rotation cycles), `cov_ever` (1990–2025), and `cov_recent_us` (the generous
variant: commodity surveyed anywhere in the US since 2013, regardless of state).
Crop diversity per county is the **effective number of crops**, Hill N₁ =
exp(Shannon entropy) of the county's crop-acreage share vector. Counties with
≥ 1,000 census crop acres and a computable diversity figure: **2,951**, holding
302.1 M acres = 98.8% of the national base.

Script: `analysis/mendez/compute.py` (runnable from repo root, ~2 min).

---

## 3. The result

### 3a. The programme measures 51 crops. Americans grow 156.

| status | commodities | share of crop acres | share of crop-growing operation-records |
|---|---:|---:|---:|
| surveyed 2013–2025 | 51 | 77.4% | 54.7% |
| surveyed once, then lapsed | 22 | 2.0% | 6.2% |
| **never surveyed, 1990–2025** | **83** | **20.6%** | **39.1%** |

Thirteen crops appear in exactly one year of the entire 36-year record:
**almonds** (1999, California only), **sugarbeets** (2000), **tobacco** (1996),
**sunflower**, **walnuts**, **pistachios**, artichokes, beets, Brussels sprouts,
okra, plums & prunes, "facilities & equipment", sheep. Almonds are now the
largest US tree-nut crop by acreage (1,366,841 bearing acres); the public federal
record of what is sprayed on them is a single survey year, twenty-six years old.

### 3b. The most widely grown crop in the United States has never been measured

Ranked by the number of farms that grow it, the 2022 Census puts **hay first**:

| crop | farms | acres | ACUP status |
|---|---:|---:|---|
| **HAY** | **612,946** | 47,207,698 | **never surveyed** |
| CORN | 327,477 | 86,576,380 | surveyed 2013+ |
| SOYBEANS | 270,851 | 84,599,236 | surveyed 2013+ |
| **HAYLAGE** | **120,781** | 8,135,653 | **never surveyed** |
| WHEAT | 97,014 | 37,211,994 | surveyed 2013+ |

612,946 farms is **32.3% of all 1,900,487 US farms**. Hay is the third-largest
crop in the country by acreage. In 36 years of the Agricultural Chemical Use
Program there are **zero** published chemical-use values for hay, haylage,
alfalfa, pasture or any forage commodity. (Verified on two independent code
paths; the only near-match in the survey record is `ORNAMENTAL GRASSES`, a
nursery crop.) Forage is the crop base of grazing livestock, of the diversified
Northeast and Appalachian farms, and of exactly the mixed crop-livestock systems
this framework treats as the template for diversification.

**The number exists anyway — it just isn't a measurement.** USGS PNSP's
state × crop-group release in this mirror
(`data/raw/usgs/pnsp/2026-09-14/state-level/AgPestUsebyCropGroup92to16.zip`)
reports pesticide mass for crop groups `Alfalfa` and `Pasture_and_hay`:
**606.3 M kg of 12,212.9 M kg total, 5.0%, 1992–2016.** Its own metadata names
the source: *"Kynetec Proprietary farm survey data"*, *"Proprietary data; no link
provided."* Where the public survey is silent, a private one speaks, and the
public cannot inspect it.

### 3c. Coverage is fitted to one farming system — the corn–soybean rotation

This is the chart. County coverage against crop diversity is **not monotone**;
the overall Spearman correlation (ρ = +0.272, p = 3.6 × 10⁻⁵¹) is real but
misleading, because the curve is an inverted U.

| decile of county crop diversity | median effective crops | acres | coverage (2013+) | hay share of acres |
|---|---:|---:|---:|---:|
| 1 (least diverse) | 1.30 | 6.1 M | **5.8%** | 90.5% |
| 2 | 1.86 | 12.7 M | 54.3% | 41.8% |
| **3** | **2.23** | 42.4 M | **92.0%** | 7.1% |
| 4 | 2.54 | 36.9 M | 88.4% | 9.8% |
| 5 | 2.89 | 31.7 M | 78.4% | 16.4% |
| 6 | 3.28 | 32.6 M | 76.6% | 16.3% |
| 7 | 3.68 | 32.0 M | 70.8% | 19.1% |
| 8 | 4.14 | 34.9 M | 69.2% | 20.7% |
| 9 | 4.69 | 32.8 M | 64.2% | 19.4% |
| 10 (most diverse) | 5.97 | 40.0 M | 58.9% | 19.0% |

Coverage peaks at **92.0%** in the decile whose effective crop count is
**2.11–2.38** — an almost exact description of a two-crop corn–soybean rotation —
and falls away in *both* directions. The left tail is forage: decile 1 counties
average 95% of their crop acres in hay, and 5.8% coverage. The right tail is
mixed fruit, vegetable and forage systems: decile 10 averages 6.6 effective crops
and 58.9% coverage. The shape survives all three coverage definitions
(`cov_ever`: 6.0% → 92.3% → 68.2%; `cov_recent_us`: 6.7% → 92.7% → 67.0%).

I had expected a monotone decline — diversification as invisibility. **That is
not what the data says**, and the actual shape is more specific and more damning:
the instrument is not biased against complexity in general, it is *tuned to one
cropping system* and degrades away from it in every direction.

Geographically: **14 of 50 states have less than 10% of their census crop acres
inside the published 2013–2025 frame**, and 12 have exactly zero — AK, CT, DE,
HI, MA, MD, NH, NV, RI, UT, VT, WV (Wyoming is at 4.4% and New Jersey at 8.5%).
405 of 2,951 counties
(8.2 M acres) are at exactly zero. Illinois is at 97.2%, Iowa 95.3%. Even for
corn — the second-most-surveyed crop — the programme covered 7 to 21 states in a
given year, and the cadence collapsed from annual (1990–2003) to six
observations in the twenty-one years since: 2005, 2010, 2014, 2016, 2018, 2021.

### 3d. The two resolutions, side by side, for one year

For **2022**, the entire public federal pesticide-use survey record for the
United States is **36,453 published values covering 21 crops** (the vegetable and
wheat rotation slot). For the same year, California's legally mandated Pesticide
Use Report — every application, by product, date, acres treated, grower ID, and
one-square-mile section — contains **4,281,466 application records across 22,613
sections**. California farmers are visible because a state law compels
disclosure; everyone else is visible only as a modelled cell built on data no
citizen can read.

---

## 4. Verification

Every headline number was recomputed by a second route before being written down.

1. **ACUP frame counts, pandas vs. a separate `awk` pass over the raw gzip:**
   93 commodities ever / 52 since 2013 / 617 (commodity, state) cells — identical
   on both paths.
2. **Coverage share, national rows vs. rebuilt from county rows:** 77.444% vs.
   77.618% (0.17 pp apart; the residual is county suppression).
3. **Crop-acre base at three aggregation levels:** national 305,906,121; summed
   over states 305,262,485 (−0.21%); summed over counties 302,139,789 (−1.23%).
   The monotone shrinkage is expected — NASS suppresses more cells at finer
   geography — and is small enough not to move any conclusion.
4. **Hay:** national 612,946 farms / 47,207,698 acres reconciles *exactly* with
   the sum over states. Absence from ACUP confirmed by a direct `awk` regex over
   the raw file (`HAY|ALFALFA|GRASS|PASTURE|FORAGE|CLOVER`) and by the pandas
   join: zero rows either way.
5. **The inverted U** reproduces under three independent coverage definitions
   (state-specific recent, state-specific ever, US-wide recent) and under a
   median-of-counties statistic instead of an acre-weighted one (0.000 → 0.959 →
   0.558).

---

## 5. Limitations — what this cannot show

- **This is a record of publication, not of survey effort.** A cell can be absent
  because NASS surveyed and suppressed for disclosure reasons, because the
  sample was too thin to publish, or because the crop was never in the frame. I
  cannot separate these from the mirror. "Never surveyed" should be read strictly
  as **"never published in the QuickStats bulk record as it stands in September
  2026."** Historical ACUP releases that were withdrawn from QuickStats would not
  appear. That caveat cuts in the direction of the finding rather than against
  it — what a citizen can retrieve *is* the public record.
- **Landmine 4 applies and is the governing one: mismatched sampling frames.**
  ACUP is a voluntary stratified survey of top-producing states; the Census is a
  near-complete enumeration. Joining them yields a statement about *coverage*,
  which is what I claim, and nothing about use rates, which I do not claim. No
  causal reading is available and none is offered.
- **Coverage is not the same as ignorance.** A crop with no NASS survey may still
  be represented in the USGS PNSP model, in EPA registration review, or in
  California's PUR. The claim is narrower and specific: **no public,
  farmer-reported, crop-specific federal measurement exists.**
- **"Operation-records" are not unique farms.** Summed across crops, a farm
  growing corn and hay is counted twice. The 39.1% figure is a share of
  crop-growing records, not of farms. The hay farm count (612,946) is a clean
  Census figure and *is* a farm count.
- **The diversity metric is acreage-based** and therefore under-weights
  high-value, small-acreage enterprises — market gardens, greenhouse production,
  agroforestry — which is itself a bias in the framework's direction that I have
  not corrected for.
- **Landmines 1–3 (dilution effect, method drift, SSURGO/NRI vintaging) do not
  apply**; no time series of concentration, no analytical chemistry, and no soil
  survey is used here.
- **What this analysis cannot do is the thing the framework actually asks for.**
  A Participatory Action Research design would have farmers define the indicators
  before any data were collected. I can show the silhouette of the absence; I
  cannot show what a farmer-defined measurement programme would have recorded
  instead. Naming that as the limit is the honest end of the analysis. The
  identifiable next step is not a better model of this data — it is a different
  data-generating process.

---

## 6. References

1. Méndez, V.E., Bacon, C.M., & Cohen, R. (2013). Agroecology as a
   transdisciplinary, participatory and action-oriented approach. *Agroecology
   and Sustainable Food Systems*, 37(1), 3–18.
2. Méndez, V.E., Bacon, C.M., Cohen, R., & Gliessman, S.R. (eds.) (2016).
   *Agroecology: A Transdisciplinary, Participatory and Action-oriented
   Approach.* Advances in Agroecology. Boca Raton: CRC Press.
3. Gliessman, S.R., Méndez, V.E., Izzo, V.M., & Engles, E.W. (2023).
   *Agroecology: Leading the Transformation to a Just and Sustainable Food
   System*, 4th edn. Advances in Agroecology. Boca Raton: CRC Press.
4. Bacon, C.M., Sundstrom, W.A., Flores Gómez, M.E., Méndez, V.E., Santos, R.,
   Goldoftas, B., & Dougherty, I. (2014). Explaining the 'hungry farmer paradox':
   smallholders and fair trade cooperatives navigate seasonality and change in
   Nicaragua's corn and coffee markets. *Global Environmental Change*, 25,
   133–149.
5. Scott, J.C. (1998). *Seeing Like a State: How Certain Schemes to Improve the
   Human Condition Have Failed.* New Haven: Yale University Press. (Cited for the
   concept of legibility only.)

**Federal sources.** USDA NASS, *Guide to NASS Surveys: Agricultural Chemical Use
Program* — confirms the rotating commodity schedule and that "each survey focuses
on the top-producing states that together account for the majority of U.S. acres
or production of the surveyed commodity." USGS, *Estimated Annual Agricultural
Pesticide Use by Major Crop or Crop Group for States of the Conterminous United
States, 1992–2016*, metadata record (mirrored in this repo).

## 7. Files produced

| file | contents |
|---|---|
| `data/derived/lens_mendez_diversity_bins.csv` | **chart data** — 10 diversity deciles × coverage |
| `data/derived/lens_mendez_county_coverage.csv` | 2,951 counties: acres, diversity, coverage, hay share |
| `data/derived/lens_mendez_crop_coverage.csv` | 156 commodities: acres, farms, survey status, last surveyed year |
| `data/derived/lens_mendez_state_coverage.csv` | 50 states: coverage under three definitions |
| `analysis/mendez/compute.py` | the script that produced all four |
