"""FDA Pesticide Residue Monitoring Program -- FY2014-FY2023 raw data.

FDA's regulatory (enforcement) monitoring: ~3,500 domestic and import samples
per year screened for ~780 pesticides, statutorily required since 1987.

Each year ships five archives plus a User's Manual:
  SampleData<YEAR>.zip        one row per analytical sample result
  Product<YEAR>.zip           summary by product
  Chemical<YEAR>.zip          summary by chemical
  CountryProductResidue*.zip  summary by country x product x residue
  ReferenceFiles<YEAR>.zip    MethodScope, ProdCode, ExtCode, DetCode, Country, Chemical
The code files are NOT self-describing -- the manual is mandatory, which is
why it is pulled into the same directory as the data rather than discarded.

Bytes come from the Internet Archive because FDA's edge returns 401 to this
network; every row is tagged VIA_WAYBACK with its capture timestamp.
"""
import json, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch_via_wayback, session

AGENCY, DATASET = "fda", "pesticide-residue-monitoring"
idx = json.loads(pathlib.Path("data/raw/fda/_discovery/residue_file_index.json").read_text())
s = session()

ok = fail = 0
for year in sorted(idx, key=int):
    print(f"\n== FY{year} ==", flush=True)
    for f in idx[year]:
        label = f["label"]
        # Give the artifact a meaningful name; the /media/N/download URL has none.
        name = label if label.lower().endswith(".zip") else None
        if name is None:
            if "manual" in label.lower():
                name = f"UsersManual{year}.pdf"
            elif "report" in label.lower():
                name = f"AnnualReport{year}.pdf"
            else:
                name = f"{label[:40].replace(' ','_').replace('/','-')}_{year}"
        res = fetch_via_wayback(f["url"], AGENCY, DATASET, filename=name,
                                subdir=f"FY{year}", sess=s,
                                notes=f"FDA FY{year} residue monitoring: {label}")
        if res["ok"]:
            ok += 1
            print(f"  [ok ] {res['bytes']:>12,}  {name}  (capture {res.get('capture')})", flush=True)
        else:
            fail += 1
            print(f"  [FAIL] {name}: {res['status']}", flush=True)
        time.sleep(2.5)
print(f"\nFDA residue: {ok} retrieved, {fail} failed")
