# Step 11 — Exploratory data analysis

Acquisition is largely done; this is what the data is *for*.

- [x] `scripts/verify_mirror.py` — checksum + structural validation + inventory
- [x] `scripts/smoke_test.py` — every dataset opened, schema confirmed, sampled
- [x] `scripts/parse_40cfr180.py` — tolerance table extracted and classified
- [ ] Compound crosswalk: PNSP names ↔ CA PUR `chem_code` ↔ PDP/FDA residue codes ↔ CAS ↔ 40 CFR 180 section
- [ ] County-year pesticide use panel (PNSP 1992–2018, California backfilled from PUR)
- [ ] PDP detection rates conditioned on commodity mix (the mix rotates annually)
- [ ] FDA residue FY2014–2023 concatenated on the ReferenceFiles code tables
- [ ] TDS residue + nutrient joint analysis on the FY2018–20 frame
- [ ] SR Legacy vs Foundation nutrient comparison, method-stratified
- [ ] NHANES exposure ↔ biomarker analysis within individuals
- [ ] NRI erosion trend from a single release
- [ ] ECOTOX soil-organism endpoints for the top compounds by county use

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
