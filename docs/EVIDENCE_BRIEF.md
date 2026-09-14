# Evidence Brief: The Case for Pesticide Phase-Outs and Regenerative Agriculture

**Compiled:** September 14, 2026
**Data basis:** 12.4 GB of mirrored federal data (14 datasets, 651 files), 8 independent lens analyses, 50+ peer-reviewed sources, and regulatory records. All federal data has SHA-256 provenance tracking in `data/provenance.csv`.

**Purpose:** Technical backing document for the petition to FDA, EPA, USDA, USGS, and CDC. Every claim is cited. Every limitation is flagged. This is the document someone would use to fact-check the petition and visual report.

---

## 1. Soil Erosion and Degradation

### 1a. NRI Erosion Panel (1982–2017)

The USDA Natural Resources Inventory provides the only national erosion time series:

- Cropland erosion declined **31.8%** between 1982 and 2017 (total: sheet, rill, and wind)
- **89% of that decline was achieved by 1997**, primarily through the Conservation Reserve Program and no-till adoption
- Since 2007, water erosion has **risen 2.7%**, reversing earlier gains
- **56.5 million acres** (18% of US cropland) still erode above the tolerable rate (T)
- The word "carbon" appears **zero times** in the 222-page 2022 NRI Summary Report

**Source:** USDA NRCS, Natural Resources Inventory. In project custody: `data/raw/usda-nrcs/nri/`
**Accessible charts:** https://ers.usda.gov/data-products/charts-of-note/chart-detail?chartId=94923

**Access status:** The 2022 NRI Summary Report (key erosion tables 15–18) is **inaccessible**. NRCS resets connections on resource URLs. The Internet Archive has one capture, truncated at exactly 5 MiB with no trailing `%%EOF`. The 2017 report is in custody and intact.

### 1b. Corn Belt A-Horizon Loss (PNAS 2021)

- **35% of cultivated Corn Belt area** has lost its entire A-horizon (organic-matter-enriched topsoil)
- A-horizon loss causes an average **6% crop yield reduction**
- This loss took millennia to build and is functionally irreversible on human timescales

**Citation:** Evan DL, Quinton JN, Tye AM, et al. "Soil loss across the US Corn Belt." *PNAS* 118(8), 2021.
**URL:** https://www.pnas.org/doi/10.1073/pnas.1922375118

### 1c. Historical Erosion (Thaler 2022)

- The Midwest has lost **57.6 billion metric tons of topsoil** over ~160 years of farming
- Median historical erosion rate: **1.8 ± 1.2 mm/year** — nearly double the USDA's tolerable rate
- Soil erodes **10 to 1,000 times faster** than pre-agricultural rates (median pre-ag: 0.04 mm/year)
- Even following USDA guidelines, current erosion is **25× the rate of topsoil formation**
- USDA NRI and DEP predictions are **3× to 8× lower** than historically averaged rates because they exclude tillage erosion

**Citation:** Thaler EA, Larsen IJ, Yu Q. "Rates of Historical Anthropogenic Soil Erosion in the Midwestern United States." *Earth's Future* 10, e2021EF002396, 2022.
**URL:** https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021EF002396

### 1d. Global Soil Carbon Deficit (Sanderman 2017)

- Agriculture has depleted an estimated **133 Gt of soil carbon** over 12,000 years
- US cropland accounts for approximately **6 Gt** of that loss
- A correction (2018) found the original estimate **underestimated** carbon loss at depth

**Citation:** Sanderman J, Hengl T, Fiske GJ. "Soil carbon debt of 12,000 years of human land use." *PNAS* 114(36):9575-9580, 2017.
**URL:** https://www.pnas.org/doi/10.1073/pnas.1706103114
**Correction:** https://www.pnas.org/content/115/7/E1700

### 1e. Soil Biodiversity Decline

- Glyphosate reduces earthworm hatching from **71% to 32%** (*A. caliginosa*): https://pmc.ncbi.nlm.nih.gov/articles/PMC4542661/
- Conventional agriculture simplifies mycorrhizal network structure with lower phylogenetic diversity: https://pmc.ncbi.nlm.nih.gov/articles/PMC9218867/
- Mycorrhizal fungi provide up to **80% of plant nitrogen and phosphorus** uptake: van der Heijden et al. 2015, *New Phytologist*
- Root colonization by AMF **decreased significantly** with just 2 applications of Roundup: Camenzind et al. 2023, https://www.sciencedirect.com/science/article/pii/S0929139322003948
- 2025 meta-analysis on pesticide impacts on soil microbial indicators: https://pmc.ncbi.nlm.nih.gov/articles/PMC12105574/

### 1f. Non-Federal Soil Data Sources

University and NGO data that can corroborate or fill gaps in the federal record:

| Source | Coverage | Time depth | Biology? | Open data? |
|--------|----------|------------|----------|------------|
| Morrow Plots (U of Illinois, est. 1876) | Single site, IL | 148 years | Yield/fertility | YES — R package `morrowplots` on CRAN |
| Sanborn Field (U of Missouri, est. 1888) | Single site, MO | 136 years | SOC trajectories | Peer-reviewed papers |
| KBS LTER (Michigan State) | SW Michigan | 37+ years | Yes — soil carbon, N cycling, microbes | YES — https://lter.kbs.msu.edu/ |
| NAPESHM (Soil Health Institute) | 124 sites, North America | Cross-section, 2,029 samples | Yes — 30+ indicators | YES — Ag Data Commons |
| NSF NEON | 81 sites, all US | ~10 years | Yes — metagenomes | YES — CC BY 4.0, https://data.neonscience.org/ |
| SoilHealthDB | 354 sites globally | 321 papers compiled | Yes | YES — Figshare |
| DSP4SH | 8 states | Cross-section | Yes — 37 lab parameters | YES — published May 2024 |
| SoilGrids (ISRIC) | Global, 250m | Snapshot | No | YES — CC BY 4.0 |

**Critical gap:** No non-federal source provides a national-scale soil health time series. Commercial soil labs (Ward, Midwest Labs, etc.) process millions of samples annually but the data is proprietary. Iowa's RCFI Analytics database (987,917 samples) is the closest anyone has come to aggregating it.

### 1g. Limitations

- NRI erosion values are **modelled**, not directly measured
- Converting erosion to carbon loss is contested across a **2 Pg/yr range**
- RaCA (the only national soil carbon measurement) is a **single snapshot** (~2010), ~1,263 lab-measured cropland pedons, with zero repeat measurements
- USDA's Soil Carbon Monitoring Network (SCMN) won't produce first repeat data until **FY2030+**
- SSURGO is **not a time series** — never diff vintages
- NRI **back-updates its own history** — always use a single release for both historical and current values

---

## 2. Pesticide Use Patterns

### 2a. National Trends (PNSP Corrected)

From the project's corrected USGS PNSP county panel (`data/derived/pnsp_county_panel_corrected.parquet`), with California excluded (USGS substitutes CA DPR PUR) and aggregate rows removed:

- **Total applied mass:** Roughly flat, +14.7% over 26 years (1992–2018); +2.3% on a fixed compound roster
- **Glyphosate:** 6.9 → 119.2 million kg (1.8% → 26.6% of mass), a **17× increase**
- **Everything else combined:** Mass fell over the same period
- The published 2016→2018 "decline" (-10.1%) is an **artifact** of California's absence and double-counted aggregate rows. Corrected: **+0.8%**

### 2b. Composition Shift

- **Effective number of compounds** fell ~56% nationally (23.8 → 10.4)
- At the county level: effective compounds fell from **9 → 4.8**
- This is classic **input substitution, not redesign or efficiency**

Source: Project Altieri lens analysis, `analysis/altieri/FINDING.md`

### 2c. The 2015 PNSP Seed Treatment Break

**CRITICAL METHODOLOGICAL CAVEAT:** Beginning 2015, the provider of the surveyed pesticide data discontinued making estimates for seed treatment application. The metadata in every preliminary zip states this verbatim.

Impact:
- Neonicotinoid EPest-high mass falls **85.3%** in one step (2014→2015)
- Clothianidin: **-99.4%**
- Thiamethoxam: **-80.7%**
- Imidacloprid: **-66.1%**
- Total insecticide mass drops **~20%** across the same step

**Any insecticide trend crossing 2014/2015 is measuring a survey decision, not the field.** Confine insecticide comparisons to ≤2014, or state the break explicitly.

### 2d. Cover Crop Adoption

- Cover crops reached **4.7% of US cropland** by 2022 (NASS Census of Agriculture)
- At the realized growth rate, cover crops would take **~225 years** to reach half of US cropland
- SARE/CTIC 2025 survey: 3% corn yield increase, 4.9% soybean yield increase after 5 consecutive years of cover crops
  - Report: https://www.sare.org/wp-content/uploads/CTIC_Cover_Crop_Report_2025.pdf

### 2e. Limitations

- PNSP county estimates are partly **derived from Census crop acreage**, making some correlations partly definitional
- County-level resolution cannot capture field-level variation
- PNSP stops at 2018 preliminary (no 2019 county file)
- California is excluded from 2017–2018 ("NoCA") — national totals from those years undercount the largest agricultural pesticide market

---

## 3. Regulatory and Toxicological Gaps

### 3a. ECOTOX Coverage Analysis

From the project's cross-reference of EPA ECOTOX full release with PNSP applied mass:

- **98.8%** of applied pesticide mass has **zero records on soil bacteria**
- **96.3%** has no field evidence on earthworms
- **97.5%** has none on mycorrhizal fungi
- Only **0.87%** reaches multi-year field evidence with ≥2 studies
- **79%** of applied mass has no comparable acute soil-fauna toxicity record
- Glyphosate: 106 soil-fauna records, **zero comparable endpoints**, **zero soil-bacterial records**

Source: Project Scow lens analysis, `analysis/scow/FINDING.md`

### 3b. US vs EU Regulatory Requirements

- **40 CFR 158.630** (US): Contains **no soil-organism test requirement** for pesticide registration
- **EU Regulation 283/2013**: Requires soil organism testing before authorization
- **72 pesticides** approved in the US are banned or being phased out in the EU
- **322 million pounds** of EU-banned pesticides are applied annually in US agriculture (2016 data)
- The US uses a **risk-based approach** (benefits vs. risks); the EU uses a **hazard-based approach** (precautionary principle)

**Sources:**
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6555703/
- https://www.ewg.org/foodnews/neonic-pesticides.php

### 3c. Glyphosate

| Development | Detail | Source |
|-------------|--------|--------|
| IARC classification (2015) | "Probably carcinogenic" (Group 2A) — based on NHL evidence in workers + animal carcinogenicity | WHO/IARC Monograph 112 |
| EPA contradicting assessment | "Not likely to be carcinogenic" | EPA Interim Registration Decision |
| Ninth Circuit vacatur (2022) | Vacated EPA's "not likely" finding; ordered EPA to redo human health assessment | https://nationalaglawcenter.org/ninth-circuit-orders-epa-to-revisit-conclusion-that-glyphosate-is-not-likely-to-cause-cancer/ |
| Ramazzini Institute (June 2025) | Dose-dependent tumors at EU ADI-equivalent doses; early-onset leukemia (zero historical controls in first year among >1,600 rats) | https://publichealth.gmu.edu/news/2025-06/international-study-reveals-glyphosate-weed-killers-cause-multiple-types-cancer |
| 2026 meta-analysis | Glyphosate–DLBCL: meta-RR = **1.29 (95% CI 1.02–1.63)**, statistically significant | https://pmc.ncbi.nlm.nih.gov/articles/PMC13512628/ |
| Supreme Court (June 2026) | *Monsanto v. Durnell*: FIFRA preempts state failure-to-warn claims (7-2) | https://www.cnbc.com/2026/06/25/glyphosate-roundup-bayer-supreme-court-case-monsanto.html |
| Bayer executive order (Feb 2026) | DPA declares glyphosate "critical to national defense"; grants Bayer legal immunity | One day after Bayer's $7B settlement proposal |
| AHS finding (2025) | Glyphosate use associated with mosaic loss of chromosome Y | Chang et al. 2025 |
| Gut microbiome (2023) | Selectively kills Lactobacillus/Bifidobacterium, spares Clostridium/Salmonella | https://www.sciencedirect.com/science/article/abs/pii/S1382668923000911 |
| Prenatal hormonal (2026) | Disrupts estrogenic, thyroid, and stress hormone systems | J. Exposure Science & Environ. Epidemiology |

### 3d. Neonicotinoids

- EU banned all outdoor use of imidacloprid, clothianidin, thiamethoxam in **2018**
- **95% of neonicotinoid applied to a seed** disperses into surrounding soil
- Soil half-lives **can exceed 1,000 days**; they accumulate with repeated use
- Earthworm DNA damage and reproduction reduction with bioaccumulation
- Critical nitrogen-fixing bacteria sensitive to imidacloprid
- Human evidence: neurotoxicity, hepatotoxicity, genotoxicity, reproductive impairment
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC13102768/
- US beekeepers losing **upward of 60% of hives** (2025)
- PNSP data break at 2015 systematically undercounts true neonicotinoid use in post-2014 federal data

### 3e. Chlorpyrifos

- **Columbia University cohort**: Prenatal exposure → visible brain abnormalities on MRI, lower IQ, developmental delays
  - https://www.publichealth.columbia.edu/news/brain-abnormalities-seen-children-exposed-prenatally-pesticide-chlorpyrifos
- **NEJM "Polluting Developing Brains"**: https://www.nejm.org/doi/full/10.1056/NEJMp1716809
- ~300 studies link chlorpyrifos to multi-organ damage
- Regulatory timeline: banned (2021) → court-reversed (2023) → tolerances reinstated (Feb 2024) → partial ban proposed with **11 crop exemptions**
- Originally developed as a **nerve agent in WWII**, repurposed as insecticide

### 3f. Atrazine

- Hayes et al. 2010: "Complete feminization and chemical castration" of male frogs at **below US drinking water limit** (3 ppb MCL)
- IARC Group 2A ("probably carcinogenic")
- EU banned since **2004**
- US still uses ~76.5 million lbs/year
- Contaminates drinking water of **40 million Americans**; exceeds health guidelines for **3 million**
- EPA **raised** the allowable limit in January 2025
- FWS reversed endangered species finding in May 2026
  - https://usrtk.org/pesticides/atrazine/

### 3g. Cumulative and Synergistic Effects

- 27 peer-reviewed studies document synergistic effects of pesticide mixtures
- Cumulative Risk Assessment (CRA) is **not implemented in either the US or EU**
- EFSA (2025) began identifying biological functions impaired by combinations
- Fungicide co-exposure **increases neonicotinoid toxicity** to pollinators
  - https://beyondpesticides.org/dailynewsblog/2026/06/literature-review-unpacks-synergistic-and-cumulative-pesticide-impacts-on-aquatic-life/

### 3h. Agricultural Health Study (AHS)

The largest prospective cohort study of pesticide applicators (89,000+ participants, 1993–present):

- **Cancer elevations** (despite healthy worker effect): prostate, lip, AML, myeloma, thyroid, testicular
- **Dose-response for neurological symptoms**: OR 1.64 (1–50 days), 1.89 (51–500 days), **2.50 (>500 days)** vs never users
- Glyphosate → chromosome Y loss; atrazine → nephrotoxicity; pesticides → Parkinson's, diabetes, rheumatoid arthritis
- Parkinson's disease formally recognized as **occupational disease** in French agricultural workers
  - https://www.aghealth.nih.gov/news/publications.html

### 3i. Limitations

- Glyphosate cancer evidence is strongest for **occupational exposure** (NHL); dietary exposure data is weaker
- EPA, EFSA (2023), and several national agencies found glyphosate "not likely" carcinogenic — the regulatory consensus is genuinely divided
- AHS studies are in **applicators**, not consumers — dose extrapolation required
- German BfR questioned Ramazzini study design
- Analytical method drift between historical and modern measurements can create artifacts

---

## 4. Nutritional Decline

### 4a. Davis 2004 — The Foundational Study

Compared USDA food composition data for **43 garden crops** between 1950 and 1999:
- Protein: **-6%**
- Riboflavin: **-38%**
- Statistically reliable declines also in calcium, phosphorus, iron, ascorbic acid
- No significant changes for 7 other nutrients

**Davis attributed declines primarily to yield/cultivar dilution, not soil depletion.**

**Citation:** Davis DR, Epp MD, Riordan HD. *J Am Coll Nutr* 23(6):669-82, 2004.
**URL:** https://pubmed.ncbi.nlm.nih.gov/15637215/

### 4b. Broadbalk Wheat Experiment (since 1843)

- Grain concentrations of Zn, Fe, Cu, Mg **stable from 1845 to mid-1960s**, then **declined significantly**
- Timing coincided with introduction of semi-dwarf, high-yielding cultivars
- **Soil mineral concentrations either increased or remained stable** over the same period
- Similar trends on plots receiving no fertilizer, inorganic fertilizer, OR organic manure

**This is the strongest evidence that nutrient decline is real (archived samples), AND that simple soil mineral depletion is NOT the primary mechanism.**

**Citation:** Fan MS et al. *J Trace Elements Med Biol* 22(4):315-324, 2008.
**URL:** https://pubmed.ncbi.nlm.nih.gov/19013359/

### 4c. Rising CO₂ Effects

**ter Haar, van Bodegom & Scherer (2025)** — the largest meta-analysis to date:
- **29,524 observation pairs** across 43 crops and 32 nutrients
- Rising CO₂ directly reduces protein, zinc, and iron in C3 crops
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/gcb.70568

**Myers et al. (2014)** — *Nature*:
- ~2.3 billion people get >60% of dietary Zn/Fe from C3 grains and legumes
- Estimated 2 billion already suffer Zn/Fe deficiencies, causing 63 million life-years lost annually
- **URL:** https://www.nature.com/articles/nature13179

### 4d. Montgomery & Biklé 2022 — Paired-Farm Comparison

Regenerative vs. conventional farms across the US (5–10 years of practice):
- Regenerative wheat mineral density gains: Boron **+41%**, Calcium **+48%**, Zinc **+56%**, Magnesium **+29%**, Molybdenum **4×**, Potassium **+26%**, Manganese **+35%**
- Higher soil organic matter, higher soil health scores

**Citation:** Montgomery DR, Biklé A. *PeerJ* 10:e12848, 2022.
**URL:** https://peerj.com/articles/12848/

### 4e. The Dilution Effect Debate — Honest Assessment

**Marles (2017)** — Health Canada's official review, the strongest published counterargument:
- Historical food composition comparisons are unreliable due to method changes
- Observed changes are within natural variation and "not nutritionally significant"
- **URL:** https://www.sciencedirect.com/science/article/pii/S0889157516302113

**The honest synthesis:**
1. **Yield/cultivar dilution** is real, well-documented, and explains a large portion of declines (strongest evidence)
2. **Rising CO₂** is a separate, independent mechanism confirmed by 29,524 observation pairs
3. **Soil biological disruption** (mycorrhizal/microbiome) reduces mineral uptake even from mineral-adequate soils — growing evidence but less definitive
4. **Simple soil mineral depletion** ("strip-mining") is the **weakest** explanation — Broadbalk showed minerals stable in soil while declining in grain

**The strongest policy argument is biological (mycorrhizal disruption by pesticides), not chemical (mineral depletion from soil).**

### 4f. Limitations

- Separating soil-management effects from cultivar effects requires **same-cultivar controlled studies** that don't exist at scale
- Montgomery & Biklé's paired-farm design partially addresses this but does not settle it
- Organic certification alone does not fix the problem — the evidence is for soil health practices, not the organic label per se

---

## 5. Human Health Outcomes

### 5a. NHANES Biomonitoring (Project Analysis)

From CDC NHANES 2013–2023 (n ≈ 31,000):
- Children aged 3–11 carry ~**1.9× adult body burden** for glyphosate, TCPy (chlorpyrifos metabolite), and 2,4-D
- Creatinine correction widened the gap
- Exposure is **universal and income-flat**: 77–99% detection rates, <3 percentage points across income brackets
- Nutritional deficiency is **income-steep**: 2–2.5× gap poorest vs. richest for iron, vitamin D, folate

Source: Project bodies_report analysis, `notebooks/bodies_report.html`

### 5b. Micronutrient Deficiency Trends

- Iron and zinc intake: **significant decline** 2003–2018 (NHANES)
  - https://ajcn.nutrition.org/article/S0002-9165(24)00124-2/fulltext
- **52.2%** of US population does not meet daily magnesium requirement
- Vitamin D deficiency prevalence **increased** 2001–2018
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9573946/

### 5c. Birth Cohort Studies

Three independent cohorts, all finding prenatal pesticide exposure → neurodevelopmental harm:

**CHAMACOS** (UC Berkeley, Salinas Valley):
- Prenatal organophosphate exposure → lower cognitive scores at age 2, attention deficits at 5, lower IQ at 7
- Children with PON1−108TT genotype (less detoxification enzyme) were most vulnerable
- Effects tracked into adolescence: delinquent behavior by age 16
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4338203/

**Columbia Center** (NYC, Rauh et al.):
- First MRI study of structural brain changes from prenatal chlorpyrifos
- Abnormal enlargement in some brain areas, thinning in others
- Higher exposure → lower full-scale IQ
- Effects at exposure levels **below EPA threshold for toxicity**
- Dr. David Bellinger (Harvard): Americans collectively lose **16.9 million IQ points** from fetal/childhood organophosphate exposure
  - https://www.pnas.org/doi/full/10.1073/pnas.1203396109

**CHARGE** (UC Davis):
- Residential proximity to agricultural pesticides during pregnancy → autism spectrum disorders and developmental delay
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4181917/

### 5d. Gut Microbiome Disruption

Glyphosate inhibits the EPSPS enzyme (shikimate pathway) in gut bacteria:
- **Lactobacillus and Bifidobacterium** (beneficial) are highly sensitive
- **Clostridium perfringens and Salmonella** (pathogenic) are tolerant
- 2023 metagenomics confirmation: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10561581/
- Low-dose exposure alters gut microbiota composition: https://www.sciencedirect.com/science/article/abs/pii/S1382668923000911

### 5e. Negative Finding: Iron Deficiency NOT Worsening

Project NHANES analysis found iron deficiency is **not worsening** over time: 14.0% in 2005 to 14.6% in 2023 — essentially flat. This contradicts the simplest version of the "declining nutrition" narrative and must be acknowledged.

### 5f. Limitations

- Birth cohort studies show association, establishing causation requires ruling out confounders
- Gut microbiome effects confirmed in animal models; in vivo human evidence is developing
- AHS dose-response data is in applicators, not the general population
- Joining NHANES exposure data with nutritional outcomes across mismatched sampling frames yields descriptive association, not causation

---

## 6. Data Erasure and Institutional Capacity

### 6a. Scale of Federal Data Removal

Since January 2025:
- **8,000+ federal web pages** modified or removed
- **~3,000 datasets** deleted from data.gov
- **3,000+ CDC pages** altered or removed
- **70% more website changes** in first 100 days than Trump's entire first term (EDGI)
- Environmental racism information **entirely excised** from all federal websites
- All five **National Climate Assessments** removed from public access

**Sources:**
- EDGI "Climate of Suppression" report: https://envirodatagov.org/publication/climate-of-suppression-environmental-information-under-the-second-trump-administration/
- UCS Attacks on Science Tracker: **574 documented attacks**, 343 impacting public health — https://www.ucs.org/resources/attacks-on-science
- Wikipedia tracker: https://en.wikipedia.org/wiki/United_States_government_online_resource_removals_under_the_second_Trump_administration

### 6b. This Project's Direct Experience

| Finding | Detail |
|---------|--------|
| FDA returns HTTP 401 | On every data path; 64 artifacts retrieved via Internet Archive `VIA_WAYBACK` |
| NRCS resets connections | On `/resources/` and `/sites/default/files/`; 38 artifacts via Wayback |
| 2022 NRI truncated | Only Wayback capture stops at exactly 5 MiB; key erosion tables missing |
| FDA FY2023 data | Published 2025-12-22; **not captured** by Internet Archive |
| TDS pesticide results | FY2018+ post-date newest Wayback capture |
| EPA CompTox | Requires API keys; training cancelled due to "federal travel restrictions" |
| Geospatial Data Gateway | **Decommissioned March 2026** |

### 6c. Workforce and Budget Destruction

| Cut | Detail |
|-----|--------|
| Conservation Technical Assistance | **$776.5M → $0** proposed |
| NRCS staff | 11,715 → 8,000 (**-32%**); 711 soil conservationists lost |
| Counties with zero NRCS staff | 0 → **141** |
| EPA Office of Research & Development | **Eliminated** — 1,155 scientists |
| Total USDA employees lost | **20,306** |
| ARS employees lost | **1,647 (-23%)** |
| USGS proposed budget cut | **-38%** |
| EQIP grants (2024–2025) | **-38%** |
| USDA contracts/grants cancelled | **$5.5 billion** by 100-day mark |
| BARC closure | Proposed despite 92% public opposition |

**Sources:**
- https://sustainableagriculture.net/blog/usda-staffing-crisis-widespread-loss-of-conservation-staff/
- https://climate.law.columbia.edu/content/epa-eliminates-office-research-and-development-will-cut-over-3700-staff
- https://www.dtnpf.com/agriculture/web/ag/news/article/2025/06/03/usda-budget-plan-slashes-technical

### 6d. Regulatory Capture and Industry Favor

- **26 officials with pesticide industry ties** appointed since January 2025
- **11 political appointees at EPA**, with former chemical industry lobbyists in the **four highest-ranking positions**
- **Glyphosate executive order** (Feb 18, 2026): DPA Section 707 grants Bayer legal immunity; signed one day after Bayer's $7B settlement proposal
  - Bipartisan **"No Immunity for Glyphosate Act" (HR 7601)** introduced: https://www.congress.gov/bill/119th-congress/house-bill/7601
  - FOIA lawsuit filed: https://www.thenewlede.org/2026/06/lawsuit-usda-glyphosate/
- **USDA rescinded pesticide recordkeeping** (June 2025): farmers no longer required to document restricted-use applications
- **NIH ended IARC collaboration** (March 2026): US scientists blocked from WHO cancer research
- **EPA "restricted science rule"** applied to exclude epidemiological studies from chlorpyrifos assessment
- USRTK tracker: https://usrtk.org/pesticides/tracking-trump-administration-favors-to-the-pesticide-industry/

### 6e. Preservation Efforts

- **Harvard Law School Library**: 16 TB archive, 311,000+ datasets from data.gov
- **EDGI**: Published research, preserved data, built access tools — https://envirodatagov.org/
- **Data Rescue Project**: 1,100+ public datasets from 80+ offices — https://www.datarescueproject.org/
- **Internet Archive End of Term**: Federal site captures during 2024 transition
- **Tracking tools**: https://essentialdata.us/in-memoriam and https://dataindex.us/terminations-tracker

---

## 7. Regenerative Agriculture Evidence

### 7a. Rodale Farming Systems Trial (43 years)

The longest-running side-by-side comparison of organic/regenerative vs. conventional (Kutztown, PA, 1981–present):
- Yields: organic **matches conventional** on average; **+30% in drought years**
- Soil organic matter: organic systems **continuously increasing**; conventional flat
- Energy: organic uses **45% less**; emits **40% fewer GHGs**
- Water infiltration: **2–3× greater** in organic plots
- Profitability: **3–6× higher** (partly due to organic premiums)

**URL:** https://rodaleinstitute.org/science/farming-systems-trial/

### 7b. LaCanne & Lundgren 2018 — Profitability

76 corn fields across the Northern Plains:
- Regenerative: **29% lower grain production** but **78% higher profits**
- Conventional: allocated **32%** of gross income to seed + fertilizer
- Regenerative: allocated **12%**
- Profit correlated with **soil particulate organic matter**, not yield

**URL:** https://peerj.com/articles/4428/

### 7c. Cover Crop Carbon Sequestration

**Poeplau & Don 2015**: Meta-analysis of 30 studies — cover crops sequester **0.32 ± 0.08 Mg C/ha/yr**
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0167880914004873

**Powlson et al. critique**: Soil carbon can contribute meaningfully but **cannot single-handedly offset fossil fuel emissions**. Organic amendments are often nutrient transfer, not net atmospheric sequestration.
**URL:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6001646/

### 7d. Policy Models

- **Costa Rica**: Payment for Ecosystem Services raised forest coverage **40% → 59%**: https://dialogue.earth/en/forests/50074-how-costa-rica-deforestation-millions-for-conservation/
- **EU Farm to Fork**: Targets 50% pesticide reduction, 25% organic by 2030
- **France "4 per 1000"**: 36 countries committed — aspirational but not quantitatively achievable alone: https://4p1000.org/
- **Sikkim (India)**: First 100% organic state (2016) — but ongoing struggles with yield, supply, imports: https://www.agdaily.com/insights/history-of-misery-when-farmers-are-forced-to-go-organic/

### 7e. The Sri Lanka Cautionary Tale

April 2021: President Rajapaksa banned all agrochemical imports overnight:
- Rice production fell **20% in 6 months**
- Overall food production dropped **40–50%**
- Tea yields fell **16%** (lowest since 1995)
- Economy contracted **7.8% in 2022**
- Ban revoked after 7 months

**This does not invalidate regenerative agriculture. It proves that transition must be funded, gradual, and supported.**

**Sources:**
- https://foreignpolicy.com/2022/03/05/sri-lanka-organic-farming-crisis/
- https://news.mongabay.com/2022/08/drawing-the-wrong-lessons-from-sri-lankas-organic-farming-experience-commentary/

### 7f. USDA Conservation Programs — Current Status

Conservation Technical Assistance: **$776.5M → $0** proposed (FY2026)
EQIP: **-38% decrease** in grants 2024–2025 despite +11% applicants
NRCS: From 11,715 to proposed 8,000 staff (**-32%**)
CTA is the **entry point** for farmers into EQIP and CSP — cutting it creates a cascade failure

**Sources:**
- https://www.dtnpf.com/agriculture/web/ag/news/article/2025/06/03/usda-budget-plan-slashes-technical
- https://www.kcur.org/environment-agriculture/2026-08-31/nrcs-cuts-impact-conservation-farmers

---

## 8. What the Evidence Does NOT Support

Intellectual honesty requires acknowledging what the data cannot prove:

1. **Total pesticide mass is NOT rising.** It's roughly flat (+14.7% over 26 years). The problem is composition shift and measurement failure, not volume increase.

2. **>99% of food residues are within EPA tolerance.** PDP 2024: 99% of 9,872 samples below tolerance. However, tolerances are set on acute toxicity, not chronic low-dose endocrine disruption, mixture effects, or developmental neurotoxicity.

3. **Iron deficiency is NOT worsening.** NHANES: 14.0% (2005) to 14.6% (2023) — flat. Iron and zinc *intake* are declining, but clinical deficiency is stable.

4. **Soil carbon decline cannot be demonstrated at national scale.** RaCA is one snapshot. SCMN won't produce repeat data until FY2030+. No national soil health time series exists from any source — federal or non-federal.

5. **Nutrient decline cannot be fully separated from cultivar selection.** The dilution effect is real. Broadbalk showed soil minerals stable. Same-cultivar controlled studies at scale don't exist.

6. **Overnight bans do not work.** Sri Lanka lost 40–50% food production. Any mandate must include transition periods, farmer training, and organic input supply chains.

7. **Soil carbon sequestration alone cannot offset emissions.** Powlson's Rothamsted critique is definitive on this point. It helps; it's one tool among many.

8. **Glyphosate regulatory consensus is genuinely divided.** EPA, EFSA (2023 re-approval), and several national agencies found it "not likely" carcinogenic. The IARC, Ramazzini Institute, Ninth Circuit, and 2026 meta-analysis disagree. Both positions cite real evidence.

---

## References — Key Sources by Domain

### Soil Erosion
- Evan et al. 2021. PNAS. https://www.pnas.org/doi/10.1073/pnas.1922375118
- Thaler et al. 2022. Earth's Future. https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021EF002396
- Sanderman et al. 2017. PNAS. https://www.pnas.org/doi/10.1073/pnas.1706103114
- Lal 2004. Science. https://www.science.org/doi/10.1126/science.1097396

### Pesticide Toxicology
- Ramazzini/GMU 2025. https://publichealth.gmu.edu/news/2025-06/international-study-reveals-glyphosate-weed-killers-cause-multiple-types-cancer
- 2026 meta-analysis. https://pmc.ncbi.nlm.nih.gov/articles/PMC13512628/
- Columbia chlorpyrifos MRI. https://www.pnas.org/doi/full/10.1073/pnas.1203396109
- Hayes et al. 2010 (atrazine). PNAS.
- AHS publications. https://www.aghealth.nih.gov/news/publications.html

### Nutritional Decline
- Davis et al. 2004. https://pubmed.ncbi.nlm.nih.gov/15637215/
- Fan et al. 2008 (Broadbalk). https://pubmed.ncbi.nlm.nih.gov/19013359/
- ter Haar et al. 2025 (CO₂). https://onlinelibrary.wiley.com/doi/10.1111/gcb.70568
- Montgomery & Biklé 2022. https://peerj.com/articles/12848/
- Marles 2017 (counterargument). https://www.sciencedirect.com/science/article/pii/S0889157516302113

### Regenerative Agriculture
- Rodale FST. https://rodaleinstitute.org/science/farming-systems-trial/
- LaCanne & Lundgren 2018. https://peerj.com/articles/4428/
- Poeplau & Don 2015. https://www.sciencedirect.com/science/article/abs/pii/S0167880914004873
- Powlson et al. (critique). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6001646/

### Data Erasure
- EDGI. https://envirodatagov.org/
- UCS tracker. https://www.ucs.org/resources/attacks-on-science
- USRTK tracker. https://usrtk.org/pesticides/tracking-trump-administration-favors-to-the-pesticide-industry/
- Harvard data archive. https://www.thecrimson.com/article/2025/2/6/hls-federal-data-vault-launch/
- Data Rescue Project. https://www.datarescueproject.org/

### Human Health
- CHAMACOS. https://pmc.ncbi.nlm.nih.gov/articles/PMC4338203/
- Columbia MRI. https://www.pnas.org/doi/full/10.1073/pnas.1203396109
- CHARGE. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4181917/
- NHANES micronutrient trends. https://ajcn.nutrition.org/article/S0002-9165(24)00124-2/fulltext
- Glyphosate-microbiome. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10561581/

### US vs EU Regulatory Gap
- USA lags behind. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6555703/
- EWG neonicotinoid report. https://www.ewg.org/foodnews/neonic-pesticides.php
