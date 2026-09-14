# Independent custody: what the Data Rescue Project tracker says about our sources

The Data Rescue Project maintains a coordination catalogue of federal-data
backup efforts (Baserow public grid, queryable without a key; 6,140 backup
records and 45 maintainer organisations as retrieved 2026-09-14, mirrored under
`data/raw/datarescueproject/`).

It matters here for two reasons, neither of which is avoiding duplicated work:

1. **Independent custody.** Where a third party holds a copy of a dataset we
   also mirror, a checksum disagreement between the two copies is evidence that
   the file changed. That is a far stronger claim than our single copy plus our
   own assertion about when we took it.
2. **Early warning.** A dataset appears in this catalogue because someone
   judged it at risk. Its presence is a signal about that dataset's stability,
   independent of anything the agency says.

## Findings for this project's sources

| Our dataset | Independent copy | Notes |
|---|---|---|
| **USGS PNSP** | **NO — rescue FAILED** | Harvard Dataverse `10.7910/DVN/2FQEK6`, status **Error**, 0.0000 GB. Source URL on the record is exactly the one we mirror. |
| **FDA pesticide residue monitoring** | **NO — zero records** | Nobody in the catalogue has rescued it. |
| **FDA Total Diet Study** | **NO — zero records** | Nobody in the catalogue has rescued it. |
| **NRCS National Resources Inventory** | **NO** | The four "NRI" hits are FEMA's *National Risk Index*, a different dataset. The soil NRI is absent. |
| USDA PDP | yes | DataLumos project 250233, 0.171 GB, Finished. |
| NASS Quick Stats | yes | DataLumos project 238414, 3.4 GB, Finished. |
| FoodData Central / SR Legacy | yes | DataLumos projects 250286 and 250304. |
| EPA ECOTOX | yes | Harvard Dataverse `10.7910/DVN/LTVQUK`, 0.95 GB. |
| NHANES | partial | Harvard Dataverse `10.7910/DVN/WYIIQ1`, 1.4 GB, **flagged incomplete** — "a small number of very large" files missing. |
| CompTox / IRIS | yes, impractically | 1 TB WARC/WACZ on sciop.net, flagged `takedown_issued`. |
| NCSS / KSSL | partial | Only the POX-C dataset (DataLumos 250419), not the Lab Data Mart. |

## The consequence

Four of this project's pillars rest on datasets with **no working independent
backup**: PNSP (the entire pesticide-use pillar), FDA residue monitoring and the
Total Diet Study (the exposure pillar, and the only internally-valid
residue-plus-nutrient frame), and the NRI (the erosion backbone).

For PNSP this is not an oversight by the community — they tried and the attempt
is recorded as failed. Our mirror may be among the few complete accessible
copies outside USGS. The same three properties that make these datasets hard to
rescue are the ones that make them valuable: FDA refuses many networks outright,
NRCS refuses all but a browser-shaped TLS fingerprint, and the PNSP county files
sit behind a WAF that rejects an incomplete header set.

That raises the stakes on our own custody rather than lowering them:

- These four are the highest priority for the quarterly re-retrieval and
  checksum-diff described in `plans/step-01-infrastructure.md`.
- They are the ones worth depositing somewhere durable. Contributing our PNSP,
  FDA residue and TDS mirrors back to DataLumos or Harvard Dataverse would close
  a real hole in the public record, not merely back up our own work.
  Submission form: the Data Rescue Tracker's own intake (a Baserow form linked
  from datarescueproject.org/data-rescue-tracker).
- A citation to any of them in a petition should carry our retrieval date and
  checksum explicitly, because there is no second copy to appeal to.

## Access notes

`datalumos.org` and `dataverse.harvard.edu` both refuse this network (403 / a
202 challenge), so the independent copies could not be checksum-compared here.
`source.coop` refuses curl but yields to wget — the same fingerprint behaviour
seen at NRCS. The cross-copy comparison remains open work.
