# The soil-biology evidence ladder has almost no rungs

**Lens:** the long-term replicated field-experiment framework developed by Kate Scow
and colleagues at UC Davis and the Russell Ranch Sustainable Agriculture Facility.
**Slug:** `scow` · **Analyst:** this is my analysis applying that published framework
to the federal mirror; nothing here is Scow's own statement, claim or opinion.

---

## The question, and why this framework makes it the right one

Regenerative-agriculture advocacy leans hard on soil biology. Cover crops feed the
microbiome; tillage destroys fungal networks; glyphosate sterilises the soil;
mycorrhizae will fix the carbon problem. These claims are made in a register that
implies a settled evidence base. The question this framework presses is prior to all
of them: **what was actually measured, in what design, over what duration, with what
replication?**

The framework is worth applying here because the published Russell Ranch work is
unusually explicit about how much design it takes to get a defensible soil-biological
answer, and about how often a cheaper design gets the sign wrong:

- Bossio, Scow, Gunapala & Graham (1998), *Determinants of soil microbial communities:
  effects of agricultural management, season, and soil type on phospholipid fatty acid
  profiles*, **Microbial Ecology** 36:1–12 — showed that management signal in microbial
  community composition is entangled with season and soil type, so a single-date,
  single-soil sample cannot separate them.
- Kong, Six, Bryant, Denison & van Kessel (2005), *The relationship between carbon
  input, aggregation, and soil organic carbon stabilization in sustainable cropping
  systems*, **SSSAJ** 69:1078–1085 — a ten-year Russell Ranch/LTRAS analysis; the
  carbon-input-to-stabilisation relationship only becomes estimable across a decade of
  maintained, replicated treatments.
- Schmidt, Gravuer, Bossange, Mitchell & Scow (2018), *Long-term use of cover crops and
  no-till shift soil microbial community life strategies in agricultural soil*,
  **PLoS ONE** 13(2):e0192953 — the community shift is detectable because the
  treatments had been maintained for years in a replicated design.
- Tautges, Chiartas, Gaudin, O'Geen, Herrera & Scow (2019), *Deep soil inventories
  reveal that impacts of cover crops and compost on soil carbon sequestration differ in
  surface and subsurface soils*, **Global Change Biology** 25:3753–3766 — 19 years of
  Russell Ranch plots sampled to 2 m. Cover-cropped conventional plots **gained**
  carbon at 0–30 cm and **lost** more of it at 30–200 cm. A shallow, single-timepoint
  survey would have reported the opposite sign of the true effect.

That last result is the methodological hinge. If a decades-long replicated experiment
with deep cores can reverse the conclusion of a shallow survey, then the burden of
proof for any claim about pesticides, tillage or cover crops and soil biology sits at
the level of design, not of assertion. So: **for the pesticide mass that is actually
applied to US cropland, what tier of soil-biological evidence does the federal record
hold?**

## What I did

### Data

| source | use |
|---|---|
| `data/derived/pnsp_county_panel_corrected.parquet` | 2018 applied mass by compound (California excluded, aggregate rows removed). Total 448.386 M kg over 330 compounds. |
| `data/raw/epa/ecotox/2026-09-14/ecotox_ascii_09_15_2026.zip` | `tests.txt`, `results.txt`, `validation/species.txt`, `validation/chemicals.txt` |
| `data/derived/compound_crosswalk_full.csv` | PNSP compound → DTXSID |
| `data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf` | design audit of the federal soil-carbon baseline (below) |
| 40 CFR 158.630 (eCFR / Cornell LII) | why the ECOTOX gap exists |

### Method

1. **Join on CAS, never names.** PNSP compound → DTXSID (crosswalk) → ECOTOX
   `cas_number`. Glyphosate is filed in ECOTOX as *N-(Phosphonomethyl)glycine*; a
   name join silently returns nothing. Eight high-mass compounds whose DTXSID is
   absent or left ambiguous in the crosswalk got a manual CAS (listed in
   `compute.py`); `METAM` needed 137-42-8 (metam-sodium) because the crosswalk
   DTXSID resolves to the free acid. Resolution: 279/330 compounds = **98.8% of
   applied mass**. The 1.2% unresolved is mostly microbial products
   (*Bacillus amyloliquefaciens*, *B. thuringiensis*) and petroleum/fatty-alcohol
   mixtures with no single CAS; it is carried through the output as its own
   category rather than dropped.
2. **Expand each compound to its CAS family** by systematic-name containment, so
   salts and tank mixes count as evidence (glyphosate expands from 1 to 28 CAS).
   This deliberately biases the record *upward*.
3. **Restrict to non-target soil biota.** `organism_habitat == "Soil"`, then four
   functional groups: earthworms and potworms (Annelida), springtails and soil mites
   (Entognatha + Arachnida), mycorrhizal fungi (Glomeromycota), and soil bacteria and
   protozoa (Monera + Protista + Cyanophycota). Plant-pathogenic fungi, plant-parasitic
   nematodes and soil-dwelling insect pests are **excluded on purpose** — see the
   target/non-target trap below. Note also the brief's warning that `ecotox_group`
   "Worms" contains marine polychaetes; the habitat + phylum filter avoids that.
4. **Assign each test a design tier** from `test_location`, `media_type`, `test_type`
   and `study_duration_*`:

   | tier | design |
   |---|---|
   | 0 | no record of any kind |
   | 1 | lab, not in a soil matrix (filter paper, agar, culture, water) |
   | 2 | lab, in soil, ≤ 14 d (OECD 207-style acute) |
   | 3 | lab, in soil, > 14 d or coded chronic (OECD 222/232-style) |
   | 4 | field, < 1 year |
   | 5 | field, ≥ 1 year |

5. **Require replication across studies.** A tier counts as attained only where at
   least **two distinct ECOTOX `reference_number`s** (independent published studies)
   sit at that tier or above. One unreplicated test row is not an established result —
   that is the whole point of the framework being applied. The one-study version is
   computed alongside and kept in the output CSV.
6. Weight each compound by its 2018 `high_kg` share of national applied mass.

Script: `analysis/scow/compute.py` (runs in ~11 s from anywhere).
Outputs: `data/derived/lens_scow_soil_evidence_ladder.csv` (the chart rows) and
`data/derived/lens_scow_compound_tiers.csv` (per compound × group detail).

## The result

### 1. The ladder collapses at the first rung

Share of the 448.4 M kg applied in 2018, by the strongest design that exists anywhere
in ECOTOX (≥ 2 independent studies):

| strongest design | earthworms & potworms | springtails & mites | mycorrhizal fungi | soil bacteria & protozoa |
|---|---:|---:|---:|---:|
| No record at all | 38.5% | 65.1% | 66.7% | **98.8%** |
| CAS unresolved | 1.2% | 1.2% | 1.2% | 1.2% |
| Lab, not in soil | 0.0% | 0.8% | 27.7% | 0.0% |
| Lab, in soil, acute | 2.3% | 1.2% | 1.2% | 0.0% |
| Lab, in soil, chronic | 55.5% | 1.4% | 2.1% | 0.0% |
| Field, single season | 1.7% | 29.5% | 1.3% | 0.0% |
| Field, ≥ 1 year | 0.8% | 0.8% | 0.0% | 0.0% |
| **no field evidence at all** | **96.3%** | **68.5%** | **97.5%** | **98.8%** |

**98.8% of the pesticide mass applied to US cropland has no measured record of any
kind — not one laboratory test — of its effect on soil bacteria or protozoa.**

That is not a gap in a thin database. ECOTOX's entire soil bacteria and protozoa
holding, across every chemical ever entered, is **118 tests from 9 published studies
covering 21 chemicals, with exactly one field test**. Its five commonest taxa are
*Anabaena variabilis*, *Chlorogloeopsis fritschii*, *Chroococcus minutus*,
*Anabaena cylindrica* and *Nostoc muscorum* — nitrogen-fixing cyanobacteria from
mid-century rice-paddy work. There are no records on heterotrophic soil bacteria at
all: no nitrifiers, no denitrifiers, no rhizobia, no actinobacteria, none of the
organisms that actually run nitrogen mineralisation and decomposition in a cropped
soil.

### 2. Multi-year field evidence is four cells wide

Exactly four compound × group combinations reach tier 5 with two or more independent
studies: chlorpyrifos and carbaryl on earthworms, chlorpyrifos and imidacloprid on
springtails and mites. Together those three compounds are **3.9 M kg, 0.87% of applied
mass**, and all three are insecticides applied at low mass; nothing in the
herbicide-dominated top of the use distribution comes close. **No compound
reaches multi-year field evidence for mycorrhizal fungi or for soil bacteria.**

### 3. Glyphosate: 26.6% of the mass, two mycorrhizal studies, zero bacterial ones

| group | tests | independent studies | strongest design (≥2 studies) |
|---|---:|---:|---|
| Earthworms & potworms | 51 | 19 | lab, in soil, chronic |
| Springtails & soil mites | 37 | 10 | field, single season |
| Mycorrhizal fungi | 8 | 2 | lab, not in soil |
| Soil bacteria & protozoa | 0 | 0 | **no record** |

Glyphosate's earthworm record is genuinely usable: 19 studies, many 28–70 d exposures
in natural soil. Its mycorrhizal record is 8 test rows from two studies — one lab study
on *Glomus mosseae* in a media mixture, one 400-hour field study on four *Glomus*-group
species. Its soil-bacterial record is empty. The "glyphosate sterilises the soil
microbiome" claim and the "glyphosate is harmless to soil microbes" claim are, in the
federal record, equally unevidenced.

### 4. The single-study artifact is doing most of the work

This is the finding that most changes how the earlier numbers should be read. If one
test row is allowed to establish a tier, 41.4% of applied mass "has field-scale
earthworm evidence". Requiring two independent studies drops it to 2.5%.

| variant | earthworms | springtails & mites | mycorrhizae | bacteria |
|---|---:|---:|---:|---:|
| k = 1 study (single test row counts) | 57.4% | 61.8% | 70.0% | 98.1% |
| **k = 2 studies (headline)** | **96.3%** | **68.5%** | **97.5%** | **98.8%** |
| k = 3 studies | 98.0% | 97.8% | 98.7% | 98.8% |

(values are "% of applied mass with no field evidence at all")

The concrete case: glyphosate's one-study tier-5 earthworm credit rests on a single
ECOTOX row — test 2080557, organism recorded only as "Annelida", no species, field,
natural soil, 2 years. One row, one study, one unnamed worm, and glyphosate appears to
have two years of field data.

### 5. Why the gap exists: the record was never asked for

The soil-habitat record is not small. It holds **137,463 tests from 11,457 published
studies**, of which 62,559 endpoint-bearing tests were conducted in the **field**. But
**93.9% of those field tests are on terrestrial crop plants**, and only **1.53% (956
tests)** are on the four non-target soil functional groups. Field-scale soil testing
infrastructure exists at enormous scale; it is pointed at crops and at target pests.

The immediate cause is regulatory. EPA's terrestrial and aquatic nontarget organisms
data requirements table at **40 CFR 158.630** lists an avian battery, a mammalian
battery, freshwater and estuarine fish and invertebrates, sediment invertebrates, and
honeybee acute contact toxicity (OCSPP 850.3020). It contains **no earthworm test, no
soil invertebrate test, and no soil microorganism test** — non-target plants are
handled separately at 158.660. Registration in the EU under Commission Regulation (EU)
No 283/2013 requires OECD 222 (earthworm reproduction), OECD 232 (collembolan
reproduction) and OECD 216 (soil microorganisms, nitrogen transformation). The US
record is thin because the US requirement does not exist, and ECOTOX — a literature
compilation — can only hold what someone had a reason to produce.

### 6. And the federal soil-carbon baseline cannot close the gap either

The obvious rejoinder is that soil carbon is the integrative measure, and the federal
government has one: the NRCS Rapid Carbon Assessment. Reading the methodology
(`RaCA_Methodology_Sampling_Summary.pdf`; Soil Survey Staff and T. Loecke, 2016,
S. Wills ed.) against what the Tautges et al. (2019) design required:

| RaCA, as documented | what a Russell-Ranch-style answer needs |
|---|---|
| "to capture information on the carbon content of soils across CONUS **at a single point in time**" (p. 3) | repeated measurement of the same plots over years |
| stratified by soil group × NLCD **land cover** (cropland, forest, pasture, range, wetland, CRP) | assignment to a **management treatment** — tillage, cover crop, amendment, rotation |
| 6,418 sites (1,263 cropland, 347 CRP), 5 pedons each at one centre plus 30 m in four cardinal directions | pedons within a site are subsamples, not independent replicates of a treatment |
| observational: land was already in its land cover when sampled | randomised assignment, so the treatment is not confounded with site quality |
| CRP sites added beside cropland sites "to quantify the program's impact on carbon stocks" | a CRP-vs-cropland difference here confounds practice with the fact that marginal, eroded land is what gets enrolled |
| bulk density sampled 0–50 cm; VNIR prediction for satellite pedons, laboratory carbon on central pedons only | Tautges et al. found the sign of the cover-crop effect **reversed** below 30 cm |

RaCA is a well-executed national baseline and it is described as exactly that by its
authors. It is not, and does not claim to be, an instrument for attributing carbon
change to management. Any "RaCA shows practice X builds soil carbon" claim is reading a
treatment effect out of a single-timepoint land-cover survey. Note also that the mirror
holds RaCA's documentation only — the regional summaries and the methodology — and that
`Rapid_Carbon_Assessment_Workbook_215.xlsx` in the mirror is an encrypted CDFV2 file
that will not open, so no pedon-level recomputation is possible from this repository.

## Verification

Every number above is printed by `compute.py`. Five independent checks:

1. **Independent reproduction of established repo finding #4.** Rebuilt from my own
   pipeline, glyphosate has exactly **106** soil-fauna result rows under the repo's
   five-family filter — matching `scripts/eda_08_evidence_gap.py` to the row. Those 106
   result rows come from only 15 distinct endpoint-bearing tests on the parent CAS (59
   across the CAS family): the published count is of *results*, not of studies, which
   is itself part of why the record looks deeper than it is.
2. **Mass total.** Panel sum 448.386 M kg vs `pnsp_national_corrected.csv` 2018 value
   448.386 M kg; difference 0.0000.
3. **Low/high estimate basis.** Recomputing every share on PNSP `low_kg` instead of
   `high_kg` moves no share by more than 4.85 pp, and moves every group's
   "no field evidence" headline by at most ~2 pp: earthworms 96.30% → 97.34%,
   springtails and mites 68.45% → 66.24%, mycorrhizae 97.54% → 97.81%,
   bacteria 98.79% → 99.22%.
4. **Media classification.** Counting ECOTOX's ambiguous `MIX` ("media mixture")
   code as soil rather than non-soil changes the headline shares by **0.00 pp** in all
   four groups.
5. **Replication threshold.** The k = 1 / 2 / 3 sensitivity is reported in full above
   rather than buried; the headline is the middle value and the direction of the
   sensitivity is stated.

## Limitations — what this cannot show

- **This is an audit of the evidence base, not a toxicity assessment.** Nothing here
  says any compound harms or does not harm soil organisms. "No record" means no record.
  Absence of evidence is the finding; it is not evidence of absence, and it is equally
  not evidence of harm. The framework's discipline cuts against advocacy in both
  directions.
- **ECOTOX is a literature compilation, so counts track research effort.** A compound
  with many records may simply have been fashionable. That biases the *relative*
  picture but not the central result: 98.8% of applied mass having literally zero
  soil-bacterial records cannot be explained by research fashion.
- **Registrant studies submitted to EPA are not in ECOTOX.** Some unpublished
  Data Evaluation Records exist for some compounds. But 40 CFR 158.630 does not require
  soil-organism testing, so there is no systematic body of such studies to be missing,
  and any that exist are not in the public federal record this project mirrors.
- **The tier assignment is only as good as ECOTOX's own coding.** `test_location`,
  `media_type` and `study_duration_unit` carry substantial `NC`/`NR` codes. Unknown
  durations default *downward* (acute rather than chronic; <1 yr rather than ≥1 yr),
  which is the conservative direction for a "there is less here than claimed" finding
  but does mean some genuine chronic work is being scored as acute.
- **Target/non-target exclusion is a judgment call with a large effect.** Excluding
  plant-pathogenic fungi, plant-parasitic nematodes and soil insect pests removes
  5,209 tests including 2,699 field tests. Included, the "soil microbe field evidence"
  numbers look far better — but the field fungal record is *Thanatephorus cucumeris*,
  *Tilletia*, *Fusarium*, *Alternaria solani*, *Sclerotinia*: fungicide efficacy trials
  asking whether the pathogen was suppressed. That is a legitimate body of work
  answering a different question. Anyone tempted to count it as soil-microbiome
  evidence should look at the species list first.
- **Salt/mixture CAS expansion is generous.** Counting a "glyphosate mixt. with
  atrazine" test as glyphosate evidence overstates the record. It was left in
  deliberately, in the direction that weakens the finding.
- **Which of the four landmines applies:** primarily #4, joins across mismatched
  sampling frames. PNSP is modelled county-level use; ECOTOX is a global literature
  compilation with no US-use sampling frame at all. The join produces a legitimate
  *coverage* statement — "how much of what is applied has been studied in what way" —
  and nothing causal. Landmine #3 is what kills the RaCA leg: RaCA is a single-timepoint
  baseline, and diffing it against anything, or reading management effects out of its
  land-cover strata, is precisely the error that section warns about.

## What it would take

To support the claims regenerative-agriculture advocacy already makes, the federal
record would need, at minimum: a soil-organism data requirement in 40 CFR 158.630
comparable to Commission Regulation (EU) No 283/2013 (OECD 207/222 earthworms, 232
collembolans, 216/217 soil microorganisms); at least one soil-function endpoint —
nitrogen transformation or respiration — measured on the twenty compounds that make up
80% of applied mass; and a resampled, treatment-assigned subset of RaCA rather than a
single-timepoint land-cover survey, sampled below 30 cm, on the evidence of
Tautges et al. (2019) that the shallow answer can carry the wrong sign.

None of that is exotic. Three of the four test guidelines already exist and are
routinely run by commercial laboratories for EU submissions. The federal record is
empty because nobody was required to fill it.

---

### Sources

- [Scow Soil Microbial Ecology Lab, UC Davis — Russell Ranch](https://scowlab.lawr.ucdavis.edu/russell-ranch)
- [Bossio, Scow, Gunapala & Graham 1998, *Microbial Ecology* 36:1–12](https://pubmed.ncbi.nlm.nih.gov/9622559/)
- [Kong, Six, Bryant, Denison & van Kessel 2005, *SSSAJ* 69:1078–1085](https://www.researchgate.net/publication/228623367_The_Relationship_between_Carbon_Input_Aggregation_and_Soil_Organic_Carbon_Stabilization_in_Sustainable_Cropping_Systems)
- [Schmidt, Gravuer, Bossange, Mitchell & Scow 2018, *PLoS ONE* 13(2):e0192953](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0192953)
- [Tautges, Chiartas, Gaudin, O'Geen, Herrera & Scow 2019, *Global Change Biology* 25:3753–3766](https://onlinelibrary.wiley.com/doi/abs/10.1111/gcb.14762)
- [40 CFR 158.630 — Terrestrial and aquatic nontarget organisms data requirements table](https://www.law.cornell.edu/cfr/text/40/158.630)
- [Commission Regulation (EU) No 283/2013, Annex Section 5](https://www.legislation.gov.uk/eur/2013/283/annex/section/5/division/5.6)
- [OECD Test No. 216: Soil Microorganisms, Nitrogen Transformation Test](https://www.oecd.org/en/publications/2000/01/test-no-216-soil-microorganisms-nitrogen-transformation-test_g1gh290f.html)
- USDA-NRCS, Soil Survey Staff and T. Loecke, 2016, *Rapid Carbon Assessment: Methodology, Sampling, and Summary*, S. Wills (ed.) — mirrored at `data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf`
