# Substitution, not redesign: the US pesticide mixture collapsed onto one compound while the federal redesign indicator moved two percentage points

*Analysis slug: `altieri`. Framed by the agroecological transition framework
associated with Miguel Altieri and colleagues. Nothing below is written in
Altieri's voice, and no position, quotation or finding is attributed to him:
the framework supplies the question and the standard of judgement; every number
comes from the federal mirror in this repository.*

---

## 1. The question, and why this framework makes it the right one

Agroecology as developed by Altieri treats the agroecosystem — not the input —
as the unit of analysis. In *Agroecology: The Science of Sustainable
Agriculture* (Altieri 1995) and in *Biodiversity and Pest Management in
Agroecosystems* (Altieri & Nicholls 2004), the argument is that the ecological
functions an industrial farm buys in a drum — weed suppression, insect
regulation, nutrient cycling — are functions that a structurally diversified
system performs for itself. Altieri (1999) sets out the mechanism: biodiversity
in agroecosystems is not decoration but the substrate of pest regulation and
soil fertility, and simplification is what destroys it.

That framework carries a specific, and awkward, diagnostic. Nicholls, Altieri &
Vazquez (2016) restate the widely used three-phase conversion sequence —
(1) increased **efficiency** of input use, (2) **input substitution** with more
benign inputs, (3) system **redesign** through diversification that lets the
agroecosystem "sponsor its own soil fertility, natural pest control, and crop
productivity" — and then pose the question that organises this analysis: do
practices that fine-tune or substitute inputs, *while leaving the monocultural
structure intact*, actually lead anywhere? (The three-phase sequence originates
with Hill (1985) and MacRae et al. (1990); Gliessman (2007) extends it to five
levels. Nicholls et al. cite the sequence rather than claiming it.)

The diagnostic value is that the three phases leave **different fingerprints in
use data**:

| phase | expected signature in a national pesticide-use record |
|---|---|
| efficiency | total applied mass falls; composition roughly stable |
| input substitution | total mass roughly flat; composition churns, and concentrates as one product wins |
| redesign | total mass falls *and* the chemically-substituted function is visibly performed by structure instead |

This repository has already established the first half of that second row:
national applied mass is roughly flat (+14.7% over 26 years, +2.3% on a fixed
compound roster) while glyphosate went 6.9 → 119.2 M kg. The question this
analysis asks is whether that is really substitution, tested properly rather
than asserted — and whether the federal record contains any countervailing
redesign signal.

**The question: between 1992 and 2018, did the applied pesticide mixture become
more diverse or less, and did any measurable agroecosystem redesign accompany
the change?**

---

## 2. What I did

### Data

| source | file | use |
|---|---|---|
| USGS PNSP, county × year × compound, EPest-low/high kg | `data/derived/pnsp_county_panel_corrected.parquet` | the mixture. California dropped from **every** year; the double-counted `METOLACHLOR & METOLACHLOR-S` and `DIMETHENAMID & DIMETHENAMID-P` aggregate rows dropped. 9,111,543 rows, 519 compounds, 1992–2018, ~3,005 counties/yr |
| USDA NASS Agricultural Chemical Use | `data/raw/usda-nass/.../qs.environmental_20260912.txt.gz` | federal active-ingredient → pesticide-class map, read out of `DOMAIN_DESC` / `DOMAINCAT_DESC` |
| USDA Census of Agriculture 2012 / 2017 / 2022 | `data/raw/usda-nass/.../qs.census{2012,2017,2022}.txt.gz` | cover-crop, no-till, conservation-tillage and conventional-tillage acreage; total cropland acreage |

All computation is in `analysis/altieri/compute.py`; run it from the repo root.

### Metrics

**Chemical diversity of the applied mixture.** For a set of compounds with mass
shares *p*, the **effective number of compounds** is the inverse Simpson index
1 / Σ*pᵢ*², i.e. the number of equally-used compounds that would produce the
observed concentration. It is reported here rather than raw compound counts for
one reason that matters: it is *insensitive to rare compounds*, so the growth in
the reported compound roster (270 in 1992 → 343 in 2013 → 330 in 2018) cannot
manufacture a downward trend. exp(Shannon) is computed as a more
richness-sensitive companion. Both are computed:

- **nationally**, on annual compound totals; and
- **per county-year**, then summarised across counties (median). The county
  figure is the agroecologically meaningful one — it is closer to the scale at
  which a cropping system is actually designed.

Sensitivity runs use (a) EPest-**low** instead of EPest-high, and (b) a **fixed
roster** of the 143 compounds reported in all 27 years.

**Functional split.** Herbicide / insecticide / fungicide / other shares of
applied mass, using the NASS `DOMAINCAT_DESC` class for 355 compounds (87.9% of
1992–2018 mass); 23 ingredients that appear under more than one NASS class are
resolved to the class they are overwhelmingly surveyed under (sulfur →
fungicide, paraquat → herbicide, methyl bromide → other). A declared manual
table in `compute.py` covers a further 60 compounds (12.0% of mass) that NASS
spells differently or never surveyed — dominated by metam (5.4%) and
metolachlor-S (3.4%). The residual 0.06% is carried as `UNCLASSIFIED`, not
dropped. The full map is written to
`data/derived/lens_altieri_compound_classes.csv`.

**The redesign indicator.** The Census of Agriculture is the only federal series
in this mirror that measures *structure* rather than inputs at national scope:
cover-crop acres, no-till acres, conservation-tillage acres, conventional-tillage
acres, each as a share of total cropland, for 2012, 2017 and 2022. `VALUE` is
parsed as a string; thousands separators stripped, suppression codes `(D)`/`(Z)`
returned as missing.

**The joint test.** Cover-crop and tillage shares exist at county level only from
2017, so the two records are joined at **state** level for 2012 and 2017 (n = 47;
California excluded by the PNSP correction, Alaska and Hawaii absent from PNSP),
both cross-sectionally and as 2012→2017 *changes*. Spearman rank correlation
throughout.

---

## 3. Result

### 3.1 The mixture concentrated by roughly half, and richness is not the reason

| | 1992 | 2012 | 2018 |
|---|---|---|---|
| **effective no. of compounds, national** | **23.80** | **8.77** | **10.37** |
| ... fixed 27-year roster | 18.82 | — | 6.80 |
| ... EPest-low basis | 20.42 | — | 8.66 |
| exp(Shannon), national | 44.96 | 25.49 | 26.59 |
| **effective no. of compounds, median county** | **9.04** | **4.84** | **5.42** |
| compounds reported nationally | 270 | 339 | 330 |
| **compounds applied in the median county** | **101** | **125** | **89** |
| compounds making up half of all applied mass | 8 | 5 | 5 |
| compounds making up 80% of applied mass | 29 | 18 | 18 |
| total applied mass (M kg) | 390.8 | 416.5 | 448.4 |

The national effective number of compounds fell **−63% to its 2012 trough and
−56% over the full period**, on flat-to-rising total mass. The county median
fell −46% to 2012 and −40% over the full period.

The decisive line is the one in bold third from the bottom. **The median county
did not stop using many different pesticides** — 101 distinct compounds in 1992,
125 in 2012, 89 in 2018, with no systematic downward trend, out of a national
roster that *grew* by a fifth. What changed is that the mass collapsed onto a
handful of them. Counties in which glyphosate alone exceeded 25% of applied mass went from
**1.1% of counties in 1992 to 58.5% in 2018**; counties above 50% went from
0.07% to a peak of 13.4% (2010). This is not a shrinking pharmacopoeia. It is
the same pharmacopoeia with one product doing most of the work — the textbook
appearance of input substitution inside an unchanged system.

Every sensitivity points the same way and most point harder: the fixed-roster
series falls further (18.8 → 6.8) because roster growth was *masking* part of
the concentration, and the EPest-low series falls from 20.4 to 8.7.

### 3.2 The substituted function is weed control

| share of applied mass | 1992–96 mean | 2008–12 mean | 2014–18 mean |
|---|---|---|---|
| herbicide | 57.6% | 63.3% | 68.5% |
| insecticide | 14.6% | 10.6% | (not comparable, see §4) |
| fungicide | 6.9% | 6.2% | 6.6% |
| other (fumigants, PGRs, desiccants, minerals) | 20.7% | 19.9% | 17.4% |

Herbicide share of mass rose ~11 points; glyphosate went from **3.1% of all
herbicide mass in 1992 to 38.8% in 2018**. On the NASS-classified subset alone
(i.e. discarding every compound assigned by the manual table) the herbicide
share is 61.5% → 72.2%, the same movement.

Read through the framework, this is the most specific result in the analysis.
Weed suppression is the function a diversified rotation, a competitive cover
crop and a restored soil seedbank ecology deliver structurally. It is also the
function that has been chemically substituted hardest and most completely, and
the substitution consolidated onto a single mode of action.

### 3.3 The one redesign signal the federal record carries, and how small it is

USDA Census of Agriculture, national:

| | 2012 | 2017 | 2022 |
|---|---|---|---|
| cropland (M acres) | 389.7 | 396.4 | 382.4 |
| **cover crop planted (M acres)** | **10.28** | **15.39** | **17.99** |
| **cover crop, % of cropland** | **2.64%** | **3.88%** | **4.70%** |
| no-till, % of cropland | 24.76% | 26.35% | 27.52% |
| conservation tillage excl. no-till, % | 19.67% | 24.66% | 25.39% |
| conventional tillage, % | 27.13% | 20.18% | 19.21% |

Cover-crop acreage grew **+74.9% in a decade** — a real and fast-moving number,
and the only thing in this mirror that looks like structural diversification at
national scale. It reached 4.70% of cropland. At the realised 2012–2022 rate of
+0.77 M acres/year, simple arithmetic (not a forecast) puts cover crops on half
of US cropland in about **225 years**.

Meanwhile the conservation practice that *did* move at scale is tillage
reduction: no-till plus other conservation tillage covers 52.9% of cropland in
2022, up from 44.4% in 2012, while conventional tillage fell 8 points. In US
row-crop systems, tillage is precisely the weed-control operation that herbicide
substitutes for.

### 3.4 The joint test: no-till regions are glyphosate regions; cover-crop expansion tracks nothing

*(These are between-state associations. See §4 for why the no-till coefficient
must not be read as a farm-level effect.)*

State level, n = 47, Spearman ρ:

| | 2012 | 2017 |
|---|---|---|
| no-till % of cropland vs **glyphosate share of applied mass** | **+0.615** (p < 0.0001) | **+0.556** (p < 0.0001) |
| cover-crop % of cropland vs effective no. of compounds | +0.536 (p = 0.0001) | +0.423 (p = 0.0031) |
| cover-crop % of cropland vs glyphosate share | −0.430 (p = 0.0026) | −0.285 (p = 0.052) |

Contrast of extremes, 2017: the ten states with the **highest** no-till share
average a **34.4%** glyphosate share of applied mass and **6.85** effective
compounds; the ten with the **lowest** average **14.3%** and **10.00**. In 2012
the gap is wider still (40.6% / 5.11 vs 15.9% / 10.27).

Changes, 2012 → 2017 (which difference out fixed state characteristics):

| | ρ | p |
|---|---|---|
| Δ cover-crop % vs Δ effective no. of compounds | +0.121 | 0.42 |
| Δ cover-crop % vs Δ glyphosate share | −0.245 | 0.096 |

Cover-crop share rose in **41 of 47 states**. In **28 of those 41**, the
effective number of compounds rose as well — but the correlation between the two
is indistinguishable from zero. Cover crops expanded; the chemical mixture did
whatever it was going to do regardless.

The cross-sectional cover-crop correlations run the *opposite* way to a naive
"cover crops accompany chemical intensification" story, and honesty requires
saying so: states with more cover cropping have more diverse chemistry and less
glyphosate. But that correlation is a crop-mix artifact, not evidence of
redesign. The high-cover-crop states are Maryland (28.8% of cropland), Delaware
(19.5%), Connecticut, New Jersey and Virginia — Chesapeake-Bay and Northeastern
states with nutrient-management cost-share programmes and a large specialty-crop
sector, which is independently why their pesticide mixtures are diverse. Once
state identity is differenced out, the association vanishes.

### 3.5 Verdict

On the three fingerprints in §1, the federal record matches row two and only row
two. Total mass did not fall, so this is not an efficiency transition.
Composition churned violently and concentrated onto one compound and one
function, which is substitution. The one structural indicator that moved at
scale — tillage reduction — is spatially coincident with the chemical
concentration rather than opposed to it, and the one indicator that is
unambiguously diversification — cover cropping — is at 4.7% of cropland and
uncorrelated with any chemical de-concentration.

**Twenty-six years of the federal pesticide record are a record of input
substitution. The redesign phase is not visible in it.**

---

## 4. Limitations

**This is descriptive association, not causation** (landmine #4). PNSP is
*modelled* county use built from proprietary CRD-level farm surveys; the Census
of Agriculture is a farm census. They are different sampling frames joined at
state level, and the state-level n is 47. Nothing here identifies a causal link
between no-till adoption and glyphosate use; the Spearman coefficients are
descriptive, and both are plausibly driven by a third variable — the spread of
herbicide-tolerant row-crop genetics across the Corn Belt and Plains. That
third variable is itself the substitution mechanism, but this data cannot
demonstrate it.

**The no-till coefficient in §3.4 is a geographic co-occurrence, not a practice
effect.** A parallel analysis in this repository (`analysis/six/`) regresses
county-level herbicide use on no-till share and finds the pooled association
(+1.7% per 10 pp no-till) is absorbed to zero by state fixed effects (−0.1%) and
by Crop Reporting District fixed effects (−0.3%). My ρ = +0.62 is measured
across states, so it is precisely the between-geography variation that those
fixed effects remove, and it should be read that way: the regions that adopted
no-till at scale are the regions whose chemical mixture concentrated onto
glyphosate — not evidence that a given farm adopting no-till thereby uses more
glyphosate. For the argument here that distinction matters less than it might
appear, because the claim being made is about the *national pattern of
conversion*, not about a farm-level treatment effect. But the causal reading is
unavailable and I am not making it.

**A method break at 2015 invalidates the insecticide series after 2014**
(landmine #2). The mirrored PNSP metadata
(`2018PreliminaryEstimatesNoCA.zip → Metadata4PreliminaryPestUse2018noCA.xml`)
states plainly: *"Beginning 2015, the provider of the surveyed pesticide data
used to derive the county-level use estimates discontinued making estimates for
seed treatment application of pesticides… Pesticide use estimates prior to 2015
include estimates with seed treatment application."* Neonicotinoids are
predominantly seed treatments, so the 2015–2018 insecticide share is not
comparable with earlier years. I therefore report the insecticide decline only
to 2012 (14.6% → 10.6%), entirely inside the pre-break regime. The
diversity and herbicide results are not materially exposed: the 1992–2012
movement, which carries the whole result, is pre-break, and the post-2014 series
shows no discontinuity (national effective compounds 8.90 in 2015, 9.41 in 2016,
10.70 in 2017).

**Insecticide mass is a weak proxy for insecticide intensity.** Mass share falls
partly because modern chemistries are applied at far lower rates per acre. The
insecticide result should be read as "less insecticide *tonnage*", never as
"restored biological pest regulation" — which is what the framework actually
cares about and which this data cannot see at all.

**12.0% of applied mass is classified by a hand-written table.** It is declared
in `compute.py` rather than hidden, and the herbicide result survives dropping it
(§3.2), but it is a judgement layer. The largest single entry, metam (5.4% of
mass), is a soil fumigant assigned to `OTHER`; assigning it elsewhere would move
the `OTHER` and receiving shares by several points but does not touch the
herbicide trend.

**Diversity indices measure the mixture, not the agroecosystem.** A falling
effective number of compounds is consistent with substitution, but it is not
*proof* of an unchanged system — a genuinely redesigned farm might also apply few
compounds, at low mass. What rules that reading out here is the direction of
total mass (flat to rising) and the fact that compound *richness* per county held
steady. Still, the index is a proxy, and the framework's real object —
functional biodiversity, trophic structure, biological pest regulation on the
farm — is not measured by any federal series in this mirror. That is itself a
finding: the federal record instruments inputs in extraordinary detail and
instruments agroecosystem structure with four acreage lines, collected every five
years, only two of which pre-date 2017 at county resolution.

**California is absent by construction.** The corrected panel drops California
from every year to avoid the known 2017–18 discontinuity (established finding
#2), so ~12–13% of national mass — and the country's most diversified
specialty-crop cropping systems — are outside this analysis. Their inclusion
would very likely raise the level of every diversity measure; whether it would
change the *trend* is not testable from the corrected panel.

**Landmines #1 and #3 do not apply**: no crop-composition or soil-time-series
claims are made here; no SSURGO vintages are differenced and no NRI figures are
used.

---

## 5. Verification

`compute.py` prints a verification block. Every check passes:

1. **Glyphosate share and total mass** recomputed from the county parquet match
   `pnsp_national_corrected.csv` (built by a different script,
   `scripts/eda_04_corrected_series.py`) to 3.6e−15 pp and 1.1e−13 M kg.
2. **Effective number of compounds recomputed from a different file.** Rebuilt
   from `pnsp_compound_year_matrix_noCA.csv` — an independently produced
   compound × year matrix — it matches the parquet route to 1.1e−14 for
   1992–2015 and diverges for 2016–2018 (2018: 11.576 vs 10.375). The
   divergence is *expected and diagnostic*: that matrix is California-corrected
   but not aggregate-corrected, and still carries the two double-counted
   aggregate columns, which exist only from 2016. Dropping those two columns
   restores exact agreement across all 27 years (max |diff| 1.1e−14). This
   independently re-detects established finding #2 and confirms the correction
   is live in my numbers.
3. **County decomposition closes.** The mass-weighted mean of county-level
   glyphosate shares equals the national glyphosate share to 1.1e−14 pp in all
   27 years.
4. **Census acreage closes.** National cover-crop, no-till and cropland acreage
   equals the sum of the 50 state rows exactly (diff = 0) in 2012, 2017 and 2022.
5. **Class-map coverage** reported explicitly (87.9% NASS / 12.0% manual /
   0.06% unclassified by mass), with the herbicide trend recomputed on the
   NASS-only subset.

---

## References

- Altieri, M.A. (1995) *Agroecology: The Science of Sustainable Agriculture*,
  2nd edn. Boulder, CO: Westview Press.
- Altieri, M.A. (1999) "The ecological role of biodiversity in agroecosystems."
  *Agriculture, Ecosystems & Environment* 74(1–3): 19–31.
- Altieri, M.A. & Nicholls, C.I. (2004) *Biodiversity and Pest Management in
  Agroecosystems*, 2nd edn. Boca Raton, FL: CRC Press.
- Nicholls, C.I., Altieri, M.A. & Vazquez, L. (2016) "Agroecology: Principles for
  the Conversion and Redesign of Farming Systems." *Journal of Ecosystem &
  Ecography* S5: 010. doi:10.4172/2157-7625.S5-010.
- Hill, S.B. (1985) "Redesigning the food system for sustainability."
  *Alternatives* 12(3–4): 32–36. — origin of the
  efficiency/substitution/redesign sequence; Nicholls et al. (2016) cite the
  three-phase model to MacRae et al. (1990), which builds on Hill.
- Gliessman, S.R. (2007) *Agroecology: The Ecology of Sustainable Food Systems*,
  2nd edn. Boca Raton, FL: CRC Press. — the five-level extension of the same
  sequence.

## Files produced

| file | contents |
|---|---|
| `analysis/altieri/compute.py` | everything above, runnable from repo root |
| `analysis/altieri/chart.json` | the visualization spec |
| `data/derived/lens_altieri_simplification.csv` | tidy long series behind the chart |
| `data/derived/lens_altieri_class_shares.csv` | herbicide/insecticide/fungicide/other mass shares by year |
| `data/derived/lens_altieri_state_panel.csv` | state × {2012, 2017} cover crop, no-till, glyphosate share, effective compounds |
| `data/derived/lens_altieri_compound_classes.csv` | the compound → class map used, with the source of each assignment |
