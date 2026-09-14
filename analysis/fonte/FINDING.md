# The bundle the federal record cannot see

**Lens:** whole-bundle agroecosystem assessment, as developed in the published work of
Steven Fonte (Colorado State University) and colleagues.
**Slug:** `fonte`
**Analyst artefacts:** `compute.py`, `chart.json`, `data/derived/lens_fonte_bundle_coverage.csv`, `_summary.json`

> Attribution note, per the shared brief: this is my analysis applying a published
> framework. Nothing here is written in Prof. Fonte's voice, and no opinion,
> quotation or conclusion is attributed to him. The cited works are real and are
> used only to establish *which question to ask of this data and how to judge the
> answer*. Every number comes from the mirror.

---

## 1. The question, and why this framework makes it the right one

The research programme of the Fonte lab at Colorado State evaluates farming systems
by measuring, as a bundle, "yields and profitability together with an array of
ecosystem services such as erosion control, nutrient cycling and provision, carbon
sequestration, pest regulation, water capture and storage, among others"
(Agroecosystem Ecology Lab research statement, Colorado State University,
<https://labs.agsci.colostate.edu/fonte/research/>). The methodological commitment
that follows is the refusal to declare a system improved because one indicator moved.
Two of the lab's empirical papers show the commitment in operation:

- Lavelle, P., Rodríguez, N., Arguello, O., Bernal, J., Botero, C., Chaparro, P.,
  Gómez, Y., Gutiérrez, A., Hurtado, M.d.P., Loaiza, S., Pullido, S.X., Rodríguez, E.,
  Sanabria, C., Velásquez, E. & **Fonte, S.J.** (2014). *Soil ecosystem services and
  land use in the rapidly changing Orinoco River Basin of Colombia.* Agriculture,
  Ecosystems & Environment 185: 106–117. Four production systems are scored
  simultaneously on nutrient provision, hydrological function, climate regulation,
  macroaggregation and macroinvertebrate communities — and the systems rank
  *differently* on each. Annual crops score highest on nutrient provision; perennials
  on hydrology and climate regulation; pastures on macroinvertebrate activity and
  aggregation. No system wins the bundle.
- Rousseau, L., **Fonte, S.J.**, Téllez, O., van der Hoek, R. & Lavelle, P. (2013).
  *Soil macrofauna as indicators of soil quality and land use impacts in smallholder
  agroecosystems of western Nicaragua.* Ecological Indicators 27: 71–82. Soil
  macrofauna are used as functional indicators of soil quality under contrasting
  management.
- **Fonte, S.J.**, Hsieh, M. & Mueller, N.D. (2023). *Earthworms contribute
  significantly to global food production.* Nature Communications 14: 5713. Earthworm
  abundance is tied to ~6.5% of global grain production — i.e. a soil-biota outcome
  that is also a yield outcome.
- **Fonte, S.J.**, Vanek, S.J., Oyarzun, P., Parsa, S., Quintero, D.C., Rao, I.M. &
  Lavelle, P. (2012). *Pathways to agroecological intensification of soil fertility
  management by smallholder farmers in the Andean highlands.* Advances in Agronomy
  116: 125–184. The participatory strand: farmers help set the questions, co-design
  the trials in their own fields, and interpret the results.

The Orinoco result is the load-bearing one for this analysis. If different practices
win on different members of the bundle, then **the evidence base determines the
verdict**: whichever outcome is measured most densely will dominate any evaluation
built on it, and outcomes that are not measured cannot lose.

This matters for a petition that proposes *mandating* practices. A mandate is a claim
about the whole bundle enforced on farms. The question this framework presses on the
federal data system is therefore not "does regenerative practice work?" but:

> **For each outcome in the bundle, how deeply does the federal record actually
> measure it — and how much of the bundle can be observed in the same place at the
> same time?**

I quantified both.

---

## 2. What I did

**Window.** 1982–2022 (41 years) — the span of the longest bundle series in the
federal record (NRI erosion). 7 outcomes × 41 years = **287 outcome-years**.

**For each outcome I identified the best-available federal series in the mirror** and
counted, per year, the number of distinct places with a published, non-suppressed
observation. I separated two evidence classes, and the separation is the analysis:

- **direct** — the series measures the outcome itself, in a place, at a time;
- **proxy** — the series measures an input, a pressure, or a laboratory hazard
  *instead of* the outcome (fertiliser applied ≠ nutrient cycling; pesticide mass
  applied ≠ pest regulation; irrigated acres ≠ water capture; an earthworm LC50 ≠ a
  macrofauna community).

| outcome | best federal series | support | basis |
|---|---|---|---|
| Yield | NASS QuickStats, county crop yield (survey) | county | survey enumeration |
| Profitability | NASS Census of Ag, net cash farm income | county | census enumeration |
| Erosion control | NRCS NRI 2022 Summary Report, Tables 15–16 | state | **model output** (RUSLE2 / WEQ on panel points) |
| Nutrient cycling | *none* (proxy: county acres fertilised) | — | — |
| Carbon sequestration | NRCS Rapid Carbon Assessment (RaCA) | RaCA region | one campaign; satellite-pedon SOC predicted from VNIR spectra |
| Pest regulation | *none* (proxy: PNSP modelled county pesticide use) | — | — |
| Water capture | *none* (proxy: county irrigated cropland) | — | — |
| Soil macrofauna | *none* (ECOTOX = lab bioassays, no place) | — | — |

**Exact computation** (`analysis/fonte/compute.py`, runs from repo root in ~90 s):

- *Yield*: streamed `qs.crops_20260912.txt.gz`; kept `AGG_LEVEL_DESC == COUNTY`,
  `STATISTICCAT_DESC == YIELD`, `PRODN_PRACTICE_DESC == ALL PRODUCTION PRACTICES`,
  `DOMAIN_DESC == TOTAL`; rejected any `VALUE` beginning `(` (suppression codes —
  `VALUE` is a string, per the brief); counted distinct `STATE_FIPS||COUNTY_CODE` per
  year.
- *Profitability / practices / input proxies*: same treatment over the five Census
  files (2002–2022) for `INCOME, NET CASH FARM, OF OPERATIONS - NET INCOME, MEASURED
  IN $` and five other series. **`DOMAIN_DESC == TOTAL` is essential**: 2012 and 2017
  repeat county income across producer-demographic domains, and omitting the filter
  more than doubles the county count (7,149 and 7,851 rows against a 3,078-county
  universe).
- *Erosion*: `pdftotext -layout` on `2022_NRI_Summary_Report.pdf`, parsed Table 15.
  459 data rows = 51 blocks × 9 years; the 51st block is the national Total, so
  **50 reporting units × 9 years**. Per landmine #3 in the brief, all nine years are
  taken from the single 2022 release; no NRI vintage is differenced against another.
- *Carbon*: `pdftotext -layout` on `RaCA_Methodology_Sampling_Summary.pdf`, parsed
  Table 2 (sites by region × land use). **17 regions, 6,418 sites, one campaign.**
- *Macrofauna / pest regulation*: streamed ECOTOX `tests.txt` (725,635 tests) joined
  to `validation/species.txt`; classified 460 species as earthworm (219, by
  Lumbricidae and 9 other megadrile families or orders Haplotaxida/Opisthopora), ant
  (162, Formicidae) or termite (79, Isoptera and 8 families); counted tests by
  `test_location` and by presence of a `latitude`.
- *Pesticide pressure proxy*: the corrected PNSP county panel
  (`pnsp_county_panel_corrected.parquet`, 1992–2018, California removed, aggregate
  rows removed — the panel the brief directs analysts to use).

**Joint observability.** For each of the 21 unordered pairs of the seven outcomes I
asked whether they share (a) any common year and (b) a spatial support on which both
are published. Counties nest in states, so a county series can be rolled up to meet a
state series. RaCA regions are NRCS MLRA soil-survey regions and do **not** nest in
states, so a RaCA-region series can only meet a series that can be cut from counties —
and even then only via a county↔MLRA-region reallocation the mirror does not supply.

---

## 3. The result

### 3a. 19.5% of the bundle-years are filled, and three quarters of those are yield

| outcome | direct timepoints, 1982–2022 | place × year observation cells | finest support |
|---|---:|---:|---|
| Yield | **41** | **108,970** | county |
| Profitability | 5 | 15,214 | county |
| Erosion control | 9 | 450 | state |
| Carbon sequestration | **1** | **17** | RaCA region |
| Nutrient cycling | 0 | 0 | — |
| Pest regulation | 0 | 0 | — |
| Water capture | 0 | 0 | — |
| *Soil macrofauna* | *0* | *0* | — |

- **56 of 287 outcome-years (19.5%) carry a direct measurement. 41 of those 56 (73.2%)
  are yield.**
- The spread in observation density between the best- and worst-measured *measured*
  outcomes is **108,970 : 17, a factor of 6,410**. Erosion to carbon alone is 26 : 1.
- Repeat depth — the thing that makes a before/after claim possible at all — is
  41 : 9 : 5 : 1 : 0 : 0 : 0 across the bundle.

Everything a "regenerative practice works" claim can be built on from this record is
therefore a claim about yield, with erosion as a distant second and a single
un-differenceable carbon number third.

### 3b. Carbon is the thinnest row, and it is the row mandates are argued on

RaCA states its own purpose as capturing conterminous-US soil carbon **"at a single
point in time"** (RaCA Methodology, Sampling and Summary, NRCS/Soil Survey Staff &
Loecke 2016, p. 1 — verbatim in the mirrored PDF). One campaign, field seasons
2010–11, 6,418 sites in Table 2, published regionally as 17 regions × 6 land-use
classes. Consequences, all of them structural rather than rhetorical:

1. **There is no second timepoint.** A carbon *sequestration* claim is a claim about a
   change. The national record contains a level, once. Nothing can be differenced
   against it. (Landmine #3 in the brief forbids the obvious substitute — SSURGO is
   not a time series.)
2. **Most of the carbon values are predictions, not measurements.** Only central-pedon
   and organic-horizon samples went to the Kellogg lab; satellite-pedon SOC is
   predicted from VNIR spectra (RaCA methodology, "Spectra Collection" and "SOC Stock
   Calculation" sections).
3. **Its spatial support joins to nothing else in the bundle.** RaCA regions are MLRA
   soil-survey regions; NRI erosion is published by state; NASS by county. Of the
   three pairs involving carbon, two (carbon × erosion, carbon × profitability) have
   **zero common years**, because NRI publishes 1982/87/92/97/2002/07/12/17/22 and the
   Census publishes 2002–2022 in fives — neither publishes 2010 or 2011.

### 3c. The bundle requirement fails: 4 of 21 pairs, never more than 3 of 7 at once

| pair | jointly observable? | common years |
|---|---|---|
| Yield × Profitability | yes (county) | 2002, 2007, 2012, 2017, 2022 |
| Yield × Erosion control | yes (state) | 1982, 1987, 1992, 1997, 2002, 2007, 2012, 2017, 2022 |
| Yield × Carbon sequestration | yes, but only after a county↔MLRA-region reallocation | 2011 only |
| Profitability × Erosion control | yes (state) | 2002, 2007, 2012, 2017, 2022 |
| **the other 17 pairs** | **no** | **none** |

- **4 of 21 pairs (19%) can be observed in the same place in the same year.**
- The maximum number of bundle outcomes simultaneously observable anywhere, ever, is
  **3 of 7** (yield + profitability + erosion), at **state** resolution, in **5 of 41
  years** (2002, 2007, 2012, 2017, 2022 — the intersection of the Census and NRI
  calendars).
- At county resolution the maximum is **2 of 7**, in the same 5 years; in the other 36
  years it is 1 of 7.
- There is **no place and no year in which 4 of the 7 are jointly observed.**

This is the finding the framework was chosen to produce. A framework that insists on
measuring the bundle together cannot be satisfied by this data system at any spatial
scale, in any year, for more than three of its seven members.

### 3d. Soil macrofauna: 9,402 toxicity tests, 112 of them locatable

ECOTOX contains **9,402 toxicity tests on soil macrofauna** (7,560 earthworm, 1,272
ant, 570 termite; 460 species). But ECOTOX is a *hazard* archive, not a monitoring
network:

- **112 of the 9,402 macrofauna tests (1.2%) carry a latitude**; 344 carry any US
  geographic code. Across all 725,635 ECOTOX tests, only 10,090 (1.4%) are geolocated.
- 1,505 macrofauna tests are field tests, but they are one-off experiments, not a
  repeated panel — there is no year-over-year national series of earthworm, ant or
  termite abundance anywhere in this mirror.

So the functional indicator at the centre of this research programme — and the one
tied in Fonte, Hsieh & Mueller (2023) to ~6.5% of global grain production — has **zero
federal observation cells** in 41 years. The corollary already established in-repo
(finding #4: 79% of applied mass has no comparable acute soil-fauna toxicity record;
glyphosate has 106 soil-fauna records and zero comparable endpoints) is the same hole
seen from the chemical side.

### 3e. Two further results, both inconvenient

- **The treatment variable is measured twice.** County-level cover-crop and no-till
  acreage — the practices a mandate would actually specify — exist in the Census for
  **2017 and 2022 only**. Before 2017 there is nothing at county level; the 2012
  Census reports these practices nationally only. A regulator writing a practice
  mandate has two national snapshots of current practice adoption, five years apart.
- **Even the best row is thinning.** County-level published crop yields fell from a
  mean of **2,943 counties per year in 1982–86 to 2,089 in 2018–22 (−29%)**. In 2022
  NASS published a corn-grain yield for 1,543 counties while the 2022 Census recorded
  corn grain harvested in 2,322 counties (unsuppressed) — the annual survey covers
  about two-thirds of the counties that actually grow the crop. The densest outcome in
  the bundle is getting less dense.

### Verification

The brief requires a headline recomputed a second way. Three were:

1. **NRI.** The parser yields 459 Table-15 data rows (51 blocks × 9 years) and reads
   the final national block as total-cropland sheet-and-rill erosion of **3.89
   t ac⁻¹ yr⁻¹ (1982) → 2.67 (2022)**. This matches, to the digit, the narrative claim
   on p. 2-9 of the same report ("declined from 3.89 tons per acre per year to 2.67")
   — a table parse checked against independently typeset prose. The 50-unit universe
   was confirmed by extracting the entity labels (which `pdftotext` places on the
   margin-of-error line, not the year line): 48 conterminous states + Hawaii +
   Caribbean, **no Alaska** (which has its own separate 2007 NRI in the mirror).
2. **Yield cells.** Recomputed with an independent `awk` pipeline over the same source
   with a separately written filter expression. Per-year county counts match the
   Python result exactly (1985: 2,946; 2000: 2,759; 2015: 2,488; 2022: 2,027), total
   108,970.
3. **RaCA sites.** Table 2 was re-added by hand from the extracted text, region by
   region: 386+379+408+292+362+383+404+392+402+400+395+374+365+376+395+354+351 =
   **6,418**, matching the parser. (Note: the published literature commonly cites
   6,148 *sites with complete data*; 6,418 is the Table 2 sampling total. I report the
   mirrored table's number and flag the discrepancy rather than reconciling it.)

---

## 4. Limitations

**What this does not show.** It does not show that any practice does or does not
improve any outcome. It is a census of the evidence base, not an effect estimate. No
causal or even associative claim about practices is made anywhere above.

**Which landmine applies.** #3 and #4 from the brief, both squarely.

- *#3 — NRI back-updates its own history.* Handled: all nine erosion years are read
  from the single 2022 release. No NRI vintage is compared against another, and
  SSURGO is not used at all.
- *#4 — joins across mismatched sampling frames.* This analysis is *about* that
  mismatch. I deliberately did not perform any of the joins I counted; I counted
  whether they are possible. The one pair I marked joinable-with-caveat (yield ×
  carbon, 2011) would require a county↔MLRA-region reallocation, which would itself be
  a modelling step, not a measurement.

**Judgement calls a reader may want to reverse.**

- *"Direct" vs "proxy" is my classification.* A reader who counts fertiliser
  expenditure as a nutrient-cycling measure, or irrigated acreage as water capture,
  would get a fuller matrix. I think that reader would be wrong — an input purchased
  is not a cycle closed, and the Orinoco result (Lavelle et al. 2014) is precisely
  that the service and the input rank systems differently — but the CSV carries both
  columns so the alternative can be drawn.
- *Erosion is model output, not measurement.* NRI erosion is RUSLE2 and WEQ applied to
  panel points (2022 NRI, "Soil Erosion Calculations"). I counted it as direct because
  it is a place-and-time-resolved estimate of the outcome itself, published with
  margins of error, and because doing otherwise would leave the ecosystem-service half
  of the bundle completely empty. But it is a model, and the 34% national decline it
  reports is a modelled decline.
- *The mirror is not the whole record.* Census county data exist back to 1997 in
  QuickStats; the mirror has 2002–2022. Including 1997 would move profitability from 5
  timepoints to 6, and joint observability from 5 years to 6. It changes no
  conclusion. Conversely, some series outside this mirror (USGS streamflow, the CEAP
  farmer survey, the Forest Inventory & Analysis plots) would add coverage for water
  and for repeated soil measurement; the claim here is about *this* federal mirror,
  which is the one assembled for this petition.
- *Suppression is treated as absence.* A `(D)` cell is a county where the value exists
  but cannot be published. For a petition's purposes — what can actually be shown —
  treating it as absent is the right call, but it is a call.

**The result that is inconvenient for the framework itself.** The framework wants the
bundle measured together. The honest answer is that this data system is not merely
uneven — for four of seven outcomes it is *empty*, and for a fifth it holds one
snapshot. So the whole-bundle question cannot be answered by re-analysis at all; it can
only be answered by new measurement. Which is, not incidentally, the direction the
participatory strand of this research programme points (Fonte et al. 2012): the
measurements that would fill these rows — infiltration, nutrient cycling rates,
macrofauna counts, predation assays, farm-level profit on the treated field — are
field measurements on working farms, made with the people who farm them. There is no
administrative dataset that substitutes.

**The one-sentence consequence for a mandate.** A federal practice mandate justified
on soil carbon would be resting its case on the single thinnest row in the record — one
national snapshot, mostly spectrally predicted, at a spatial grain that cannot be
joined to yield, profitability or erosion in any common year — while the outcomes that
would reveal a trade-off (nutrient cycling, pest regulation, water capture, soil
biota) cannot be measured at all, and therefore cannot register a loss.
