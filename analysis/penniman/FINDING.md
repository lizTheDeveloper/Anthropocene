# Counted, but not landed

### Who holds the ground this project has been measuring

*Analysis by the `penniman` lens. The analytical frame applied here is the one
developed in Leah Penniman's* Farming While Black: Soul Fire Farm's Practical
Guide to Liberation on the Land *(Chelsea Green, 2018) — a book that puts
practical ecological farming, land access, and racial justice in a single
argument rather than treating them as separate subjects. Everything numeric
below is computed from the USDA Census of Agriculture in this repository's
mirror. Nothing in this document is attributed to Penniman or to Soul Fire Farm
as an opinion, finding, or statement; the framework supplies the question, the
mirror supplies the answers. Where I have not verified a claim against a primary
source, I say so.*

---

## 1. The question, and why this framework makes it the right one

Every other analysis in this project takes the farm as a given object and
measures something on it: kilograms of glyphosate applied per county, earthworm
LC50s, soil organic carbon, mineral concentration in a carrot. The unit of
analysis is land. The unit of analysis is never **the person standing on it**.

The framework in *Farming While Black* refuses that separation. The book is
organised as a practical manual — soil building, crop planning, seed keeping,
livestock, marketing — but each of those chapters is written on the explicit
premise that the technical question ("how do you build soil?") is downstream of
a prior question ("do you have land, and can you keep it?"). Penniman's book
foregrounds land access, tenure, and the documented twentieth-century
dispossession of Black farmers alongside the agronomy, and it foregrounds the
erasure of Black and Afro-Indigenous agronomic contribution — the point being
that a body of practice and a body of people were separated from each other by
policy, not by agronomy.

That is not a rhetorical framing. It is an **empirically testable** one, and the
Census of Agriculture is the one federal source in this mirror that can test it.
The Census records, by county and by five-year cycle, the race, ethnicity, sex
and tenure of the people who operate farms, alongside the acreage they operate
and the sales they make. So this lens asks three questions the rest of the
project does not:

1. **Who holds the land?** Not "how many farmers are there of group X" — that is
   a head-count, and head-counts are the easiest number to move without moving
   anything. **Acres.**
2. **Has it changed?** Twenty years, five censuses.
3. **If this project's policy conclusion is "mandate or incentivise regenerative
   practice," who does that instrument actually touch?** Conservation programmes
   (EQIP, CSP) and any practice mandate are delivered through *operations* the
   Census counts, weighted by *acres* the Census measures. If land and
   programme-relevant scale are concentrated, the instrument is concentrated.

The literature this framework draws on is specific and real. Gilbert, Sharp and
Felin's review of the research on Black land loss (*Southern Rural Sociology*
18(2), 2002) and Pete Daniel's *Dispossession: Discrimination against African
American Farmers in the Age of Civil Rights* (UNC Press, 2013) document the
mechanism — discriminatory USDA credit and disaster administration, partition
sales of heirs' property, county committee gatekeeping — and the USDA's own
Civil Rights Action Team report (*Civil Rights at the United States Department of
Agriculture*, 1997) conceded much of it, as did the *Pigford v. Glickman*
consent decree (1999). Horst and Marion's "Racial, ethnic and gender inequities
in farmland ownership and farming in the U.S." (*Agriculture and Human Values*
36, 2019) is the most directly comparable quantitative treatment of Census
demographic data. On the "whose knowledge counts" half of the framework, the
strongest documented case is African Dark Earths: Solomon et al., "Indigenous
African soil enrichment as a climate-smart sustainable agriculture alternative"
(*Frontiers in Ecology and the Environment* 14(2), 2016), which characterises
anthropogenic carbon-enriched soils in Ghana and Liberia produced by indigenous
West African practice — the same family of practice that a 2020s soil-carbon
programme would now call novel.

**A caution I will keep.** The figure most often cited for the starting point —
roughly 925,000 Black-operated farms in 1920, about one in seven U.S. farms — is
**not in this mirror**. The bulk QuickStats census files here begin at 2002. I
have not verified the 1920 figure against a primary source and do not assert it
as my own computation; it appears here only as context attributed to the
secondary literature above. Everything I do assert is computed from files whose
SHA-256 is in `data/provenance.csv`.

---

## 2. What I did

**Source.** `data/raw/usda-nass/quickstats-bulk/2026-09-14/qs.census{2002,2007,
2012,2017,2022}.txt.gz` — USDA NASS Census of Agriculture bulk QuickStats,
tab-delimited, latin-1, gzipped.

**Extraction.** `analysis/penniman/compute.py` makes one streaming pass per
file. `VALUE` is parsed as a string: thousands separators stripped, and any
value beginning with `(` treated as a suppression code — `(D)` withheld to avoid
disclosing an individual operation, `(Z)`, `(NA)`, `(X)`, `(L)` — and never
coerced to zero.

**Series selected.** At `AGG_LEVEL_DESC = NATIONAL`, `DOMAIN_DESC = TOTAL`:

| years | subject prefix | measures |
|---|---|---|
| 2002, 2007, 2012 | `OPERATORS, <group>` | `NUMBER OF OPERATIONS`, `ACRES OPERATED`, `NUMBER OF OPERATORS` |
| 2017, 2022 | `PRODUCERS, <group>` | `NUMBER OF OPERATIONS`, `ACRES OPERATED`, `NUMBER OF PRODUCERS` |

Denominators are `FARM OPERATIONS - NUMBER OF OPERATIONS` and
`FARM OPERATIONS - ACRES OPERATED` from the same year and domain. The seven
groups are the seven NASS race/ethnicity categories. I deliberately used the
narrow race series, **not** the `ALONE OR COMBINED WITH OTHER RACES` variant
(which exists only from 2007 and is a broader concept), and excluded every
sub-cut (age, sex, tenure, decision-making, principal/second/third operator).

Cross-tabs also pulled, same pass: `TENURE`, `AREA OPERATED`, `ECONOMIC CLASS`,
and the `STATE` level. (In the `ECONOMIC CLASS` cross-tab the race series is
published as `OPERATIONS WITH RECEIPTS` — an operations basis, not a
head-count — which is what §3.4 uses.)

**Three things to hold onto about what these series mean.**

- *They are "at least one" concepts and they overlap.* A farm with one Black and
  one White producer is counted once in the Black row and once in the White row,
  with its full acreage in both. The groups **do not sum to the national total
  and must never be stacked.** In 2022 the six race rows sum to 897.1 M acres
  against a national 880.1 M — 1.9% over. Adding the Hispanic row (an ethnicity,
  overlapping every race row by construction) gives 934.0 M, 6.1% over.
- *There is a real definitional break at 2017.* 2002–2012 count "operators"
  (a principal operator plus up to two others). 2017–2022 count "producers" (up
  to four, all counted equally, with an explicit effort to enumerate spouses and
  other decision-makers). **This break inflates head-counts, not land.** White
  producer head-count rose 6.9% across 2012→2017 (3,035,413 → 3,244,344) while
  the number of White-operated *operations* fell 3.2% and acres fell 1.5%,
  tracking the national decline. This is exactly why the headline metric here is
  acres and operations, and why producer counts are carried in the CSV but not
  used to draw a trend line. I will not draw a clean line through 2017 for
  head-counts, and neither should anyone reading this.
- *"Acres operated" is not "acres owned."* It is land the operation farms,
  owned or rented. Tenure is handled separately in §3.3.

**Verification.** Three independent re-derivations, all in the script's output:
(a) summing the 50-state values back to the published national figure,
(b) summing the five mutually exclusive `AREA OPERATED` size classes back to the
published national operation count, and (c) summing the three tenure classes
back to the `TOTAL`-domain operations and acres. Results in §4.

**Outputs.**
- `data/derived/lens_penniman_land_access_by_race.csv` — **the chart data**;
  35 rows, 7 producer groups × 5 censuses.
- `data/derived/lens_penniman_scale_and_tenure_2022.csv` — long form: tenure ×
  group, size class × group, economic class × group, 2022 (§3.3, §3.4).
- `data/derived/lens_penniman_black_farmland_by_state_2022.csv` — state
  geography (§3.5).

The script also prints both verification tables and the §3.4 and §3.5 figures to
stdout, so every number in this document can be regenerated and checked by
running it.

---

## 3. The result

### 3.1 The gap is between being counted and holding land

2022 Census, national:

| producer group | operations | % of U.S. farms | acres operated | % of U.S. farmland | acres/farm | land share ÷ farm share |
|---|---:|---:|---:|---:|---:|---:|
| White | 1,829,449 | 96.26% | 823,942,903 | 93.62% | 450 | **0.97** |
| Hispanic (any race) | 83,505 | 4.39% | 36,866,263 | 4.19% | 441 | **0.95** |
| American Indian / Alaska Native | 40,621 | 2.14% | 55,781,477 | 6.34% | 1,373 | **2.97** |
| **Black or African American** | **28,723** | **1.51%** | **4,318,741** | **0.49%** | **150** | **0.33** |
| Multi-race | 24,990 | 1.32% | 9,661,430 | 1.10% | 387 | 0.84 |
| Asian | 16,072 | 0.85% | 2,608,401 | 0.30% | 162 | 0.35 |
| Native Hawaiian / Pacific Islander | 2,779 | 0.15% | 799,151 | 0.09% | 288 | 0.62 |
| *(all U.S. farms)* | *1,900,487* | *100%* | *880,100,848* | *100%* | *463* | *1.00* |

**Farms with at least one Black producer are 1.51% of American farms and hold
0.49% of American farmland.** The land share is 3.1 times smaller than the
farm-count share. The average such farm is 150 acres against a national average
of 463.

(Those are the same statement twice: the final column — land share ÷ farm share
— is algebraically identical to average farm size ÷ national average farm size.
`0.33 = 0.49/1.51 = 150/463`. The CSV emits both because a chart may want either
reading.)

This is the finding the brief anticipated, and it is worth being precise about
why it matters: **a group can be present in the count of farms and nearly absent
from the land.** Every headline that reports "the number of Black farmers rose"
is reporting the number that moves most easily and matters least for anything
measured in kilograms per hectare.

**The one reversal, reported honestly.** American Indian / Alaska Native
producers are the mirror image: 2.14% of operations, 6.34% of farmland, 1,373
acres per farm. That is not evidence of superior land security. 37% of those
acres (20.8 M of 55.8 M) are in Arizona alone, with New Mexico, Montana, Utah
and South Dakota next — arid reservation rangeland, much of it held in trust and
collectively operated, whose per-acre productive value is a small fraction of
Midwestern cropland. An acreage-share metric *by itself* would mislead badly
here, and I am flagging that rather than letting the number do rhetorical work
it cannot support.

**Hispanic producers** sit near parity in aggregate (4.39% / 4.19%) — but the
Census counts *producers*, not the roughly three-quarters-Hispanic hired crop
workforce, who appear in this dataset only as a labour expense line. Parity in
this table is not parity in the food system.

### 3.2 Twenty years does not close it

| census | Black-operated farms | % of U.S. farms | Black-operated acres | % of U.S. farmland | acres/farm | land ÷ farm share |
|---|---:|---:|---:|---:|---:|---:|
| 2002 | 30,605 | 1.44% | 3,836,339 | 0.409% | 125 | 0.28 |
| 2007 | 31,912 | 1.45% | 3,614,608 | 0.392% | 113 | 0.27 |
| 2012 | 34,758 | 1.65% | 4,208,972 | 0.460% | 121 | 0.28 |
| *2017* ‡ | 32,910 | 1.61% | 4,097,857 | 0.455% | 125 | 0.28 |
| *2022* ‡ | 28,723 | 1.51% | 4,318,741 | 0.491% | 150 | 0.33 |

‡ producer-concept years; see the definitional-break note in §2.

Two things are true at once and the framework is better served by saying both.

**Inconvenient for the framework:** the Black share of U.S. farmland did *not*
fall over these twenty years. It rose, 0.409% → 0.491%, a 20% relative increase.
Absolute acreage rose 12.6% (3.84 M → 4.32 M) while total U.S. farmland fell
6.2%. On this series, in this window, the land share is not deteriorating.

**Unchanged:** the *ratio* — land share divided by farm-count share — sat at
0.27–0.28 for fifteen years and moved to 0.33 only in 2022. Whatever the
mechanism, the structural position is the same one it was in 2002: present in
the count, near-absent from the land. And the 2012→2022 decade lost 6,035
Black-operated farms (−17.4%) against a national farm loss of −9.9% — the exits
ran roughly 1.8× the national rate, with the remaining operations somewhat
larger. The improving acreage share is partly a consolidation artefact, not
only an access gain.

### 3.3 The gap is scale, not tenure — and that is not what the history predicts

Given a history in which sharecropping and tenancy are the central mechanism,
the natural hypothesis is that Black-operated farms are disproportionately
tenanted. **In the 2022 data they are not.** 2022 national, by tenure:

| | full owner | part owner | tenant |
|---|---:|---:|---:|
| **share of operations** | | | |
| all U.S. farms | 71.4% | 22.3% | 6.3% |
| White | 71.9% | 22.5% | 5.6% |
| Black or African American | 69.8% | 22.2% | 8.1% |
| **acres per operation** | | | |
| all U.S. farms | 230 | 1,155 | 655 |
| White | 205 | 1,170 | 715 |
| **Black or African American** | **92** | **328** | **168** |

The tenure *mix* is nearly identical to the national mix. The difference is
entirely **scale inside each tenure class**. White-to-Black ratio of acres per
operation: full owner 2.2× (205 / 92), part owner 3.6× (1,170 / 328), tenant
4.3× (715 / 168). Same tenure, a third to a quarter of the land.

That matters mechanically. "Part owner" — own some land, rent more — is *the*
channel by which American farms scale up: nationally, part owners are 22% of
farms and operate 56% of the farmland, at five times the acreage of a full
owner. Black producers enter that channel at exactly the national rate (22.2%
of their operations vs. 22.3% nationally) and get much less out of it: moving
from full owner to part owner multiplies a Black-operated farm's acreage by 3.6×
(92 → 328) and a White-operated farm's by 5.7× (205 → 1,170). The rental market
is being entered at the same frequency and yielding about a third as much land.

### 3.4 What a practice instrument would actually reach

2022, national, operations by size and by sales:

| | Black-operated | all U.S. farms |
|---|---:|---:|
| farms of 1–9.9 acres | 15.5% | 12.3% |
| farms of 10–49.9 acres | 38.1% | 29.8% |
| farms of 50–179 acres | 31.0% | 27.9% |
| farms of 180–499 acres | 9.9% | 15.2% |
| **farms of 500+ acres** | **5.5%** | **14.7%** |
| farms with sales < $10,000 | 68.3% | 52.3% |
| **farms with sales ≥ $50,000** | **11.4%** | **26.9%** |

And the acreage those sales classes control, nationally: farms with **≥ $50,000
in sales are 26.9% of U.S. farms and operate 676.8 M acres — 76.9% of all U.S.
farmland.** Farms below $10,000 in sales are 52.3% of U.S. farms and operate
114.9 M acres, 13.1%.

So the arithmetic of reach, stated plainly:

- An instrument denominated **per acre** — practice cost-share, per-acre
  incentive, soil-carbon payment — reaches Black-operated land in proportion
  **0.49%**.
- An instrument denominated **per operation** — a flat enrolment payment, a
  technical-assistance visit, an outreach programme — reaches Black-operated
  farms in proportion **1.51%**, three times higher for the same total budget.
- An instrument with any effective **commercial-scale threshold** — explicit
  eligibility, a practice whose fixed costs only pencil above some acreage, or
  simply a cost-share that presumes working capital — sorts against 88.6% of
  Black-operated farms while still covering roughly three-quarters of American
  farmland.

(I have characterised EQIP and CSP above as per-acre/per-practice instruments
from general knowledge of their design. **Programme rules are not in this
mirror and I have not verified them here.** The arithmetic above does not depend
on any particular programme: it is a statement about what per-acre and
per-operation denominators do to this distribution.)

**The choice of denominator is itself a distributional decision**, and this
project has so far made it silently, by measuring everything in kilograms and
hectares. That is the concrete thing this lens contributes to the rest of the
analysis: a "mandate regenerative practices" recommendation that is not
explicitly specified per-operation, with a scale-neutral cost structure, is
specified per-acre by default, and per-acre in the United States means
overwhelmingly the operations that already hold the land.

### 3.5 Where it is

Black-operated farmland is regionally concentrated: the top ten states hold
about 82% of it. 2022:

| state | Black-operated acres | % of state farms | % of state farmland |
|---|---:|---:|---:|
| Texas | 855,704 | 3.14% | 0.68% |
| Mississippi | 741,466 | 13.78% | 7.23% |
| Alabama | 396,248 | 6.58% | 4.59% |
| Georgia | 323,899 | 4.44% | 3.26% |
| Arkansas | 267,082 | 2.43% | 1.95% |
| Louisiana | 226,135 | 7.60% | 2.83% |
| Oklahoma | 221,523 | 1.35% | 0.67% |
| North Carolina | 197,898 | 2.95% | 2.43% |
| South Carolina | 178,041 | 7.17% | 3.91% |
| Virginia | 148,733 | 2.77% | 2.03% |

Mississippi is the clearest single statement of the pattern in the whole
dataset: **13.8% of the state's farms, 7.2% of the state's farmland** — and
172 acres per farm against a Mississippi average of 328.

---

## 4. Verification

Three independent re-derivations of the headline quantities, all run inside
`compute.py` and printed to stdout.

**(a) State-sum vs. published national, 2022.** Summing all state values:

| | state sum | published national | difference |
|---|---:|---:|---:|
| Black-operated operations | 28,723 | 28,723 | **0.00%** |
| Black-operated acres | 4,293,953 | 4,318,741 | **−0.57%** |

The operations count reconciles exactly. Acres fall 0.57% short, which is the
expected signature of `(D)` suppression: a handful of states where Black-operated
acreage is small enough that publishing it would disclose an individual
operation. 0.57% is an order of magnitude smaller than any difference this
analysis rests on, and the same check on earlier censuses gives −0.06% (2002),
−0.40% (2007), −0.37% (2012) and −0.13% (2017) — the suppression loss is small
and does not trend. The top-10-state share is ~82% on either basis.

**(b) Size-class sum vs. published total operations, 2022.** The five mutually
exclusive `AREA OPERATED` classes sum to:

| | class sum | published total | difference |
|---|---:|---:|---:|
| Black-operated | 28,723 | 28,723 | 0.00% |
| all U.S. farms | 1,900,487 | 1,900,487 | 0.00% |

Exact. Independently, the eleven `ECONOMIC CLASS` acreage cells sum to exactly
880,100,848 — the published national farmland total — confirming the 76.9%
figure in §3.4 is computed on a closed partition, not a residual.

**(c) Tenure partition vs. the `TOTAL` domain, 2022.** The three tenure classes
are mutually exclusive and exhaustive, so they should reconstruct the totals in
§3.1 from an entirely different published cross-tab. They do, exactly:

| | full owner + part owner + tenant | published `TOTAL` | difference |
|---|---:|---:|---:|
| Black-operated operations | 28,723 | 28,723 | 0 |
| Black-operated acres | 4,318,741 | 4,318,741 | 0 |
| White-operated acres | 823,942,903 | 823,942,903 | 0 |
| all U.S. farmland | 880,100,848 | 880,100,848 | 0 |

So the headline 4,318,741 acres reconciles three independent ways: from the
`TOTAL` domain directly, from summing tenure classes, and (to within 0.57%
suppression) from summing the states.

I could not verify the pre-2002 historical baseline against any primary source
in this mirror, and have not asserted one.

---

## 5. Limitations

**Which of the four project landmines applies.** Landmine 4 — *joins across
mismatched sampling frames*. I have not joined the Census to PNSP, ECOTOX, NRI
or PDP, precisely because those frames do not match: PNSP is modelled county
pesticide use, the Census is a producer census, and a county-level correlation
between "share of farmland with a Black producer" and "kg of glyphosate per
county" would be a textbook ecological fallacy. Everything above is
within-Census. The §3.4 programme-reach argument is a **structural inference,
not a measurement**: I am arguing from who holds the acres and the scale to who
a per-acre instrument reaches, not from observed programme receipts.

Landmines 1–3 (dilution effect, method drift, SSURGO/NRI vintage) do not apply;
none of them touch the Census demographic series.

**What this cannot show.**

1. **Not ownership.** "Acres operated" includes rented land. The Census does
   publish owned vs. rented acreage by tenure class, but the race cross-tab is
   on acres *operated*. Heirs' property — the fractionated, clouded title that
   the literature identifies as a central mechanism of Black land loss — is
   invisible here by construction.
2. **Not programme receipts.** I searched the 2022 census file for a
   conservation-payment series crossed with producer race and did not find one.
   The Census can tell you who holds the land and at what scale; it cannot tell
   you who received an EQIP contract. That join would need USDA NRCS contract
   data, which is **not in this mirror**. Anyone wanting to convert §3.4 from
   inference to measurement needs it.
3. **The 2017 break is real and I have not "corrected" it.** Operations and
   acres are the least-affected series, which is why they carry the argument —
   but 2002–2012 "any of ≤3 operators" and 2017–2022 "any of ≤4 producers" are
   not the same concept, and the 2012→2017 movements in §3.2 should be read as
   approximately, not exactly, comparable.
4. **The race categories overlap and are self-reported**, and the "at least one
   producer of group X" construction attributes a farm's *entire* acreage to
   every group represented on it. For the Black series this inflates rather than
   deflates the land share, so the 0.49% is, if anything, an upper bound on
   land actually held by Black producers.
5. **Small denominators.** Native Hawaiian / Pacific Islander (2,779 operations)
   and county-level cells generally are suppression-prone; I kept the analysis
   at national and state level for that reason.
6. **Census acreage is self-reported and farms are self-defined** ($1,000 in
   sales, actual or potential). The very small end of the size distribution is
   the part of the Census with the widest known coverage uncertainty, and that
   is exactly where Black-operated farms are concentrated.

**What would falsify the central claim.** A showing that the 0.49% land share
is an artefact of non-response or coverage — i.e. that Black producers are
systematically under-enumerated on large operations. NASS's coverage-adjustment
methodology weights for non-response; testing that specific hypothesis would
need the census methodology documentation and the non-response adjustment
factors, which are not in this mirror.

---

## 6. What this changes for the rest of the project

One thing, because it is the only thing this lens needs the other analyses to
absorb: **the acre is not a neutral unit.** Every finding in this repository —
flat applied mass, glyphosate's 17× rise, 79% of mass without a soil-fauna
toxicity record, monitoring that tracks the market of 1992 — is denominated in
mass, hectares, or counties, and each of those denominators resolves, in the
United States, onto a population of operations 96.3% of which have a White
producer and which holds 93.6% of the land. That does not make any of those
findings wrong. It makes
the *recommendation* that follows from them a distributive instrument whose
incidence is already determined before anyone argues about it, and this is the
one dataset in the mirror that says so with numbers.

The cheapest concrete change: whenever this project proposes a practice
instrument, state its denominator. Per acre reaches 0.49% Black-operated land.
Per operation reaches 1.51% Black-operated farms. Those are not rounding
differences from each other, and the choice between them is currently being made
by default.

---

## References

1. Penniman, L. (2018). *Farming While Black: Soul Fire Farm's Practical Guide
   to Liberation on the Land.* Chelsea Green Publishing. — the framework applied
   here: land access, tenure and dispossession treated as prior to agronomy, and
   Afro-Indigenous agricultural knowledge treated as a documented tradition
   rather than folklore.
2. Gilbert, J., Sharp, G., & Felin, M. S. (2002). "The Loss and Persistence of
   Black-Owned Farms and Farmland: A Review of the Research Literature and Its
   Implications." *Southern Rural Sociology*, 18(2), 1–30.
3. Daniel, P. (2013). *Dispossession: Discrimination against African American
   Farmers in the Age of Civil Rights.* University of North Carolina Press.
4. Horst, M., & Marion, A. (2019). "Racial, ethnic and gender inequities in
   farmland ownership and farming in the U.S." *Agriculture and Human Values*,
   36, 1–16.
5. Solomon, D., Lehmann, J., Fraser, J. A., et al. (2016). "Indigenous African
   soil enrichment as a climate-smart sustainable agriculture alternative."
   *Frontiers in Ecology and the Environment*, 14(2), 71–76.
6. USDA Civil Rights Action Team (1997). *Civil Rights at the United States
   Department of Agriculture.* U.S. Department of Agriculture.
7. USDA National Agricultural Statistics Service. *Census of Agriculture*, 2002,
   2007, 2012, 2017, 2022 — bulk QuickStats release, mirrored in
   `data/raw/usda-nass/quickstats-bulk/2026-09-14/`, hashes in
   `data/provenance.csv`. **The source of every number above.**

*Reference 1 is cited for its analytical framework, not as a source of any
figure in this document. No statement, position or opinion in this analysis is
attributed to Leah Penniman or to Soul Fire Farm.*
