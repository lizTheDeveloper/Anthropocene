# The United States has a forty-year erosion panel and a one-day carbon record

**Lens:** the soil-organic-carbon / erosion / degraded-land-restoration framework
developed by Rattan Lal and colleagues at the Ohio State Carbon Management and
Sequestration Center.
**Slug:** `lal` · **Analyst role:** scientific anchor, not political frame.

> Attribution note, per the shared brief: this is *my* analysis applying *their
> published framework*. Nothing below is written in Rattan Lal's voice, no
> opinion is attributed to him, and no quotation is invented. The framework
> supplies the question and the standard of evidence; every number comes from
> the mirror in this repository.

---

## 1. The question, and why this framework makes it the right one

The project's organising thesis is that American agriculture is "strip-mining
the soil." Stated that way it is a claim about a **stock** and its **rate of
change**: soil organic carbon in cultivated topsoil, declining over time.

That is precisely the quantity the Lal literature is built around. Lal (2004,
*Science*) states the terms in its abstract: "The carbon sink capacity of the
world's agricultural and degraded soils is 50 to 66% of the historic carbon
loss of 42 to 78 gigatons of carbon," with a potential "to offset fossil fuel
emissions by 0.4 to 1.2 gigatons of carbon per year." Note what those are: a
*historic loss* and a *forward rate*. Both are statements about SOC change over
time, and the whole "maintain cover, minimise disturbance, return organic
matter, integrate trees" prescription follows from treating SOC as a measurable
stock with a measurable trajectory.

Two features of that framework make the erosion data in §3 directly relevant
rather than a substitute topic. First, **erosion is a line item in the carbon
accounting itself.** Table 1 of the same paper decomposes postindustrial
soil carbon loss of 78 ± 12 Gt into 26 ± 9 Gt from erosion and 52 ± 8 Gt from
mineralization — roughly a third of the loss attributed to soil moving. Second,
the US-specific version of the claim exists: Lal, Follett, Kimble & Cole (1999)
estimate that "U.S. cropland has lost about 5000 MMTC as a result of
cultivation" (5 Pg C) and put the sequestration potential at 75–208 MMT C/yr.
Those are exactly the magnitudes a "strip-mining" thesis would want to invoke,
and exactly the magnitudes the federal record must be asked to support.

The same literature is where the hard critiques live — sequestration-potential
estimates that vary by a factor of several (Schlesinger & Amundson 2019;
Poulton et al. 2018), SOC saturation (Six et al. 2002), sampling-depth and
stratification artifacts in claimed no-till gains (Powlson et al. 2014), and,
the one that matters most here, the statistical difficulty of *detecting* a
change in SOC stock at all against high spatial variability (Smith 2004). An
honest application of this framework has to carry the critiques with it, and
they all point at the same requirement: **measurement, repeated.**

And the framework must be applied at a stated vintage, because its own central
estimates have moved a great deal. Lal (2018, *Global Change Biology*) revises
the historic depletion figure from 78 ± 12 Pg to 115–154 (mean 135) Pg C, and
the global technical potential from the 2004 paper's 0.4–1.2 Gt C/yr to
1.45–3.44 (mean 2.45) Pg C/yr — roughly a threefold escalation in fourteen
years. The 2004 *Science* paper is not even internally consistent on the
historic loss: 42–78 Gt in the abstract, "55 to 78 Gt" in the body, and "44 to
537 Gt" quoted as the range in the literature. I am not raising this to score a
point. It is the strongest possible argument for the position this analysis
ends up at: when the estimates move by a factor of three and disagree with
themselves inside one paper, **the binding constraint on the field is
measurement, not modelling** — which is precisely what the US federal record
turns out to lack.

Applying that framework honestly means asking the question in the direction
that can embarrass the thesis:

> **Does the US federal record contain the measurements needed to state a rate
> of soil carbon change on American cropland — and if not, exactly which
> measurement is missing?**

I checked downward. The answer is no, and the gap is specific and nameable.
This is the most attackable claim in the project, and the cheapest place to
lose an argument; establishing its limits is worth more than a chart that
overstates it.

## 2. What I did

### Sources (all from the local mirror)

| file | used for |
|---|---|
| `data/raw/usda-nrcs/nri/2026-09-14/reports/2022_NRI_Summary_Report.pdf` | Tables 10, 15, 16, 17, 18 — the national erosion panel |
| `data/raw/usda-nrcs/nri/2026-09-14/reports/2017NRISummary_Final.pdf` | Table 14 — **landmine demonstration only**, never mixed into a reported number |
| `data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf` | Tables 2 and 8, and the method narrative |

The NRI erosion tables are published only inside the PDF; NRCS offers no CSV.
`analysis/lal/compute.py` extracts them with `pdftotext -layout` and parses the
fixed-width columns, then writes
`data/derived/lens_lal_soil_measurement_record.csv`.

### Filters and definitions

- **Land use.** "Cultivated cropland" is the NRI class; the CSV also carries
  "Total cropland" (cultivated + non-cultivated) for the reader who wants the
  broader base. Headline numbers below are cultivated cropland.
- **Erosion.** Sheet-and-rill (water) from Table 15, wind from Table 16, both as
  national "Total" rows, tons per acre per year. "Combined" is their sum.
- **T** is the NRI soil-loss tolerance factor, defined in the report's own
  glossary as "the maximum rate of annual soil loss that will permit crop
  productivity to be sustained economically and indefinitely on a given soil."
  Tables 17 and 18 report acres by erosion-to-T ratio class. "Above T" is
  `Total − (≤T)`.
- **Release discipline.** Every value, 1982 through 2022, is taken from the 2022
  release only. See §5.

### Verification — the numbers were recomputed before they were written down

`compute.py` refuses to write the CSV unless all of the following pass. They do.

1. **Three independent tables must agree on cropland acreage.** Table 10
   (Chapter 4) versus Tables 17 and 18 (Chapter 5). Cultivated cropland agrees
   to the digit in all nine years. The largest disagreement anywhere is 2.6
   thousand acres in non-cultivated cropland in 2002 — 0.005% — which is the
   report's own editing residue, not a parse error.
2. **The national rate, recomputed a second way.** Tables 15/16 publish the
   cultivated, non-cultivated *and* total-cropland rates independently. The
   total must be the acreage-weighted mean of the two components, with acreage
   taken from a different chapter's tables. It is, in all nine years and both
   erosion types, to within 0.0052 t/ac/yr — inside the 0.01 rounding of the
   published rates. This tests the rate parse and the acreage parse
   simultaneously; a column mis-parse would be off by orders of magnitude.
3. **The report's own narrative.** Chapter 2 states water erosion fell 3.89 →
   2.67 and wind 3.24 → 2.08 t/ac/yr on cropland. The parsed Table 15/16 totals
   are exactly those numbers.
4. **The T-class columns sum to the published Total** in all 89 parsed rows of
   Tables 17 and 18, to 0.00 thousand acres.
5. **Textual absence check** (see §3.3).

A small honest discrepancy surfaced: the narrative says cropland erosion
"decreased 34 percent between 1982 and 2022," but recomputing from the two
rates it cites in the same sentence gives 7.13 → 4.75 t/ac/yr, **−33.4%**. The
difference is consistent with rounding of the published 0.01-resolution rates.
I report 33.4% and note the narrative's 34%.

## 3. The result

### 3.1 The erosion panel is real, long, and it stopped improving in 1997

National average annual erosion on US cultivated cropland, 2022 NRI release:

| year | water | wind | combined | combined (Mg/ha/yr) |
|---|---|---|---|---|
| 1982 | 4.27 | 3.56 | **7.83** | 17.55 |
| 1987 | 3.90 | 3.51 | 7.41 | 16.61 |
| 1992 | 3.36 | 2.98 | 6.34 | 14.21 |
| 1997 | 3.02 | 2.59 | **5.61** | 12.58 |
| 2002 | 3.09 | 2.37 | 5.46 | 12.24 |
| 2007 | 2.93 | 2.33 | 5.26 | 11.79 |
| 2012 | 2.96 | 2.27 | 5.23 | 11.72 |
| 2017 | 2.99 | 2.31 | 5.30 | 11.88 |
| 2022 | 3.01 | 2.33 | **5.34** | 11.97 |

*(tons/acre/year unless noted)*

- Over the full 40 years: **−31.8%**. A real achievement, and the conservation
  policy of the 1985 and 1990 Farm Bills is the obvious candidate cause.
- **89% of that entire decline was already achieved by 1997.**
- 1997 → 2022, twenty-five years: **−4.8%**.
- Sheet-and-rill erosion has *risen* since 2007: 2.93 → 3.01 t/ac/yr, **+2.7%**.
  The 2022 figure lies outside the report's stated margin of error on the 2007
  figure (3.01 ± 0.03 against 2.93 ± 0.04).

The report's own headline — "decreased 34 percent between 1982 and 2022" — is
true and, read as a statement about the present, misleading. Nothing has
improved nationally in a quarter of a century.

### 3.2 On the degradation claim's own terms, the exceedance is large and no longer falling

Acres of cultivated cropland eroding **above T**, the rate NRCS itself defines
as the limit of sustainability:

| year | above T (water) | share | above T (wind) | share | above **5T** (water) |
|---|---|---|---|---|---|
| 1982 | 95.5 M ac | 25.4% | 80.4 M ac | 21.4% | 12.5 M ac |
| 1997 | 59.9 M ac | 18.4% | 52.5 M ac | 16.1% | 4.2 M ac |
| 2007 | 52.9 M ac | 17.3% | 46.3 M ac | 15.2% | 4.0 M ac |
| **2022** | **56.5 M ac** | **18.0%** | **45.6 M ac** | **14.6%** | **4.6 M ac** |

- In 2022, **56.5 million acres — 18.0% of US cultivated cropland — were still
  losing soil to water faster than NRCS says is sustainable.**
- That is **3.6 million acres more than in 2007** (+0.69 pp). The share has
  risen at every reading since 2007.
- Acres eroding above **five times** T rose from 4.00 to 4.61 million,
  **+15.2%**, over the same period.
- Wind exceedance has continued to fall slightly, 46.3 → 45.6 M ac.

**These two columns must not be added.** Tables 17 and 18 are marginal
distributions over the same land base; the report publishes no joint
distribution, so the number of acres above T on *either* process is unknown and
lies somewhere between 56.5 M and 102.2 M acres.

One further comparison, and it cuts against complacency. The 2022 national
combined rate on cultivated cropland is 5.34 t/ac/yr = **11.97 Mg/ha/yr** — just
under the value Lal (2015) identifies as the conventional tolerance limit while
arguing it is too permissive: "Soil erosion must be curtailed to within the
tolerable limits, **which is often much less than the presumed value of 12.5
Mg/ha per year**." So the US national average sits fractionally below a
threshold this framework regards as already too generous, and 18.0% of the
acreage sits above NRCS's own, stricter, soil-specific T. I report this as a
comparison of published benchmarks, not as a finding: it depends entirely on
whose threshold you accept, which is the point.

### 3.3 Against that: the carbon record is one day long

- **The 2022 NRI Summary Report is 222 pages covering nine measurement years
  and does not contain the word "carbon" once.** Not "soil carbon," not
  "organic carbon," not "organic matter." Zero occurrences, verified
  programmatically over the full extracted text. The flagship federal
  natural-resources inventory of US non-federal land does not measure the
  quantity the degradation thesis is about.
- The only national measurement of soil organic carbon stocks the United States
  has ever made is the **Rapid Carbon Assessment (RaCA)**. Its own methodology
  report opens by saying it was designed "to capture information on the carbon
  content of soils across the conterminous United States (CONUS) **at a single
  point in time**."
- RaCA Table 2: **6,418 sites**, of which **1,263 were cropland**. Five pedons
  per site, but only the **central** pedon went to the Kellogg Soil Survey
  Laboratory for measured carbon — the other four are VNIR-predicted, and the
  report states plainly why the lab subset was expanded: "After initial results
  indicated inadequate accuracy and noticeable bias, all central pedon samples
  were sent to KSSL for analysis."
- So the measured national cropland carbon record is roughly **1,263
  laboratory-measured pedons**, once. Against 313.2 million acres of cultivated
  cropland in 2022, that is **one measured soil profile per ~248,000 acres**
  (~1,000 km²).
- RaCA's cropland SOC stock to 100 cm is **106.1 Mg C/ha** (Table 8,
  LUGR-weighted), against 141.8 for forestland and 65.8 for rangeland.

**Number of repeat measurements: zero. Number of computable rates of change:
zero.**

**An important correction to the obvious reading of this.** "One pedon per
248,000 acres" sounds like the problem is that RaCA was too small. On the
published evidence it probably was not. Conant & Paustian (2002) estimate that
verifying soil C change at the **national** scale requires on the order of
**501 samples** (α = 0.1, after 5 years); NASEM (2019) recommends a national
network of **5,000–7,000** points across all cropland and grassland. RaCA's
1,263 lab-measured cropland pedons are in the right order of magnitude for a
national-scale design. **The binding constraint is not n. It is that there is
no second visit.** No increase in sample size at one date can produce a rate of
change. This matters for how the project frames the gap: the criticism to make
of the federal record is not that it sampled too thinly, but that it sampled
once.

### 3.4 The finding

The contrast is the finding. On erosion, the federal government has nine
national estimates spanning forty years, with margins of error, back-updated
for methodological consistency, broken out by land use and by exceedance of a
sustainability threshold. On soil carbon — the variable the "strip-mining"
thesis is actually about — it has one snapshot, taken around 2010, explicitly
framed by its own authors as a single point in time.

**A quantitative claim about soil carbon change on American cropland cannot be
made from the US federal record.** Not "is not well supported." Cannot be made:
a rate requires two measurements and the federal record contains one.

What the federal record *does* support is a claim about **soil loss**: that
18.0% of cultivated cropland exceeds the government's own sustainability
threshold for water erosion, that this share has been rising since 2007, and
that national erosion rates have not improved since 1997. That claim is
defensible, quantified, and sourced to nine measurement years. It is a weaker
claim than "strip-mining the soil" and it is the one the data will carry.

## 4. What it would take — and the fact that USDA has now started

The missing measurement is precise and nameable: **repeat sampling of the same
locations, with bulk density and laboratory-measured SOC to a fixed depth, on a
probability sample of US cropland, at an interval long enough for the signal to
exceed spatial noise.**

That is not my specification. It is the National Academies', and it comes with
a design and a price. NASEM (2019), *Negative Emissions Technologies and
Reliable Sequestration*, p. 129:

> "**A National On-Farm Soil Monitoring System.** USDA should fully implement a
> national on-farm soil monitoring system on existing National Resource
> Inventory (NRI) points on cropland and grassland. Full buildout to
> approximately **5,000-7,000 NRI locations** with soil sampling and analysis
> carried out at **intervals of 5-7 year** (on an annual rotating basis similar
> to the FIA system) is recommended. **Similar systems already exist in many
> countries, including in the European Union, Australia, New Zealand, and
> China** … The **cost for this system is $5M/y** as an augmentation of USDA's
> existing NRI system."

Read that carefully. A National Academies panel recommending in 2019 that the
United States "fully implement" a system that "already exist[s]" in the EU,
Australia, New Zealand and China is, in effect, the published statement that
the United States did not have one — and it prices the gap at **$5 million a
year**. (I searched for a statement by Rattan Lal specifically asserting the
absence of such a US network and did not find one; I therefore do not attribute
this point to him. NASEM 2019 and RaCA's own "single point in time" sentence
carry it without needing to.)

And on the interval: Smith (2004) is the reason "repeat" is not enough on its
own. Its abstract reports that where carbon inputs rise 20–25%, SOC change
"could be detected with 90% confidence after about 6–10 years" only under a
sampling regime resolving a 3% change in background SOC — "probably requiring a
very large number of samples" — and "could not be detected at all" under a
regime resolving only 15%. "If increases in C inputs are much below 15%, it
might not be possible to detect a change in soil C without an enormous number
of samples." A monitoring network therefore needs a stated minimum detectable
change as well as a stated revisit interval, or it can run for decades and
report nothing.

USDA began exactly this in 2024. The NRCS **Soil Carbon Monitoring Network
(SCMN)** was established to support Sec. 21002(a)(2) of the Inflation Reduction
Act. Per the NRCS programme page (retrieved 2026-09-14):

> "Data collection started in fiscal year 2024, with plans to expand in fiscal
> year 2025 and should be fully implemented on the remaining sites between
> fiscal years 2026 and 2030. The SCMN team plans to revisit sites on a 5- to
> 10-year recurring basis to monitor soil change over time. **Resampling of
> sites is planned to begin in fiscal year 2030.**"

Two things follow, and they cut in opposite directions for the project.

1. **The frame was never the obstacle.** SCMN samples at established NRI
   locations ("Triangles"), exactly as RaCA drew its sites from the NRI frame.
   The probability sample that would have made a soil-carbon time series
   possible has existed since 1982. What was missing was the decision to go
   back.
2. **The first federal repeat-measurement soil carbon data in US history does
   not exist yet, and is not scheduled to exist before FY2030.** A defensible
   national *rate* of change, which needs the second visit plus analysis, is
   later still. Anything written today about the trajectory of American
   cropland SOC from federal sources is inference from a single point.

That page also carries a notice dated 5/20/2025 stating the site "is under
review and content may change," so the schedule above should be treated as the
agency's stated plan, not as a commitment. And the plan is explicitly national,
not local: NRCS states that "the sampling design is not structured to capture
statistical difference on individual farms." SCMN will not settle any argument
about a particular field or a particular practice on a particular farm, which
is what most soil-carbon controversy is actually about.

**Acquisition recommendation for the parent:** SCMN is not in this mirror. It
should be — both the programme page and `SCMN Field Sampling Instructions.pdf`
(2025-01). Like the rest of NRCS it refuses curl and python-requests but serves
`wget` normally, so `fetchlib.fetch_via_wget` will reach it.

## 5. Limitations — read these before quoting anything above

**Which of the four landmines applies: #3, squarely. And #4, partly.**

**(a) NRI back-updates its own history, and I can show it.** `compute.py` prints
a demonstration built from both releases in the mirror. The national
sheet-and-rill rate for cultivated cropland, as published in the 2017 release
versus the 2022 release:

| year | 2017 release | 2022 release | revision |
|---|---|---|---|
| 1982 | 4.26 | 4.27 | +0.01 |
| 1987 | 3.89 | 3.90 | +0.01 |
| 1992 | 3.35 | 3.36 | +0.01 |
| 1997 | 3.02 | 3.02 | 0.00 |
| 2002 | 3.09 | 3.09 | 0.00 |
| 2007 | **2.90** | **2.93** | **+0.03** |
| 2012 | 2.96 | 2.96 | 0.00 |
| 2017 | 2.99 | 2.99 | 0.00 |

Four of eight already-published years were restated. This matters *exactly
where my finding is*: the +2.7% rise since 2007 becomes +3.8% if you take the
2007 value from the 2017 release — a 1.1 pp inflation on a 2.7 pp signal.
Every number in §3 uses the 2022 release throughout. Anyone reproducing this
must do the same.

**(b) NRI erosion is modelled, not measured.** Sheet-and-rill comes from USLE
and wind from WEQ, driven by field-observed inputs at NRI sample points. These
are long-term average-annual *predictions* under the observed conditions, not
weighed sediment. A change in the estimate can in principle reflect a change in
model inputs or in how a practice is recorded rather than a change in soil
moving. The stated margins of error are sampling errors on the NRI point
sample; they do not include model error, which is not quantified in the report.
This is the single largest caveat on §3.1 and §3.2.

**(c) The T threshold is a convention, not a measurement.** T is an NRCS soil
interpretation carried on the soil survey; the 2022 report defines it but
publishes no values or range. It is a defensible policy benchmark and it is the
government's own, which is why §3.2 is stated on its terms — but "above T" is
not a measured biophysical fact. The underlying soil survey is also not static:
the 2025 Annual Soils Refresh in this mirror records 41,974,803 acres of new
soil data, 20,321 new soil components and 75,702 new soil horizons added in a
single October. NRI's practice of back-updating its own history is how changes
of that kind get absorbed into restated prior years — which is the reason
release discipline (§5a) is not a formality.

**(d) Wind and water exceedance cannot be combined.** Stated in §3.2; repeated
here because it is the easiest error to make with these tables.

**(e) RaCA's land-use contrast is space-for-time and I have not used it as a
change estimate.** Cropland 106.1 versus forestland 141.8 Mg C/ha is a real
difference in the RaCA snapshot, but cropland and forest occupy
systematically different soils, slopes and climates — cropland is
preferentially on the better land. Reading that 35.7 Mg/ha gap as
cultivation-induced loss would be exactly the kind of unearned inference this
analysis exists to prevent. RaCA is reported here as a baseline, which is what
its authors called it.

**(f) I have not attempted to convert erosion into carbon loss, deliberately —
and this is the most important restraint in the analysis.** It is the obvious
next step and it is a trap. The sign of the erosion–carbon term is contested in
the primary literature across a two-petagram range. Van Oost et al. (2007) open
by noting that estimates "range from a source of 1 petagram per year to a sink
of the same magnitude," and conclude from caesium-137 and carbon inventories
that agricultural erosion is a **sink** of 0.12 (0.06–0.27) Pg C/yr. Lal (2003)
reaches the opposite sign, estimating erosion-induced **emission** of 0.8–1.2
Pg C/yr. The disagreement ran to a published Comment and reply in *Science*
(2008, 319(5866): 1040).

Look at how Lal (2003) gets there, because it shows exactly what is missing:
"assuming a delivery ratio of 10% and SOC content of 2–3%" the displaced carbon
is 4.0–6.0 Pg/yr, and "with 20% emission due to mineralization" the flux is
0.8–1.2 Pg C/yr. Three parameters do all the work — a delivery ratio, an SOC
concentration of the eroded sediment, and a mineralised fraction. **The federal
mirror supplies none of the three.** There is no measured SOC concentration for
eroded sediment, no enrichment ratio, and no depositional-site measurement
anywhere in the NRI or RaCA.

And the tempting shortcut — multiply eroded tonnage by RaCA's bulk SOC
concentration — is wrong on the framework's own terms, because erosion is
selective. Lal (2015): "the enrichment ratio of SOC, clay and essential plant
nutrients (N, P, S) is **>1 (and most often as much as 5 or more)** because of
the preferential removal of these constituents." An unknown multiplier with a
plausible range of 1 to 5 sits between the NRI tonnage and any carbon figure,
before the delivery ratio and mineralised fraction are even reached. Any "tons
of soil × percent carbon = carbon lost" arithmetic built on §3.1 would be a
number with no error bar and an indeterminate sign, and I have not produced
one.

**(g) RaCA pedon-level data is not in this mirror.** Only the methodology and
summary report are held (`plans/step-04-soil.md` lists the pedon data as not yet
acquired). I therefore could not compute the spatial variance of cropland SOC
and so could not compute a minimum detectable change from the mirror itself.
The statement in §3.3 is about the *number and timing* of measurements, which
the summary report establishes directly, not about their variance.

**(h) RaCA's exact field seasons are not stated in the mirrored report body.**
RaCA is universally cited as 2010–2011, and the corroborating evidence in this
mirror is consistent with that — the Field Collection Protocols are dated June
2010, the sampling population was defined from an October 2010 Soil Data Mart
snapshot, and SSURGO coverage is taken as of January 2012 — but I did not find a
sentence in the methodology report giving the field seasons, so I write "around
2010" rather than asserting the range. Nothing in the finding depends on the
exact dates; what matters is that there is one of them. The frequently cited
totals of 6,148 sites / 32,084 pedons / 144,833 samples come from Wills et al.
(2014), not from the mirrored report; **summing Table 2 of the report itself
gives 6,418 sites**, which is the number I use.

**(i) Provenance gap — flagging for the parent.** The 2022 NRI Summary Report
is the load-bearing file in this analysis, and its actual SHA-256
(`5aa1b976a225772166322b2f0f392648f8061222d5ddad277ce2ac4ef322c58c`,
12,666,474 bytes, 222 pages) appears in **neither** `data/provenance.csv` nor
`data/manifests/nri.sha256`. Both record only the truncated 5,242,880-byte
Internet Archive copy that `plans/step-04-soil.md` says was discarded and
replaced by the complete direct-from-agency fetch. The file on disk is complete
(trailing `%%EOF` present, 222 pages, all tables render), but it is currently
unattested. `compute.py` pins the hash and fails closed if it changes; the
provenance row should be corrected.

## 6. References

These are the published works whose framework structures the question above.
**Every DOI below was resolved against Crossref and every title, author list,
journal, volume and page range confirmed**; quoted figures were taken from the
publishers' or PubMed's abstracts, not from memory. Where I could not verify a
specific figure against the source, I say so rather than assert it.

- **Lal, R. (2004).** "Soil carbon sequestration impacts on global climate
  change and food security." *Science* 304(5677): 1623–1627.
  DOI: 10.1126/science.1097396. The reference statement of the framework.
  Verified from the abstract: historic carbon loss of 42–78 Gt C, sink capacity
  50–66% of it, offset potential 0.4–1.2 Gt C/yr (5–15% of global fossil-fuel
  emissions), and yield response of 20–40 kg/ha (wheat), 10–20 (maize),
  0.5–1 (cowpeas) per tonne of SOC restored on degraded cropland.
- **Lal, R. (2003).** "Soil erosion and the global carbon budget."
  *Environment International* 29(4): 437–450.
  DOI: 10.1016/S0160-4120(02)00192-7. The argument that erosion is a carbon
  process and not only a productivity one — the reason §3.1 and §3.3 belong in
  the same analysis. Verified from the abstract: displaced C of 4.0–6.0 Pg/yr
  "assuming a delivery ratio of 10% and SOC content of 2–3%", and
  erosion-induced emission of 0.8–1.2 Pg C/yr at 20% mineralisation. Contested;
  see Van Oost et al.
- **Lal, R. (2015).** "Restoring Soil Quality to Mitigate Soil Degradation."
  *Sustainability* 7(5): 5875–5895. DOI: 10.3390/su7055875. Degraded-soil
  restoration framing and the link from soil loss to food security. Citation
  verified; I did not verify individual figures inside it and quote none.
- **Van Oost, K., Quine, T.A., Govers, G., De Gryze, S., Six, J., Harden, J.W.,
  et al. (2007).** "The Impact of Agricultural Soil Erosion on the Global Carbon
  Cycle." *Science* 318(5850): 626–629. DOI: 10.1126/science.1145724. The
  principal counter-argument. Verified from the abstract: estimates "range from
  a source of 1 petagram per year to a sink of the same magnitude"; their own
  estimate is an erosion-induced **sink** of 0.12 (0.06–0.27) Pg C/yr. The
  exchange that followed is itself the evidence that the field did not settle
  it: **Lal, R. & Pimentel, D. (2008),** "Soil erosion: a carbon sink or
  source?" *Science* 319(5866): 1040–1042, DOI 10.1126/science.319.5866.1040
  (technical comment, with author reply on the same pages), and **Harden, J.W.,
  Berhe, A.A., Torn, M., Harte, J., Liu, S. & Stallard, R.F. (2008),** "Soil
  erosion: data say C sink." *Science* 320(5873): 178–179,
  DOI 10.1126/science.320.5873.178.
- **Smith, P. (2004).** "How long before a change in soil organic carbon can be
  detected?" *Global Change Biology* 10(11): 1878–1883.
  DOI: 10.1111/j.1365-2486.2004.00854.x. The detectability problem, and the
  reason §4 is framed as an interval *and* a minimum detectable change rather
  than just a second visit. Figures quoted in §4 are verbatim from the
  abstract. **Caveat: the article body, tables and figures are behind a
  paywall and were not retrieved; I quote nothing beyond the abstract.** In
  particular, the widely repeated claim that this paper shows "up to 15 years
  for cropland" is *not* in the abstract and I could not source it — the
  abstract instead describes the relationships as "robust over a range of soil
  types and land uses." I do not repeat that claim anywhere.
- **Conant, R.T. & Paustian, K. (2002).** "Spatial variability of soil organic
  carbon in grasslands: implications for detecting change at different scales."
  *Environmental Pollution* 116(Suppl. 1): S127–S135.
  DOI: 10.1016/S0269-7491(01)00265-2. Source of the national-scale sample-size
  benchmark used in §3.3 to argue *against* the reading that RaCA was simply
  too small: verifying change (α = 0.1) after 5 years needs on the order of
  "34, 224, 501 samples at the county, state, or national scales."
- **National Academies of Sciences, Engineering, and Medicine (2019).**
  *Negative Emissions Technologies and Reliable Sequestration: A Research
  Agenda.* Washington, DC: The National Academies Press.
  DOI: 10.17226/25259. Chapter 3, p. 129 — the specification and the $5M/yr
  price of the monitoring system §4 says is missing, quoted verbatim.
- **Lal, R. (2018).** "Digging deeper: A holistic perspective of factors
  affecting soil organic carbon sequestration in agroecosystems." *Global
  Change Biology* 24(8): 3285–3301. DOI: 10.1111/gcb.14054. The later vintage
  of the framework's central estimates (historic depletion 115–154, mean 135
  Pg C; potential 1.45–3.44, mean 2.45 Pg C/yr), cited in §1 to show how far
  they have moved.
- **Lal, R., Follett, R.F., Kimble, J. & Cole, C.V. (1999).** "Managing U.S.
  cropland to sequester carbon in soil." *Journal of Soil and Water
  Conservation* 54(1): 374–381. The US-specific statement of the claim: "U.S.
  cropland has lost about 5000 MMTC as a result of cultivation," with a
  sequestration potential of 75–208 MMT C/yr. (A companion book,
  *The Potential of U.S. Cropland to Sequester Carbon and Mitigate the
  Greenhouse Effect*, is in circulation under both 1998 and 1999 imprints and
  two publishers; I could not resolve which is correct, so I cite the journal
  article, which reproduces its numbers.)
- **Schlesinger, W.H. & Amundson, R. (2019).** "Managing for soil carbon
  sequestration: Let's get realistic." *Global Change Biology* 25(2): 386–389
  (published online 2018). DOI: 10.1111/gcb.14478. The main published downward
  correction on sequestration-potential claims.
- **Baveye, P.C., Berthelin, J., Tessier, D. & Lemaire, G. (2018).** "The '4 per
  1000' initiative: A credibility issue for the soil science community?"
  *Geoderma* 309: 118–123. DOI: 10.1016/j.geoderma.2017.05.005. A Letter to the
  Editor arguing that headline sequestration targets rest on
  "back-of-the-envelope calculations." **Caveat: closed access with no open
  copy available anywhere; its argument is known to me only through quotations
  reproduced in the published rejoinder (Minasny et al. 2018, *Geoderma* 309:
  124–129, DOI 10.1016/j.geoderma.2017.05.026). It advances a credibility
  argument rather than a quantitative one, and I attribute no number to it.**
- **Poulton, P., Johnston, J., Macdonald, A., White, R. & Powlson, D. (2018).**
  "Major limitations to achieving '4 per 1000' increases in soil organic carbon
  stock in temperate regions: Evidence from long-term experiments at Rothamsted
  Research, United Kingdom." *Global Change Biology* 24(6): 2563–2584.
  DOI: 10.1111/gcb.14066. The *empirical* version of the above — 16 long-term
  experiments, 114 treatment comparisons over 7–157 years — and the better
  citation when a quantitative feasibility critique is wanted.
- **Powlson, D.S., Stirling, C.M., Jat, M.L., Gerard, B.G., Palm, C.A.,
  Sanchez, P.A., et al. (2014).** "Limited potential of no-till agriculture for
  climate change mitigation." *Nature Climate Change* 4(8): 678–683.
  DOI: 10.1038/nclimate2292. Sampling-depth and stratification artifacts in
  claimed no-till SOC gains — a caution that will apply to SCMN analyses as
  much as to this one.
- **Six, J., Conant, R.T., Paul, E.A. & Paustian, K. (2002).** "Stabilization
  mechanisms of soil organic matter: Implications for C-saturation of soils."
  *Plant and Soil* 241(2): 155–176. DOI: 10.1023/A:1016125726789. SOC
  saturation: why sequestration rates are not indefinitely sustainable.

Federal sources:

- **USDA-NRCS (2026).** *2022 National Resources Inventory Summary Report.*
  Tables 10, 15, 16, 17, 18. Local mirror; see §5(i) on provenance.
- **Soil Survey Staff and T. Loecke (2016).** *Rapid Carbon Assessment:
  Methodology, Sampling, and Summary.* S. Wills (ed.). USDA-NRCS. Tables 2 and
  8. (This is the citation the report gives for itself.)
- **USDA-NRCS.** *Soil Carbon Monitoring and Research Network.* Programme page
  and *SCMN Field Sampling Instructions* (2025-01). Retrieved 2026-09-14; not
  yet in the mirror.

## 7. Files produced

| file | what it is |
|---|---|
| `analysis/lal/FINDING.md` | this document |
| `analysis/lal/chart.json` | spec for the single visualization |
| `analysis/lal/compute.py` | runnable from repo root; extracts, verifies, writes the CSV |
| `data/derived/lens_lal_soil_measurement_record.csv` | 18 rows: 9 NRI years × {cultivated cropland, total cropland} |

Nothing has been committed to git.
