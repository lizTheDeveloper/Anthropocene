# Step 07 — Farming practice adoption

For the "mandate regenerative practices" ask, and for the counterfactual.

- [x] **Census of Agriculture 2002–2022** via NASS bulk (`qs.census*.txt.gz`) —
      cover crop acreage, no-till, reduced till, conservation tillage, by county
- [x] NASS `environmental` bulk — pest management practices, scouting, treated acres
- [ ] ERS ARMS production practices and costs (has its own API)
- [ ] NRCS EQIP/CSP contract and practice data via RCA Data Viewer (FY1998–2025)
- [ ] USDA Organic INTEGRITY database — the counterfactual population
- [ ] NASS Cropland Data Layer / CropScape (30 m, 2008–present) — reconstruct
      per-pixel rotation history as a proxy for management intensity

## Notes

- Organic INTEGRITY is a JavaScript application with no static export at the
  documented URLs; it needs either its internal JSON endpoint or a browser-driven
  export. Deprioritised — useful as a counterfactual population, not on the
  critical path.
- Next Census of Agriculture: 2027.

## Budget context worth knowing

The FY2026 NRCS congressional justification proposes a net decrease of ~$783M
and ~2,636 staff years in Private Lands Conservation Operations — including
~$776M and ~2,546 staff years from Conservation Technical Assistance, plus 59
staff years from the Soil Survey Program. If any part of the ask depends on NRCS
delivery capacity, that number is the counterargument. It may also be an argument
worth making.
