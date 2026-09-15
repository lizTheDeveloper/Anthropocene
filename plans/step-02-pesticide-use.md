# Step 02 — Pesticide use (how much, where, on what)

- [x] **USGS PNSP county-level estimates, final 1992–2012** (21 annual files)
- [x] **PNSP preliminary 2013–2018** (2013–14 txt; 2015–16 zip; 2017–18 zip, no California)
- [x] **PNSP state-level by crop group 1992–2016**
- [x] **California DPR PUR, full annual history from 1974** — legally mandated
      full census, section-level (1 mi²) geography
- [x] PUR data-structure definitions / code lookups (codebooks)
- [x] **NASS Quick Stats bulk dumps** — `environmental` (Agricultural Chemical Use),
      `crops`, `economics`, `demographics`, `animals_products`, and census 2002–2022
- [ ] EPA Pesticide Industry Sales and Usage — top-line framing only, low priority
- [ ] Build crosswalk: PNSP compound names ↔ PUR active ingredient codes ↔ CAS

## Corrections to the source brief

- The brief says PNSP county data runs through **2019 preliminary**. The USGS
  county-level listing actually stops at **2018 preliminary**; there is no 2019
  county file published. Most recent usable county-level year is **2018**, and
  it is preliminary and excludes California.
- 2017 and 2018 preliminary files are published as "NoCA" — California is
  excluded because USGS substitutes CA DPR PUR there. Any national total built
  from these years must add California from PUR or it silently undercounts the
  largest agricultural pesticide market in the country.
- NASS bulk dumps carry the same content as the Quick Stats API without an API
  key. The key is still worth requesting for targeted queries, but it is not on
  the critical path.

## Watch item

USGS has said final 2018–22 estimates for ~400 compounds will publish (2025,
then revised to 2026). Pipeline is built so that release drops in without
rework: add the files to `acquire_pnsp.py` and re-run.
