# Water Quality Portal — censoring and comparability

Audit of the 15 compound result sets retrieved 2026-09-14. Three properties of
this data decide whether a water analysis survives review. All three are easy to
get wrong in a way that produces a confidently stated, wrong answer.

## 1. Most rows are non-detects, and they carry no numeric value

| Compound | Rows | Numeric | Non-detect flagged | Sites |
|---|---:|---:|---:|---:|
| Atrazine | 304,030 | 177,617 | 132,896 | 41,917 |
| Simazine | 240,621 | 103,161 | 160,921 | 32,509 |
| Alachlor | 239,129 | 71,458 | 197,662 | 32,893 |
| Acetochlor | 238,070 | 94,159 | 163,883 | 31,359 |
| Metolachlor | 279,116 | 145,429 | 144,739 | 37,515 |
| Chlorpyrifos | 170,596 | 16,653 | 140,436 | 31,832 |
| Trifluralin | 146,543 | 19,217 | 113,628 | 27,201 |
| Pendimethalin | 144,160 | 14,650 | 118,948 | 28,365 |
| 2,4-D | 109,445 | 41,215 | 60,613 | 23,830 |
| Dicamba | 80,927 | 8,953 | 65,455 | 17,850 |
| Chlorothalonil | 60,399 | 5,757 | 43,524 | 10,956 |
| **Glyphosate** | **59,538** | **34,452** | **32,139** | **7,305** |
| Acephate | 31,309 | 4,308 | 21,889 | 4,675 |
| Glufosinate | 15,312 | 267 | 15,045 | 2,353 |
| **Paraquat** | **142** | **102** | **40** | **41** |

Chlorpyrifos is 82% non-detect; glufosinate is 98%. `ResultMeasureValue` is empty
on those rows and the information lives in `ResultDetectionConditionText` with the
limit in `DetectionQuantitationLimitMeasure/MeasureValue`.

**Dropping non-numeric rows is not cleaning — it is selecting on the outcome.**
Mean concentration computed over surviving rows is the mean *of detections*, which
is upward-biased by construction and rises as detection limits improve. This is
left-censored data and needs censored methods (Kaplan-Meier, ROS, or Tobit; see
Helsel, *Statistics for Censored Environmental Data*). Substituting zero or
LOD/2 is common and is criticised for exactly this reason.

## 2. Negative values are present and are not concentrations

| Compound | Negative values |
|---|---:|
| Simazine | 17,408 |
| Alachlor | 17,373 |
| Acetochlor | 13,301 |
| Metolachlor | 12,878 |
| Atrazine | 8,063 |
| Paraquat | 85 of 102 numeric |

These are estimated or blank-corrected values reported below the detection limit,
not measurements of negative concentration. They must be treated as censored, not
clipped to zero and not averaged in. Paraquat is the extreme case: **85 of its 102
numeric values are negative**, so it has almost no real positive detections
nationally.

## 3. Monitoring effort is wildly unequal, and it is not proportional to use

Glyphosate is the most-used agricultural pesticide in the United States by a
factor of roughly four (PNSP 2012: 129.9M kg, against 32.0M kg for atrazine). It
is monitored at **7,305 sites against atrazine's 41,917 — 17%** — because it
requires a dedicated analytical method and is absent from the standard
multi-residue scans that generate most WQP records.

Paraquat is starker: 3.6M kg of annual use, **41 monitoring sites nationally**,
142 measurements across 15 years.

**Never report detections as a share of total samples, and never compare
detection frequency across compounds without conditioning on samples analysed for
that compound.** A chart showing the most-used herbicide as among the least
detected is a monitoring artifact, and presenting it as a finding hands an
opposing comment its entire argument.

There is a legitimate and much stronger claim available in the same data: *the
compounds we use most are the ones we measure least.* That is a statement about
the monitoring regime, it is directly supported by the site counts above, and it
does not require any inference about concentration at all.
