# Better by which metric, compared with what, on which soil, over what time horizon?

**Lens:** the soil-structure / trade-off framework developed by Johan Six and
colleagues (ETH Zürich, Sustainable Agroecosystems).
**Slug:** `six`. **Analyst:** this is my analysis applying their published
framework; nothing here is written in Six's voice, and no position is attributed
to him that does not appear in the cited papers.

---

## 1. The question, and why this framework makes it the right one

The literature Six and colleagues built has a consistent shape: a mechanism is
proposed, and then the *measurement protocol that would make the mechanism
visible* is interrogated until the original claim either survives or shrinks.

- [Six, Elliott & Paustian (2000)](https://doi.org/10.1016/S0038-0717(00)00179-6),
  *Soil Biology & Biochemistry* 32: 2099–2103, proposed the mechanism — slower
  macroaggregate turnover under no-till lets microaggregates form inside
  macroaggregates and occlude carbon.
- [Six, Ogle, Breidt, Conant, Mosier & Paustian (2004)](https://doi.org/10.1111/j.1529-8817.2003.00730.x),
  *Global Change Biology* 10: 155–160, then shrank the claim on two axes at once:
  newly converted no-till *increases* net global warming potential in both humid
  and dry regimes, and only adoption beyond roughly ten years reduces it, and
  then only in humid climates. That is the **time horizon** and the **which
  soil/climate** question made empirical.
- [Baker, Ochsner, Venterea & Griffis (2007)](https://doi.org/10.1016/j.agee.2006.05.014),
  *Agriculture, Ecosystems & Environment* 118: 1–5, made the **compared with
  what** question concrete for sampling: in essentially every trial where
  conservation tillage appeared to sequester carbon, soil was sampled to 30 cm or
  less, while roots go far deeper. The gain is frequently a redistribution
  toward the surface, not an addition to the profile.
- [Ellert & Bettany (1995)](https://doi.org/10.4141/cjss95-075), *Canadian
  Journal of Soil Science* 75: 529–538, supplies the correction: compare an
  **equivalent soil mass**, not a fixed depth, because tillage changes bulk
  density and a fixed-depth core therefore weighs different amounts of soil under
  the two treatments.
- [Pittelkow, Liang, Linquist, van Groenigen, Lee, Lundy, van Gestel, Six,
  Venterea & van Kessel (2015)](https://doi.org/10.1038/nature13809), *Nature*
  517: 365–368, is the trade-off statement: the three principles of conservation
  agriculture deliver their promised yield outcome only in specific
  combinations and conditions, and no-till alone frequently costs yield.

Applied to this repository, that framework asks one question of every claim in
the project: **better by which metric, compared with what, on which soil, over
what time horizon?** The deliverable below is an attempt to make the cost of
*not* answering those four visible, in two parts.

---

## 2. Part A — what the US federal soil-carbon record can and cannot adjudicate

**Source:** `data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf`
(Soil Survey Staff and T. Loecke, 2016, *Rapid Carbon Assessment: Methodology,
Sampling, and Summary*, S. Wills ed., USDA–NRCS). Read in full; the facts below
are quoted from its Project Design, Site Data Collection, Bulk Density, and SOC
Stock Calculation sections.

The headline is **partly good news, and it is worth reporting as such**:

> **RaCA does sample deep.** Pits were excavated to 50 cm or to a root-limiting
> layer, and probes or augers were used to sample genetic horizons from **50 to
> 100 cm**. Stocks are reported to 5, 30 **and 100 cm**. Cropland mean stock to
> 100 cm is 106.1 Mg C/ha (Table 8); the 0–5 cm, 5–30 cm and 30–100 cm split is
> given in Figure 10. RaCA is therefore *not* another shallow-sampling dataset,
> and it is not vulnerable to the Baker et al. (2007) criticism in its crudest
> form.

Three limits, however, determine what it can settle:

| Requirement | What RaCA has | Consequence |
|---|---|---|
| **Depth below the tilled zone** | Yes — genetic horizons to 100 cm | Profile-scale stocks are reportable |
| **Measured bulk density at depth** | **No.** Volumetric samples "when possible… between 0 and 50 centimeters". Everything below 50 cm uses bulk density **predicted** by a random-forest pedotransfer function (Sequeira et al. 2014a), reported accuracy 0.10–0.15 g cm⁻³ | The 30–100 cm layer — exactly where the no-till depth argument is settled — rests on modelled, not measured, density |
| **Equivalent soil mass** | **No.** The stock equation is `Σ (SOC_i × BD_i × Dep_i × (1 − CFRAG_i/100))` — a **fixed-depth** sum | RaCA reports the quantity Ellert & Bettany (1995) wrote their paper to replace |
| **A management attribute (tilled vs no-till)** | **No.** Stratification is by *soil group × land use–land cover* (Cropland, Forestland, Pastureland, Rangeland, Wetland, CRP). `RaCA_Field_Collection_Protocols.pdf` defines only land cover/use categories and vegetation cover, stage and species — no tillage, residue-management or rotation field¹ | No-till and conventional-till cropland are pooled inside one "Cropland" class |
| **Repeat measurement** | **No.** The stated design is to capture carbon "across the conterminous United States **at a single point in time**" | No change can be computed at all |

¹ One caveat on that row: the field data-entry workbook itself (Appendix C,
`Rapid_Carbon_Assessment_Workbook_215.xlsx`) arrives in this mirror as an
encrypted CDFV2 file and could not be opened. My "no tillage field" conclusion
therefore rests on the methodology report's own description of what was recorded
and on the field-collection protocol PDF, not on the spreadsheet's column list.
If a tillage attribute exists in NASIS but is undocumented in both, that would
change this row — and it would be worth someone requesting the data directly
(`soilshotline@lin.usda.gov`, per the report) to find out.

**Therefore:** the US federal soil-carbon record, as mirrored here, cannot
adjudicate *any* claim of the form "practice X raised soil carbon by Y". It
lacks the treatment variable, the repeat measurement, and the equivalent-soil-mass
basis. It can describe how much carbon is in US cropland and how it is
distributed with depth — a real and useful thing — and that is the boundary.
A project claim about carbon *gains* that cites RaCA is citing a cross-section.

---

## 3. Part B — a trade-off that is actually visible: no-till and herbicide reliance

### The hypothesis

No-till removes the mechanical seedbed pass. Something has to control the weeds
it used to control. If conservation tillage buys reduced erosion at the price of
higher herbicide reliance, US counties with more no-till should carry more
applied herbicide per hectare — and especially more of the "burndown" actives
that physically substitute for the tillage operation.

### What I did

**Data.**
- *Practice*: USDA NASS **Census of Agriculture 2017**
  (`data/raw/usda-nass/quickstats-bulk/2026-09-14/qs.census2017.txt.gz`), county
  rows, `DOMAIN_DESC = TOTAL`: no-till acres, conservation-tillage-excluding-no-till
  acres, conventional-tillage acres, cover-crop acres, total and harvested
  cropland acres, and ten crop acreages. 2017 is the **first** census to carry
  the tillage question.
- *Chemical*: USGS PNSP **EPest-low, 2017**, from
  `data/derived/pnsp_county_panel_corrected.parquet` (California already dropped,
  aggregate rows already removed).
- *Herbicide classification*: taken from NASS's **own** chemical classes in
  `qs.environmental_20260912.txt.gz`, where `DOMAINCAT_DESC` reads
  `CHEMICAL, HERBICIDE: (GLYPHOSATE = 417300)`. 243 herbicide names, 624
  insecticide/fungicide/other names. PNSP ships no class column, so this avoids a
  hand-curated roster. Matching is exact, then stereochemistry-tolerant
  (PNSP's `METOLACHLOR-S` vs NASS's `S-METOLACHLOR`), then prefix
  (`GLUFOSINATE` → `GLUFOSINATE-AMMONIUM`). Every fuzzy match is printed for
  audit; all 26 are genuine herbicides. Result: 121 compounds, 281.6 M kg =
  72.5% of all applied mass in 2017.

**Constructed variables.** `notill_share` = no-till acres ÷ (no-till +
conservation-excl-no-till + conventional) acres. `herb_kg_ha` = classified
herbicide mass ÷ harvested cropland hectares. `burndown` = glyphosate, paraquat,
2,4-D, dicamba, glufosinate, saflufenacil, carfentrazone.

**Filters.** Counties with ≥ 5,000 acres of both harvested and tilled cropland
and non-zero herbicide mass: **2,087 counties**, dropped 915. Retained counties
hold **95.4%** of national harvested cropland and **96.5%** of national applied
herbicide mass, so the filter is not doing quiet work. 4.5% of county no-till
acreage values are suppressed `(D)` and become missing.

**The design.** Rather than report one correlation, I estimate the same
coefficient five times, changing only which counties are treated as comparable —
`log(kg/ha) ~ notill_share`, with group fixed effects imposed by within-group
demeaning and crop mix imposed as ten harvested-acre shares. Standard errors are
HC1-robust.

### The result

Effect of **+10 percentage points** of no-till share on applied mass per hectare
(`data/derived/lens_six_notill_herbicide_tradeoff.csv`):

| Comparison group | all herbicides | glyphosate | burndown group |
|---|---|---|---|
| 1. Pooled, no controls | **+1.7%** (t=2.6) | **+3.4%** (t=4.6) | **+4.2%** (t=6.2) |
| 2. + state fixed effects | −0.1% (t=−0.1) | +0.2% (t=0.2) | +2.4% (t=2.6) |
| 3. + Crop Reporting District FE | −0.3% (t=−0.4) | −0.4% (t=−0.4) | +0.9% (t=1.2) |
| 4. + crop mix (10 shares) | **+3.7%** (t=7.2) | **+5.2%** (t=9.1) | **+4.9%** (t=8.7) |
| 5. + crop mix **and** CRD FE | +0.2% (t=0.5) | −0.6% (t=−0.9) | +0.6% (t=1.1) |

Expressed as the contrast between a real pair of counties — the 75th percentile
of no-till share (60.1%) against the 25th (18.1%) — the glyphosate answer is
**+15.3%** pooled and **−2.3%** within district and crop mix. Same counties,
same year, same variable. The sign changes.

**Three further results in the same direction.**

1. **Crop mix alone explains R² = 0.535** of county log herbicide intensity;
   no-till share alone explains 0.003. The dominant structure in this data is
   what is grown, not how it is tilled.
2. **The apparent trade-off is not a national fact.** Computing Spearman ρ
   separately *inside* each of the 204 Crop Reporting Districts with ≥ 5
   counties: median **−0.059**, IQR −0.400 to +0.240, 42% positive
   (Wilcoxon p = 0.046). 45 districts sit above ρ = +0.3 and 60 below ρ = −0.3.
   There is no single sign to report.
3. **The mirror image is equally spurious.** Run the same ladder with
   **cover-crop share** as the practice variable and the pooled answer is
   **−13.4% per +10 pp** (t = −9.0) — cover crops appear to cut herbicide use
   sharply. Fully controlled: **−0.9%** (t = −0.8). The apparent *benefit* of the
   regenerative practice and the apparent *penalty* of no-till are the same
   artifact wearing two faces.

Note rows 3 and 4 in the table. Geography alone removes the whole association;
crop mix alone *enlarges* it. The two confounders pull in opposite directions, so
there is no safe partial adjustment — "we controlled for region" and "we
controlled for crop" produce opposite headlines from identical data.

### Verification

Every headline was recomputed a second way.

1. **EPest-high instead of EPest-low**: pooled +1.7% (t=3.2), fully controlled
   +0.5% (t=1.2). Unchanged.
2. **Herbicide mass rebuilt from the raw source file**
   (`county-preliminary/2017PreliminaryEstimatesNoCA.zip`) rather than the
   derived parquet: 271.69 M kg vs 271.69 M kg, max |difference| across 2,087
   counties = **0.0000 kg**. The corrected panel is faithful for 2017.
3. **Non-parametric, no functional form**: the within-district Spearman result
   above reaches the same null without any log or linearity assumption.
4. **Independent replication on a different vintage** — Census of Agriculture
   **2022** tillage against PNSP **2018** herbicide, 2,137 counties: pooled
   Spearman ρ = **−0.014** (p = 0.53); all herbicides +0.3% pooled and +1.3%
   fully controlled; burndown +2.4% pooled and +1.5% fully controlled. The weak
   pooled association present in 2017 is not even stable across file vintages.
5. **External validation of the constructed practice variable**: the
   acreage-weighted no-till share of my 2,087-county sample is **37.4%** against
   the **37.0%** computed from the published national totals in the same Census
   file (104,452,339 / 282,211,485 acres). Sample covers 96.0% of national tilled
   cropland.

### The honest answer

**The US federal record does not show that no-till counties spray more
herbicide.** A weak positive association exists when every county in the country
is treated as comparable to every other; it does not survive being asked
"compared with what?". I looked for the trade-off with the most favourable
possible specification — the burndown actives that would carry the mechanism —
and it still does not survive.

That is *not* evidence that the trade-off does not exist. It is evidence that
**this data cannot see it**, for reasons given below. Reporting it as "no
trade-off found" would be as wrong as reporting the pooled +15.3% as a finding.

---

## 4. Limitations

**Landmine #4 from the brief (joins across mismatched sampling frames) applies,
and in an unusually severe form.** USGS EPest county estimates are constructed by
taking proprietary farm-survey application rates *per harvested crop acre* at the
Crop Reporting District level and multiplying them by **county harvested-crop
acreage** from NASS (Thelin & Stone, 2013, *Estimation of annual agricultural
pesticide use for counties of the conterminous United States*, USGS SIR
2013–5009). Two consequences:

1. Within a Crop Reporting District, county-to-county variation in EPest mass is
   *by construction* driven by county crop acreage, because the rate is the same.
   My row-3 and row-5 estimates therefore compare counties whose herbicide
   numbers were generated from the same rate table — they are close to a null by
   design, and their tightness around zero should not be read as a precisely
   estimated zero effect.
2. Across districts, real farmer behaviour does enter — but so does everything
   else about the region. The R² = 0.535 on crop mix is partly a measurement
   tautology, not only a real confound.

**A cross-sectional county correlation cannot establish direction.** Counties
adopt no-till *because* cheap post-emergence chemistry made it agronomically
possible; herbicide-tolerant corn and soybean systems and no-till diffused
together across the same geography. Confounding by crop mix, region and farm size
is severe and I have only conditioned on the first two. Nothing here separates
"no-till causes spraying" from "spraying enabled no-till" from "both are
symptoms of a corn–soy rotation".

**There is no time horizon available at all.** PNSP county estimates run
1992–2018. The Census of Agriculture asked the tillage question in **2017 and
2022 only**. The intersection is **one year: 2017**. No county in the United
States can be observed in this mirror before and after a change in its tillage
regime. Given that Six et al. (2004) found the sign of the no-till GWP effect
itself depends on whether adoption is under or over ten years old, a
single-cross-section answer is not an answer to the question the framework asks.

**There is no soil in this analysis.** I could not attach a soil property to a
county from anything in the mirror. RaCA regions are pre-2013 MLRA office regions
and do not resolve to counties; SSURGO is not present as a county summary; and
the brief's landmine #3 rules out treating SSURGO vintages as a series in any
case. So of the four questions this lens exists to force, this deliverable
answers *metric* and *compared with what*, partially answers *which soil* (only
as the district-to-district heterogeneity in §3, which is large), and cannot
answer *over what time horizon* at all.

**Erosion is asserted, not measured, on the benefit side.** I have framed this as
an erosion/herbicide trade-off but only measured the herbicide arm. The NRI
erosion tables are in `2022_NRI_Summary_Report.pdf` at state-and-year resolution,
which will not join to a county tillage share; and landmine #3 forbids mixing NRI
releases. The benefit side of this trade-off surface is therefore unquantified
here.

**Suppression is non-random.** 4.5% of county no-till acreage values are
suppressed under NASS disclosure rules, which fires preferentially in counties
with few operations reporting the practice. Those counties are dropped.

**What it would take.** To answer the question properly for the herbicide arm:
a county or field panel with (a) tillage observed in at least two periods, (b)
pesticide use measured rather than allocated from a district rate — California's
PUR (`data/raw/ca-dpr/pur/`) is the only source in this mirror with that
property, and California is precisely what the corrected PNSP panel drops. For
the carbon arm: repeat sampling of the same pedons, measured bulk density below
50 cm, a tillage attribute, and stocks computed on an equivalent-soil-mass basis.
RaCA has the depth. It has none of the other three.

---

## 5. Files

| file | contents |
|---|---|
| `analysis/six/compute.py` | produces everything above; runnable from repo root |
| `data/derived/lens_six_notill_herbicide_tradeoff.csv` | the 15 rows the chart needs (3 outcomes × 5 specifications) |
| `data/derived/lens_six_county_panel_2017.csv` | 2,087-county backing table |
| `analysis/six/chart.json` | chart spec |

`compute.py` requires `pandas`, `numpy`, `pyarrow` and `scipy`. Runtime ≈ 32 s,
most of it decompressing the two Census bulk files. It prints every number quoted
above, including the fuzzy chemical-name matches for manual audit.
