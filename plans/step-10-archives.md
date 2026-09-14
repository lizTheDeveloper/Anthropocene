# Step 10 — Archives and mirrors (assume nothing stays up)

- [x] Internet Archive used as the retrieval path for every agency that blocks
      this network (FDA, NRCS) — `id_` modifier, original bytes, capture
      timestamp recorded in `provenance.csv`
- [ ] Harvard Law School Library Data.gov Archive (BagIt, ~16 TB, 311,000+ datasets)
- [ ] DataLumos (ICPSR) community deposit archive
- [x] **Data Rescue Project tracker** — full catalogue mirrored (6,140 backup
      records, 45 maintainers) and cross-referenced against every source in this
      project; see `docs/INDEPENDENT_CUSTODY.md`
- [ ] Public Environmental Data Partners (EJScreen, FEMA Future Risk Index, CDC SVI/EJI)
- [ ] EDGI federal environmental website change tracking; *Climate of Suppression* (Aug 2025)
- [ ] essentialdata.us terminations tracker
- [ ] Re-retrieval schedule: re-fetch headline files quarterly, diff checksums,
      flag silent edits

## The point of this step

Datasets that remain live have in some cases been **altered** rather than
removed. Where a figure matters to the argument, check it against an archived
snapshot. Our own mirror plus `scripts/verify_mirror.py` makes that check
mechanical for anything already in custody; this step extends the same
capability to things we have not yet mirrored.


## Headline finding (2026-09-14)

Four pillars of this project rest on datasets with **no working independent
backup**: USGS PNSP (the rescue attempt is recorded as *failed*), FDA pesticide
residue monitoring and the FDA Total Diet Study (zero records in the
catalogue), and the NRCS National Resources Inventory (the catalogue's "NRI"
entries are FEMA's National Risk Index, a different dataset).

PDP, NASS Quick Stats, FoodData Central, SR Legacy and ECOTOX do have
independent copies; NHANES has one flagged incomplete. Full table in
`docs/INDEPENDENT_CUSTODY.md`.

Consequence: those four are the priority for quarterly re-retrieval and
checksum-diffing, and are the ones worth depositing back into DataLumos or
Harvard Dataverse — that would close a hole in the public record rather than
just backing up our own work.
