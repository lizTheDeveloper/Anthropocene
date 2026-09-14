# Step 10 — Archives and mirrors (assume nothing stays up)

- [x] Internet Archive used as the retrieval path for every agency that blocks
      this network (FDA, NRCS) — `id_` modifier, original bytes, capture
      timestamp recorded in `provenance.csv`
- [ ] Harvard Law School Library Data.gov Archive (BagIt, ~16 TB, 311,000+ datasets)
- [ ] DataLumos (ICPSR) community deposit archive
- [ ] Data Rescue Project clearinghouse — 1,000+ preserved datasets
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
