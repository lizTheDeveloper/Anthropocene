# Step 08 — Water and environmental fate

- [x] **EPA/USGS Water Quality Portal** — pesticide occurrence results, 2000–present,
      for 18 compounds, plus monitoring-location metadata
- [ ] USGS NAWQA pesticide water quality (84 pesticides, 81 river sites, WY2013–2022)
- [ ] USGS NWIS raw water-quality time series
- [ ] EPA TRI facility-level releases

## Compound selection

The WQP compound list is **derived from the PNSP data already in custody** — top
agricultural-use compounds by 2012 national high estimate — rather than chosen by
hand, so the water pillar is anchored to the same compounds as the use pillar and
the two can be joined without an arbitrary selection step in between.

Fumigants and oils in the PNSP top 30 (1,3-dichloropropene, metam, metam
potassium, chloropicrin, petroleum oil, sulfur, sulfuric acid, methyl bromide)
are deliberately excluded: they are not routinely analysed in water and would
return empty sets that look like absence of contamination.

## A trap specific to glyphosate

Glyphosate leads agricultural use by roughly 4× the next compound, but it has
historically been **under-monitored in water because it requires a dedicated
analytical method** and is not part of the standard multi-residue scans that
produce most WQP records. A low detection count for glyphosate is a monitoring
artifact, not an absence — and reading it as an absence is exactly the kind of
error an opposing comment is built to find. Always report detections against
*number of samples analysed for that compound*, never against total samples.

## Access notes

- `waterqualitydata.us` works directly and returns CSV; results are pulled one
  compound at a time so a single failure does not lose the batch.
- Station metadata is pulled alongside results: a Result row without its
  MonitoringLocation is not locatable.
- `www.usgs.gov/mission-areas/...` returns 403 to this network; the NAWQA
  landing page needs the archive route. `water.usgs.gov` itself works given a
  complete browser header set (see `fetchlib.BROWSER_HEADERS`).
- **TRI**: the documented bulk zip paths (`www3.epa.gov/tri/current/US_<year>.zip`,
  `ordsext.epa.gov/FLA/...`) return 404, and the TRI pages are JavaScript-driven
  with no static links. The working route is the **Envirofacts REST API**:
  `https://data.epa.gov/efservice/<table>/rows/<start>:<end>/JSON` — confirmed
  returning `tri_facility` records. It is paginated, so a full pull is many
  requests. TRI is the lowest-value item in this pillar (it covers the
  manufacturing side, not application), so it is documented rather than pulled.
