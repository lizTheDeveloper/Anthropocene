"""Find the US locations where soil carbon has actually been MEASURED TWICE.

Every soil lens in this project hit the same wall: a rate of change needs two
measurements, and the national products have one. RaCA is explicitly a single
timepoint. SSURGO is modelled. NRI never measures carbon at all.

The NCSS Kellogg Soil Survey Laboratory database is the remaining candidate --
71,329 lab-characterised pedons with measured organic carbon and bulk density,
accumulated over decades. This asks whether any of them are repeats.

Answered two ways, because the answer depends on keying:
  by site_key      -- catches resamples recorded against the same site
  by coordinates   -- catches resamples entered as a new site at the same place

Both agree in magnitude. The resampled set is real but tiny, and identifying it
is the difference between "no measured soil-carbon change exists for the US"
and "it exists at roughly this list of places, and here they are."
"""
import collections, glob, json, sqlite3, sys

DB = glob.glob("data/raw/usda-nrcs/ncss-lab-characterization/*/NCSSLabDataMartSQLite.sqlite3")
if not DB:
    sys.exit("NCSS database not present; run scripts/acquire_ncss_labdata.py first")
con = sqlite3.connect(f"file:{DB[0]}?mode=ro", uri=True)
cur = con.cursor()

def year(v):
    try: return int(str(v)[:4])
    except Exception: return None

# --- method 1: site_key ---
by_key = cur.execute("""SELECT site_key, COUNT(*) n, MIN(site_obsdate), MAX(site_obsdate)
                        FROM lab_combine_nasis_ncss WHERE site_key IS NOT NULL
                        GROUP BY site_key HAVING n > 1""").fetchall()
key_multiyear = [r for r in by_key if year(r[2]) and year(r[3]) and year(r[3]) > year(r[2])]
total_sites = cur.execute("SELECT COUNT(DISTINCT site_key) FROM lab_combine_nasis_ncss").fetchone()[0]

# --- method 2: coordinates ---
rows = cur.execute("""SELECT latitude_decimal_degrees, longitude_decimal_degrees,
                             site_obsdate, site_key, pedon_key
                      FROM lab_combine_nasis_ncss
                      WHERE latitude_decimal_degrees IS NOT NULL
                        AND longitude_decimal_degrees IS NOT NULL
                        AND site_obsdate IS NOT NULL""").fetchall()

def group(precision):
    g = collections.defaultdict(list)
    for la, lo, d, sk, pk in rows:
        y = year(d)
        if y is None: continue
        try: g[(round(float(la), precision), round(float(lo), precision))].append((y, sk, pk))
        except Exception: pass
    return g

out = {}
for prec, label in ((4, "~11 m"), (3, "~110 m")):
    g = group(prec)
    multi = {k: v for k, v in g.items() if len({y for y, _, _ in v}) > 1}
    spans = sorted(max(y for y, _, _ in v) - min(y for y, _, _ in v) for v in multi.values())
    out[label] = {"locations": len(g), "resampled": len(multi),
                  "median_span": spans[len(spans)//2] if spans else 0,
                  "max_span": max(spans) if spans else 0,
                  "ge10": sum(1 for s in spans if s >= 10),
                  "ge20": sum(1 for s in spans if s >= 20),
                  "ge30": sum(1 for s in spans if s >= 30)}
    if prec == 3:
        # Export the usable long-span set: this is the actual working list.
        usable = []
        for (la, lo), v in multi.items():
            ys = sorted({y for y, _, _ in v})
            if ys[-1] - ys[0] >= 20:
                usable.append({"lat": la, "lon": lo, "years": ys, "span": ys[-1] - ys[0],
                               "site_keys": sorted({sk for _, sk, _ in v if sk}),
                               "pedon_keys": sorted({pk for _, _, pk in v if pk})})
        usable.sort(key=lambda d: -d["span"])
        import pathlib
        pathlib.Path("data/derived/ncss_repeat_sampled_sites.json").write_text(json.dumps(usable, indent=1))

print(f"NCSS lab-characterised sites: {total_sites:,}")
print(f"\nBy site_key: {len(by_key):,} sites with >1 pedon; "
      f"{len(key_multiyear):,} with observations in different years")
print("\nBy coordinates:")
for label, d in out.items():
    print(f"  {label:<8} {d['locations']:>7,} locations | resampled in different years "
          f"{d['resampled']:>4,} ({100*d['resampled']/max(d['locations'],1):.3f}%) | "
          f"median span {d['median_span']}y, max {d['max_span']}y | "
          f">=10y {d['ge10']}, >=20y {d['ge20']}, >=30y {d['ge30']}")
print("\nwritten: data/derived/ncss_repeat_sampled_sites.json (locations with >=20-year spans)")
con.close()
