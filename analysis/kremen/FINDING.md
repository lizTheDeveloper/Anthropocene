# A county is not an ecological unit

**Lens:** diversified farming systems and landscape-scale pollinator / natural-enemy
ecology, as developed in the published work of Claire Kremen and colleagues.

**Slug:** `kremen` · **Analyst output:** this file, `chart.json`, `compute.py`,
`data/derived/lens_kremen_cropdiversity_vs_insecticide.csv`,
`data/derived/lens_kremen_county_detail.csv`

*Attribution note, per the shared brief: nothing below is written in Claire Kremen's
voice and no opinion is attributed to her. What follows is my analysis of this data
mirror, using the analytical framework set out in her published work and in the
adjacent landscape-and-pesticide literature. The numbers come from the mirror.*

---

## 1. The question, and why this framework makes it the right one

The diversified-farming-systems (DFS) framework defines diversification as the
intentional inclusion of functional biodiversity **at multiple spatial and temporal
scales** in order to regenerate the ecosystem services that agriculture depends on —
pollination, pest control, soil fertility, water regulation (Kremen, Iles & Bacon 2012;
Kremen & Miles 2012). The spatial clause is not decoration. It is the empirical core
of the framework, and it is what distinguishes DFS from a checklist of field practices.

The evidence for the spatial clause is specific and quantitative. Kremen, Williams &
Thorp (2002) found that native bee communities delivered full pollination of watermelon
on organic farms near natural habitat, and failed to on farms that were conventional
and/or isolated from it. Kremen et al. (2004) then put a distance on it: pollination
services were predicted by the **proportion of natural upland habitat within 1–2.5 km
of the farm**, a scale matching the maximum foraging distance of the largest bees in
the system (~2.2 km); farm type, insecticide use, field size and honeybee abundance
were *not* significant predictors in that model (adj. R² = 0.49). The threshold results
were ≥40% natural habitat within 2.4 km, or ≥30% within 1.2 km, for full native-bee
pollination. Kennedy et al. (2013), with Kremen as senior author, generalised this
across 39 crop systems: wild-bee abundance and richness rose with diversified and
organic management *and* with high-quality surrounding land cover, and — crucially for
what follows — conventional, low-diversity fields were the ones that benefited **most**
from good landscape context. Landscape context substitutes for on-farm management.

That is the framework's sharpest claim about data: **a farm's ecological outcomes are
not determined by its own management alone.** If that is right, then a record that
describes only (a) political units and (b) field-level practices cannot see the variable
that governs the outcome. It will systematically mis-attribute landscape effects to
field management, or miss them entirely.

That is exactly the shape of the federal record this project is built on. The USGS
Pesticide National Synthesis Project reports pesticide mass **by county**. The Census of
Agriculture reports cover crop, tillage, and crop acreage **by county** and by practice.
A county is a 19th-century administrative rectangle. It is not a foraging radius, a
watershed, a dispersal neighbourhood, or a patch.

So the question I put to the mirror is a falsifiable one:

> **Can the county-level federal record detect the landscape-simplification signal at
> all?** Specifically: does a county-level crop-composition diversity measure, built
> from the Census of Agriculture, predict insecticide mass per harvested acre in the
> direction the landscape literature predicts — simpler landscapes, more insecticide?

This is not a strawman. It is the design of two well-known papers. Meehan, Werling,
Landis & Gratton (2011) used exactly this combination — county land cover, the Census
of farm practices, and a regional pest-monitoring network across seven Midwestern
states — and found that the proportion of harvested cropland treated with insecticides
rose with the proportion and patch size of cropland and **fell with the proportion of
seminatural habitat in a county**. Larsen (2013) published a direct rebuttal arguing
the result is not robust across specifications. Larsen & Noack (2017), working at
**field** rather than county resolution over >100,000 Kern County field-observations,
found that higher crop diversity does reduce insecticide use but that the relationship
is **strongly confounded by which crop types occur in diverse versus simple
landscapes** — and that cropland extent is distance-dependent, nearby cropland
decreasing and distant cropland increasing insecticide use. Their own summary is that
neither the "simplified" nor the "complex" landscape is straightforwardly better.

I chose insecticides rather than total applied mass deliberately. Insecticide mass is
the most defensible link in this mirror to pollinator and natural-enemy outcomes: it is
the fraction of applied chemistry that acts directly on the arthropod communities whose
landscape dependence the framework is about. Total mass in this record is 27% glyphosate
(established finding 1) and is dominated by herbicides and soil fumigants that speak to
weed management and soil sterilisation, not to the pollination/pest-control services at
issue.

---

## 2. What I did

### Data

| input | use |
|---|---|
| `data/raw/usda-nass/quickstats-bulk/2026-09-14/qs.census2017.txt.gz` | crop composition, **primary** (year-matched to PNSP 2018) |
| `.../qs.census2022.txt.gz` | crop composition, independent recomputation |
| `data/derived/pnsp_county_panel_corrected.parquet` | county × year × compound applied mass, kg |

### Crop-composition diversity

From the Census of Agriculture I built, per county, harvested acreage in **45 mutually
exclusive crop groups** (filters: `AGG_LEVEL_DESC = COUNTY`, `DOMAIN_DESC = TOTAL`,
`UNIT_DESC = ACRES`, `STATISTICCAT_DESC = AREA HARVESTED`,
`PRODN_PRACTICE_DESC = ALL PRODUCTION PRACTICES`). The NASS commodity hierarchy
overlaps itself, so the de-duplication is explicit and is listed in `compute.py`:
`HAY & HAYLAGE` replaces `HAY` + `HAYLAGE`; `WHEAT, ALL CLASSES` replaces winter/spring/
durum; `COTTON, ALL CLASSES` replaces upland/Pima; corn is grain + silage + traditional;
sorghum is grain + silage + syrup; individual vegetables (including potatoes) are
replaced by `VEGETABLE TOTALS, IN THE OPEN`; individual fruits and nuts by
`ORCHARDS - ACRES BEARING & NON-BEARING` (verified against 2022 national totals to equal
citrus + non-citrus + tree nuts, excluding berries); berries are their own group.

`VALUE` is a string with thousands separators and suppression codes; `(D)`, `(Z)`, `(NA)`,
`(H)`, `(L)` are parsed to missing, not to zero. Suppressed records are counted and
reported per county.

Per county I computed Shannon entropy *H* over the acreage shares and the **effective
number of crops, ENC = exp(H)** — an abundance-weighted richness that is robust to
suppression of tiny crops, unlike raw richness. Also: share in the largest crop group,
share in the top three, the dominant crop group, and **coverage** = summed group acres ÷
the Census item `AG LAND, CROPLAND, HARVESTED - ACRES`.

Counties were kept if harvested cropland ≥ 10,000 acres and coverage fell in
[0.85, 1.15]. **2,416 counties** survive, holding **303.5 M harvested acres** — 97.2% of
the 312.2 M acres of non-California US harvested cropland in the 2017 Census
(320.0 M national less 7.9 M California).

### Insecticide mass

From the corrected PNSP panel (California already dropped from every year; aggregate
rows already removed) I summed 2018 county mass over a **70-compound roster of
conventional synthetic insecticides, acaricides and insect-active nematicides** —
organophosphates, carbamates, pyrethroids, neonicotinoids, diamides, spinosyns,
avermectins, insect growth regulators, and specific acaricides. The full roster is in
`compute.py`. Deliberately excluded: soil fumigants (metam, metam-potassium,
1,3-dichloropropene, chloropicrin, methyl bromide, dimethyl disulfide), horticultural
oils, sulfur, kaolin, lime sulfur, cryolite, microbial and botanical biologicals, and
organophosphate defoliants/PGRs (tribufos, ethephon). All 70 roster compounds are
present in the 2018 data. The roster totals **13.29 M kg**, 2.96% of the 448.4 M kg of
2018 EPest-high national mass.

Normalisation: **grams of roster insecticide per acre of harvested cropland**. EPest-high
is primary; EPest-low is reported alongside throughout.

### The test

Spearman rank correlation of ENC against insecticide g/acre — pooled, then within
dominant-crop strata, then partialling out the share of cropland in high-input crops,
then restricted to counties that grow **none** of those crops.

---

## 3. The result

**The sign is wrong, and it is wrong decisively.**

| sample | n counties | median insecticide | Spearman ρ (ENC vs g/acre) | p |
|---|---|---|---|---|
| All counties | 2,416 | 20.8 g/ac | **+0.413** | 3.8 × 10⁻¹⁰⁰ |
| All counties, EPest-low | 2,416 | — | +0.312 | 8.2 × 10⁻⁵⁶ |
| Corn / soybean dominant | 1,060 | 22.3 g/ac | +0.292 | 3.3 × 10⁻²² |
| Hay & small grains dominant | 1,171 | 16.4 g/ac | +0.411 | 8.1 × 10⁻⁴⁹ |
| Southern row crops dominant | 156 | 143.1 g/ac | +0.612 | 2.2 × 10⁻¹⁷ |
| Specialty (veg/orchard/berry) dominant | 27 | 319.5 g/ac | −0.427 | 0.026 |

Counties with **more** crops in the Census sense use **more** insecticide per acre, not
less. The median rises monotonically from 7.7 g/acre in the least diverse bin
(ENC 1.0–1.5) to 116.0 g/acre in the most diverse bin (ENC ≥ 6) — a 15-fold gradient in the
direction opposite to the landscape prediction. Using share-in-the-largest-crop as the
simplification measure gives the mirror image (ρ = −0.333).

### Why: Census crop diversity measures the presence of a sprayed crop

Two decompositions establish it.

1. **High-input crop share.** Define `high_input_share` as the fraction of harvested
   cropland in cotton, vegetables, orchards, berries, tobacco, peanuts, rice,
   sugarbeets, sugarcane or hops — crops whose insecticide application rates are an
   order of magnitude above grain and forage. ENC is positively correlated with
   `high_input_share` (ρ = +0.285) and `high_input_share` is the stronger predictor of
   insecticide intensity (ρ = **+0.448**) than ENC itself. Median `high_input_share`
   rises from 0.6% in the least-diverse bin to **28%** in the most-diverse bin.

2. **Remove the confound entirely.** Restrict to the **263 counties that grow zero acres
   of any high-input crop** — pure grain, oilseed and forage counties, 44 M harvested
   acres. Within them the relationship **vanishes**:

   > ρ = **+0.057, p = 0.36** (Census 2017) · ρ = **+0.004, p = 0.95** (Census 2022)

   Median insecticide intensity across the ENC bins in that restricted sample goes
   15.8 → 16.1 → 23.4 → 23.8 → 27.9 → 20.8 → 17.2 g/acre. Flat, non-monotonic, null.

Two further observations sharpen the point:

- **The "simplest" counties in this record are not industrial monocultures.** Of the
  284 counties with ENC < 1.5, **270 are hay-dominated** — extensive forage and
  rangeland, with the *lowest* insecticide intensity in the dataset (7.7 g/acre median).
  The Census crop-diversity metric does not rank counties by intensification. It ranks
  them by whether they market more than one commodity.
- **The most "diverse" counties are the most chemically intensive.** Yakima County,
  Washington: ENC 5.37, 13 crop groups, orchard-dominant, **319 g/acre** of insecticide —
  6.5× Champaign County, Illinois (ENC 2.13, corn/soy, 49 g/acre). On a Census
  crop-diversity metric Yakima is the diversified landscape. In insecticide terms it is
  not.

### The deeper problem: the two axes are partly the same measurement

USGS constructs the county pesticide estimate by **multiplying Census of Agriculture
county harvested acreage of each crop by a Crop Reporting District median
pesticide-by-crop application rate** (Thelin & Stone 2013, USGS SIR 2013-5009; Baker &
Stone 2015, USGS DS 907; method statement confirmed on the USGS PNSP methods page).
EPest-low assumes zero use where a CRD reported none; EPest-high imputes from
neighbouring CRDs.

So the county pesticide number is, by construction, a crop-composition-weighted average
of *regional* application rates. It contains:

- **county crop composition** — which is the x axis of this chart, and
- **CRD-level application rates** — which vary at a scale several counties wide,

and **nothing else**. No field size. No patch geometry. No edge density. No seminatural
habitat. No distance to non-crop cover. Not at 1 km, not at 2.4 km, not at any scale.

This means the +0.413 correlation is not a landscape finding at all. It is close to an
identity: counties that grow crops with high application rates are estimated to receive
high applications. And it means the **null** result in the restricted sample is the more
informative number — once crop identity is held constant, the federal county record has
no residual signal left to carry a landscape effect, because it never encoded one.

**The federal pesticide record is not merely coarse about landscape configuration. It is
structurally incapable of representing it.**

---

## 4. A second, independent finding: the record loses the pollinator-relevant chemistry

While assembling the insecticide roster I checked the neonicotinoid series, since
neonicotinoids are the compound class most directly implicated in pollinator decline.
National EPest-high mass (California excluded in every year):

| year | clothianidin | thiamethoxam | imidacloprid | all neonics | all roster insecticides |
|---|---|---|---|---|---|
| 2013 | 1.570 | 0.570 | 0.837 | 3.021 | 17.862 |
| 2014 | 1.749 | 0.669 | 0.908 | **3.371** | 18.991 |
| 2015 | 0.010 | 0.129 | 0.308 | **0.497** | 15.167 |
| 2018 | 0.028 | 0.102 | 0.324 | 0.494 | 13.286 |

*(million kg)*

Neonicotinoid mass falls **85.3%** between 2014 and 2015 in a single step. This is not a
market event. Beginning with the 2015 estimates, the commercial survey vendor
discontinued estimating **seed-treatment** applications, and USGS therefore excludes
them (stated on the USGS PNSP methods page). The internal evidence matches exactly:
clothianidin, which in US field crops is almost entirely a corn and soybean seed
treatment, falls **−99.4%**; thiamethoxam, mixed seed and foliar, **−80.7%**;
imidacloprid, with large soil and foliar uses, only **−66.1%**. The ordering is the
signature of the methodology change, not of a withdrawal.

For this project the implication is direct: **the single most pollinator-relevant
insecticide class is the one this record tracks worst**, and any post-2015 trend line
through neonicotinoid use — or through total insecticide use, which drops 20% across the
same step — is measuring a survey decision. This belongs alongside established findings
2 and 3 as a third artifact in the same series.

---

## 5. Verification

Every headline number was recomputed by a second route.

| claim | primary | second route | agreement |
|---|---|---|---|
| Pooled ρ(ENC, insecticide g/ac) = +0.413 | Census 2017 × PNSP 2018 | Census **2022** × PNSP 2018: **+0.387**; Census 2017 × PNSP **2017**: **+0.501** | same sign, same order, all p < 10⁻⁸⁰ |
| Null in high-input-free counties, ρ = +0.057 (p=0.36) | Census 2017 | Census **2022**: ρ = **+0.004**, p = **0.95** | both null |
| EPest-high vs EPest-low | ρ = +0.413 | EPest-low ρ = +0.312 | robust to the imputation choice |
| Diversity measure is stable | ENC 2017 | ENC 2022, 2,272 shared counties: Spearman ρ = **+0.937** | the measure is not vintage noise |
| Champaign Co., IL (17/019) crop shares | pipeline: top1_share 0.5047, coverage 1.0003 | raw `qs.census2017.txt.gz` via `awk`: corn grain 277,293 + silage 563 = 277,856 of 550,537 grouped acres = **0.50470**; harvested cropland 550,359 | exact |
| Champaign Co. insecticide mass | pipeline (parquet): **26,946.1 kg** | raw `2018PreliminaryEstimatesNoCA.zip` → `EPest.county.estimates_NoDPR.2018.txt` summed by `awk` over the same roster: **26,946.1 kg** | exact |
| Neonicotinoid 2015 break | −85.3% in one year | compound-level ordering (clothianidin −99.4% ≫ imidacloprid −66.1%) plus the USGS published methods statement on seed-treatment discontinuation | two independent confirmations |

The crop-group construction validates itself: median county coverage
(grouped acres ÷ Census harvested cropland) is essentially 1.00, and the three spot-check
counties come in at 1.0003, 1.0026 and 0.99999. The 45 groups reconcile to the Census's
own harvested-cropland total without a residual, which means no significant crop area is
double-counted or dropped.

---

## 6. Limitations, honestly

**What this analysis cannot show.** It cannot show that landscape simplification does or
does not drive insecticide use in the United States. It shows that **this data cannot
answer that question**, and it identifies the mechanism of the failure. A null within the
restricted sample is not evidence of no landscape effect; it is evidence that the county
record carries no landscape information.

**Which of the four brief-listed landmines applies.** Landmine 4, *joins across
mismatched sampling frames*, applies and applies hard — but in a sharper form than the
brief's general warning. PNSP is not merely a different sampling frame from the Census
of Agriculture; PNSP is **derived from** the Census of Agriculture. The two sides of this
correlation are not independent measurements, so the association is not even
descriptive-but-confounded. It is partly definitional. I have labelled it as such
throughout and I would not let this correlation stand in any public output without that
label attached.

**The ecological-fallacy problem.** All of this is county-level. Nothing here licenses an
inference about any farm. Larsen & Noack (2017) is the demonstration that field-level and
county-level answers to this question differ in both magnitude and sign; the only
field-resolution application data in the country is the California DPR PUR archive in
`data/raw/ca-dpr/pur/` — and California is precisely what the corrected PNSP panel
excludes.

**Crop diversity is compositional, not configurational.** Even a perfect county crop
diversity measure would be the wrong measure. Kennedy et al. (2013) found landscape
*composition* effects on wild bees to be strong while landscape *configuration* effects
were weak; but "composition" there means the proportion of high-quality nesting and
floral resources within foraging distance, which is a very different quantity from "how
many commodities does this county market." The measure I could build is neither.

**Counterweight from the literature.** Karp et al. (2018), synthesising 132 studies and
6,759 sites, found that pest and natural-enemy responses to surrounding non-crop habitat
are highly variable and directionally inconsistent. The pollination evidence is more
consistent than the pest-control evidence. Any project ask that leans on landscape
context improving pest control specifically should cite that inconsistency rather than
around it.

**Roster judgement.** The 70-compound insecticide roster is my classification, not a
federal one — there is no pesticide-class field anywhere in this mirror. It is documented
compound-by-compound in `compute.py` so it can be contested. The exclusion of soil
fumigants is consequential: including them would roughly triple specialty-crop counties'
apparent insecticide load and strengthen the wrong-signed correlation further.

**Suppression.** Census `(D)` suppression removes small crop acreages in low-farm-count
counties, biasing ENC downward where suppression is common. Using the abundance-weighted
ENC rather than raw richness limits the damage, and per-county suppressed-record counts
are in `lens_kremen_county_detail.csv` for anyone who wants to test sensitivity.

---

## 7. What it would take — the concrete gap

**The NASS Cropland Data Layer is not in this mirror, and it is the single most valuable
missing dataset for any landscape-scale claim this project wants to make.**

- Annual, crop-specific land-cover raster for the conterminous US.
- **30 m resolution, complete CONUS coverage every year 2008–2023**; 10 m from 2024
  (also distributed resampled to 30 m for continuity). The programme began in 1997 with
  a single state; 2008 is the first complete-CONUS year.
- Built from Landsat 8/9 and Sentinel-2 imagery plus Farm Service Agency Common Land
  Unit ground truth. 100+ classes. Overall crop accuracy ~75–82% recently; major
  commodity crops 85–95%.
- Free, public, downloadable as rasters or via CropScape.

What it would add that nothing currently in `data/raw/` can:

| metric | why the framework needs it | available now? |
|---|---|---|
| Proportion seminatural / non-crop cover within a 1 km and 2.4 km buffer | the actual predictor in Kremen et al. (2004) | **no** |
| Mean field/patch size, edge density, patch-shape complexity | the Meehan et al. (2011) simplification predictors; the Larsen & Noack (2017) field-size effect | **no** |
| Crop diversity at a *foraging* rather than administrative scale | the county is an arbitrary unit; buffers are not | **no** |
| Distance-banded cropland extent (near vs. far) | Larsen & Noack (2017) found the sign reverses with distance | **no** |
| Annual crop rotation sequence per pixel | temporal diversification, the other half of the DFS definition | **no** |

Two caveats that should be written into any acquisition plan. (1) CDL's
**non**-agricultural classes (110–195) are inherited from USGS NLCD rather than
independently classified each year, so "proportion of seminatural habitat" from CDL is
only as good as NLCD and is not annually independent — a genuine weakness when the causal
story runs through natural habitat. (2) The 2024 resolution change from 30 m to 10 m is a
break in the series for any field-size or edge-density metric; use the resampled 30 m
products for cross-year work. NLCD itself would be the companion acquisition.

## 8. What this means for the project's eventual ask

The project's framing points toward mandating regenerative practices. Analysed through
the DFS framework, this analysis supplies two cautions that are load-bearing, and they
point in different directions.

**First, the measurement caution.** A practice mandate is only as good as the record that
would verify it, and the record this project holds is organised by political unit and
field-level practice. It can tell you that a county's cover-crop acreage went up. It
cannot tell you whether the resulting landscape supports a pollinator community, because
it does not record — at any scale, in any file in this mirror — the configuration
variables that the pollination literature identifies as the operative ones. If landscape
structure governs the outcome, then a field-level practice mandate verified against a
county-level record could be fully complied with and fully ineffective, and this data
would not be able to tell the difference. Acquiring CDL is the minimum fix.

**Second, and cutting the other way: on this evidence the practice-level lever is not the
one that is failing.** The DFS literature is consistent that the binding constraints on
diversification are structural rather than attitudinal. Carlisle et al. (2022) found that
even *already-organic* California Central Coast growers — people who have already cleared
the ideological and certification hurdle — face persistent structural barriers to further
diversification; Esquivel et al. (2021), from the same interview corpus, found that the
mid-scale growers who diversify most are distinguished by **secure land tenure, access to
capital, and buyers paying a premium**, which is a statement about who *can*, not who
*wants to*. Rosa-Schleich et al. (2019) document the mismatch that produces this: DFS
reduce negative externalities at landscape scale while imposing costs on the individual
farmer. Kremen & Merenlender (2018) put the same point at the end of a *Science* review:
many socioeconomic challenges impede uptake of biodiversity-based land management, and
voluntary incentives, market instruments, regulation and governance all matter.

There is also a data gap of the second kind here, and it is one this mirror can close.
The Census of Agriculture files already in `data/raw/usda-nass/` carry **land tenure,
farm size, crop insurance acreage, government-payment participation, and producer
demographics including race and ethnicity**, county by county — the exact structural
variables the adoption-barrier literature names, sitting next to the cover-crop and
tillage acreage. Whether diversification adoption in this country tracks tenure, credit
and insurance rather than region or attitude is a question this mirror *can* answer, at
county resolution, with no new acquisition. That seems to me the strongest available next
analysis, and the one most likely to change what the ask should be.

---

## References

Real, checked works. Where a figure is quoted I have noted the source of the figure.

1. **Kremen, C., Williams, N.M. & Thorp, R.W. (2002).** Crop pollination from native bees
   at risk from agricultural intensification. *PNAS* **99**(26): 16812–16816.
   doi:10.1073/pnas.262413599
2. **Kremen, C., Williams, N.M., Bugg, R.L., Fay, J.P. & Thorp, R.W. (2004).** The area
   requirements of an ecosystem service: crop pollination by native bee communities in
   California. *Ecology Letters* **7**(11): 1109–1119.
   doi:10.1111/j.1461-0248.2004.00662.x
3. **Kremen, C., Iles, A. & Bacon, C. (2012).** Diversified farming systems: an
   agroecological, systems-based alternative to modern industrial agriculture.
   *Ecology and Society* **17**(4): 44. doi:10.5751/ES-05103-170444
4. **Kremen, C. & Miles, A. (2012).** Ecosystem services in biologically diversified
   versus conventional farming systems: benefits, externalities, and trade-offs.
   *Ecology and Society* **17**(4): 40. doi:10.5751/ES-05035-170440
5. **Kennedy, C.M., Lonsdorf, E., Neel, M.C., Williams, N.M., Ricketts, T.H., Winfree, R.,
   et al. & Kremen, C. (2013).** A global quantitative synthesis of local and landscape
   effects on wild bee pollinators in agroecosystems. *Ecology Letters* **16**(5):
   584–599. doi:10.1111/ele.12082
6. **Kremen, C. (2015).** Reframing the land-sparing/land-sharing debate for biodiversity
   conservation. *Annals of the New York Academy of Sciences* **1355**(1): 52–76.
   doi:10.1111/nyas.12845
7. **Kremen, C. & Merenlender, A.M. (2018).** Landscapes that work for biodiversity and
   people. *Science* **362**(6412): eaau6020. doi:10.1126/science.aau6020
8. **Meehan, T.D., Werling, B.P., Landis, D.A. & Gratton, C. (2011).** Agricultural
   landscape simplification and insecticide use in the Midwestern United States. *PNAS*
   **108**(28): 11500–11505. doi:10.1073/pnas.1100751108
9. **Larsen, A.E. (2013).** Agricultural landscape simplification does not consistently
   drive insecticide use. *PNAS* **110**(38): 15330–15335. doi:10.1073/pnas.1301900110
10. **Larsen, A.E. & Noack, F. (2017).** Identifying the landscape drivers of agricultural
    insecticide use leveraging evidence from 100,000 fields. *PNAS* **114**(21):
    5473–5478. doi:10.1073/pnas.1620674114
11. **Karp, D.S., Chaplin-Kramer, R., Meehan, T.D., Martin, E.A., DeClerck, F., Grab, H.,
    et al. (2018).** Crop pests and predators exhibit inconsistent responses to
    surrounding landscape composition. *PNAS* **115**(33): E7863–E7870.
    doi:10.1073/pnas.1800042115
12. **Esquivel, K.E., Carlisle, L., Ke, A., Olimpi, E.M., Baur, P., Ory, J., Waterhouse,
    H., Iles, A., Karp, D.S., Kremen, C. & Bowles, T.M. (2021).** The "sweet spot" in the
    middle: why do mid-scale farms adopt diversification practices at higher rates?
    *Frontiers in Sustainable Food Systems* **5**: 734088. doi:10.3389/fsufs.2021.734088
13. **Carlisle, L., Esquivel, K., Baur, P., Ichikawa, N.F., Olimpi, E.M., Ory, J.,
    Waterhouse, H., Iles, A., Karp, D.S., Kremen, C. & Bowles, T.M. (2022).** Organic
    farmers face persistent barriers to adopting diversification practices in
    California's Central Coast. *Agroecology and Sustainable Food Systems* **46**(8):
    1145–1172. doi:10.1080/21683565.2022.2104420
14. **Rosa-Schleich, J., Loos, J., Mußhoff, O. & Tscharntke, T. (2019).**
    Ecological-economic trade-offs of diversified farming systems – a review.
    *Ecological Economics* **160**: 251–263. doi:10.1016/j.ecolecon.2019.03.002
15. **Thelin, G.P. & Stone, W.W. (2013).** Estimation of annual agricultural pesticide use
    for counties of the conterminous United States, 1992–2009. *USGS Scientific
    Investigations Report* 2013-5009. — the EPest method.
16. **Baker, N.T. & Stone, W.W. (2015).** Estimated annual agricultural pesticide use for
    counties of the conterminous United States, 2008–12. *USGS Data Series* 907.
17. **USDA NASS Cropland Data Layer** — programme description, resolution history and
    accuracy: https://www.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php

---

## Reproducing

```
python analysis/kremen/compute.py      # from repo root; needs pandas, numpy, scipy, pyarrow
```

Runtime ~6 minutes, dominated by streaming the two gzipped Quick Stats census files
(309 MB and 293 MB compressed). Writes
`data/derived/lens_kremen_cropdiversity_vs_insecticide.csv` (22 rows, the chart) and
`data/derived/lens_kremen_county_detail.csv` (2,416 rows, the audit trail), and prints
every statistic quoted above.
