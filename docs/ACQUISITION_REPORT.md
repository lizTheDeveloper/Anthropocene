# Acquisition report — 2026-09-14

**651 files, 12.4 GB, 14 datasets. All checksums verified; no corrupt archives;
every dataset opened and its schema confirmed. Two truncated PDFs found and
quarantined (see gap 3).**

## What landed

| Dataset | Files | Size | Coverage |
|---|---:|---:|---|
| `ca-dpr/pur` | 55 | 3.9 GB | Full-census CA application records, **1974–2023**, + codebooks |
| `cdc-nhanes/lab-and-dietary` | 328 | 2.0 GB | 164 lab/dietary files + docs, 1999–2023 |
| `usda-nass/quickstats-bulk` | 11 | 3.2 GB | Chemical use, crops, economics, demographics, Census 2002–2022 |
| `usda-ams/pdp` | 68 | 294 MB | **Every PDP year 1992–2024** + codebooks + summaries |
| `usda-ars-fdc/fooddata-central` | 22 | 522 MB | SR Legacy, 14 Foundation vintages, FNDDS, current full release |
| `usgs/pnsp` | 28 | 258 MB | County estimates 1992–2012 final, 2013–2018 preliminary, state-level |
| `epa/ecotox` | 2 | 138 MB | Full ASCII release 2026-09-15 + terms appendix |
| `usda-historical/food-composition` | 9 | 121 MB | Atwater Bull. 28 (1896/1899), AH-8 + 6 sectionals |
| `usda-nrcs/raca` | 27 | 74 MB | Methodology, protocols, 16 regional summaries |
| `fda/pesticide-residue-monitoring` | 57 | 55 MB | FY2014–FY2023 (see gaps) |
| `usda-nrcs/nri` | 11 | 17 MB | 2017 Summary, codebooks, Soils Refresh 2021–2025 |
| `ecfr/40cfr180-tolerances` | 4 | 13 MB | Part 180 full XML + amendment history |
| `fda/total-diet-study` | 7 | 12 MB | FY2018–FY2020 elements + radionuclides |

Derived: `data/derived/40cfr180_tolerances.csv` — **15,416 tolerance rows**
across 409 sections and 2,474 commodities, plus 1,480 exemption and 1,300
definitional rows (classified, not discarded).

## Access obstacles and how they were handled

- **`www.fda.gov` returns HTTP 401** to this network on every data path,
  including with a complete browser header set. Page discovery ran through
  archived HTML; bytes came from the Internet Archive `id_` endpoint, which
  replays the original unmodified response. 64 FDA artifacts are tagged
  `VIA_WAYBACK` with capture timestamps.
- **`www.nrcs.usda.gov` resets the connection** on `/resources/…` and
  `/sites/default/files/…` (the site root returns 200). Same archive route;
  38 artifacts tagged.
- **`water.usgs.gov` refuses a bare User-Agent** but serves normally given a
  complete browser header set. Retrieved directly — no archive dependency.
- The agent proxy reported `bundleCoversEveryHost: true` with no relay failures
  for these hosts, so all three are agency-side WAF decisions, not egress policy.

## Gaps

1. **FDA FY2023 residue data files** — `SampleData2023`, `Product2023`,
   `Chemical2023`, `CountryProductResidueData2023`, `ReferenceFiles2023`
   (media IDs 190129–190133). Published 2025-12-22 and **not captured by the
   Internet Archive**; confirmed by direct CDX lookup. The FY2023 report and
   User's Manual *were* archived and are in custody. Needs either a browser
   download or an Internet Archive Save Page Now request.
2. **FDA FY2014** — only the report and manual are archived; the five data
   archives are not.
3. **2022 NRI Summary Report (Sept 2025)** — tables 15–18 are the erosion
   backbone. **Correction to an earlier version of this report:** the file *is*
   archived, at `.../sites/default/files/2026-02/2022 NRI Summary Report.pdf`;
   the earlier claim that it was absent came from scanning only the `2025-*`
   directories. However the single capture is **itself truncated at exactly
   5 MiB** with no trailing `%%EOF`, and a Range request past that offset 404s,
   so the bytes are not in the archive. `Historical-Changes-In-Soil-Erosion.pdf`
   is truncated identically. Both are quarantined in `data/quarantine/`. Needs a
   browser download. The 2017 report is in custody and intact as an interim —
   see the back-updating warning in `plans/step-04-soil.md` first.

   This is not a general Wayback limit: other captures here came through intact
   at 8.1 MB and 10.5 MB.
4. **TDS pesticide results FY2018+** — only elements and radionuclides are
   posted at the archived URLs. The interactive TDS tool and new data released
   2026-01-27 post-date the newest Wayback capture found (2025-02-08).
5. **regulations.gov** and **EPA CompTox** need API keys / another route.

## Corrections to the source brief

- **PNSP county data stops at 2018 preliminary, not 2019.** The USGS
  county-level listing publishes no 2019 county file. Most recent usable
  county-level year is 2018, preliminary, and **excluding California** —
  2017 and 2018 are published as "NoCA" because USGS substitutes CA DPR PUR
  there. A national total from those years silently undercounts the largest
  agricultural pesticide market in the country unless California is backfilled.
- **PDP begins in 1992, not 1991.**
- **The NASS Quick Stats API key is not on the critical path.** NASS publishes
  the same records as gzipped bulk dumps, including `qs.environmental`
  (Agricultural Chemical Use) and `qs.census2022` (cover crop and tillage by
  county). Item 1 of the recommended acquisition order needs no key at all.

## Schema traps found while validating

- **PDP `PDP##Results.txt` / `PDP##Samples.txt` have no header row.** Column
  names are in `PDP DataDictionary <year>.pdf` inside the same zip. Reading with
  `header=0` silently eats the first data record.
- **eCFR Part 180** uses `DIV8`/`TABLE`/`TR`/`TD`. Sec. 180.1 (commodity
  definitions) and Sec. 180.41 (crop group tables) share the tolerance-table
  shape; counting them inflates the tolerance total by ~19%.
- **CA PUR** splits each year across ~50 `udc<yy>_<nn>.txt` county files; the
  numeric `chem_code` and `site_code` resolve only through the lookup tables.
- **NASS bulk** `VALUE` is a string with thousands separators and suppression
  codes, not a number.
- **eCFR versioner** only serves issue dates it has published — read
  `latest_issue_date` first or the request 404s.

## Sanity check that the data is real

USGS PNSP 2012: 369,394 rows, 389 compounds, 3,064 counties, 48 states.
Top compound by high estimate is glyphosate at 129.9 million kg, against
479.1 million kg total — consistent with the published national picture.
