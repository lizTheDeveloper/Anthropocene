# Step 11 — Exploratory data analysis

Acquisition is largely done; this is what the data is *for*.

- [x] `scripts/verify_mirror.py` — checksum + structural validation + inventory
- [x] `scripts/smoke_test.py` — every dataset opened, schema confirmed, sampled
- [x] `scripts/parse_40cfr180.py` — tolerance table extracted and classified
- [x] Compound crosswalk: PNSP names ↔ CA PUR `chem_code` ↔ 40 CFR 180 section
- [x] County-year pesticide use panel (PNSP 1992–2018), with comparability audit
- [x] **Finding 01** — the published 2016→2018 decline is an artifact (California + double-counting)
- [x] **Finding 02** — mass flat (+14.7%, or +2.3% fixed roster); composition transformed, glyphosate 17×
- [x] **Finding 03** — WQP monitoring tracks 1992 use (ρ=+0.55, p=0.019), not 2018 use (p=0.58)
- [x] **Finding 04** — 79% of applied mass has zero comparable acute soil-fauna endpoints in ECOTOX
- [ ] California backfill from PUR for 2017–18, to restore a true 50-state series
- [ ] PDP detection rates conditioned on commodity mix (the mix rotates annually)
- [ ] FDA residue FY2014–2023 concatenated on the ReferenceFiles code tables
- [ ] TDS residue + nutrient joint analysis on the FY2018–20 frame
- [ ] SR Legacy vs Foundation nutrient comparison, method-stratified
- [ ] NHANES exposure ↔ biomarker analysis within individuals
- [ ] NRI erosion trend from a single release
- [ ] ECOTOX soil-organism endpoints for the top compounds by county use

## Traps found during analysis (added to the smoke-test list)

- **PNSP publishes AGGREGATE AND COMPONENT rows together from 2016.**
  `METOLACHLOR & METOLACHLOR-S` and `DIMETHENAMID & DIMETHENAMID-P` appear
  alongside their components, and the aggregate equals the component sum exactly
  (ratio 1.000). Naive summation inflates 2016–18 national totals by 8–9%.
- **2017–18 county files exclude California** (`noCA` / `NoDPR` in the filename).
  California is 12–13% of national mass, so a 50-state year compared against a
  49-state year manufactures a ~10% decline that is not real.
- **ECOTOX `chemicals.txt` carries SYSTEMATIC names, not common ones** — glyphosate
  is `N-(Phosphonomethyl)glycine`. Joining on name silently returns nothing; join
  on CAS.
- **ECOTOX `ecotox_group == "Worms"` includes marine polychaetes** (*Nereis*,
  *Glycera*). Filtering on it alone puts saltwater ragworms in a soil analysis;
  use `organism_habitat == "Soil"` with the standard soil-test families.

## Known schema traps found during the smoke test

- **PDP `PDP##Results.txt` and `PDP##Samples.txt` have NO header row.** Column
  names come from `PDP DataDictionary <year>.pdf` inside the same zip. Reading
  them with `header=0` silently consumes the first data record as column names.
- **CA PUR** splits each year across ~50 `udc<yy>_<nn>.txt` files by county, plus
  separate `chemical.txt` / `county.txt` / `site.txt` lookups. Numeric
  `chem_code` and `site_code` are meaningless without them.
- **FDA `SampleData<year>.txt`** is tab-delimited with quoted fields; residue
  codes resolve only through that year's `ReferenceFiles` zip.
- **NASS bulk** files are tab-delimited, latin-1, and large (`qs.crops` is 1.1 GB
  gzipped). Chunk them; `VALUE` is a string with thousands separators and
  suppression codes, not a number.
- **eCFR Part 180** uses `DIV8`/`TABLE`/`TR`/`TD`, not `SECTNO`/`ROW`. Sec. 180.1
  (definitions) and Sec. 180.41 (crop group tables) share the tolerance table
  shape and must be excluded from tolerance counts.

## The design question to settle before joining anything

PNSP is modelled county-level use. PDP is a rotating commodity sample. NRI is a
land-point panel. FDC is a food-item reference table. A "pesticide use up → soil
carbon down → nutrients down" chain built on those four frames is a descriptive
association unless an explicit causal design says otherwise. Decide now whether
this is a causal claim with a design behind it, or an honestly-labelled
descriptive one. If causation is asserted on a join of four incompatible frames,
that will be the entire content of the opposing comment.
