"""FDA Pesticide Residue Monitoring -- direct-from-agency acquisition.

Supersedes the Wayback path in acquire_fda_residue.py wherever the agency is
actually reachable. FDA's edge returns 401 from some networks (the cloud
container this project was first built in) but serves normally from others.
Direct retrieval is strictly better provenance: the checksum then attests to
bytes FDA served us at a known time, rather than to a third-party archived copy.

Falls back to the Internet Archive per file, so a partial block degrades
gracefully instead of failing the run.
"""
import json, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch, fetch_via_wayback, session

AGENCY, DATASET = "fda", "pesticide-residue-monitoring"
idx = json.loads(pathlib.Path("data/raw/fda/_discovery/residue_file_index.json").read_text())
s = session()

def name_for(label, year):
    if label.lower().endswith(".zip"):
        return label
    if "manual" in label.lower():
        return f"UsersManual{year}.pdf"
    if "report" in label.lower():
        return f"AnnualReport{year}.pdf"
    return f"{label[:40].replace(' ', '_').replace('/', '-')}_{year}"

direct = wayback = failed = 0
for year in sorted(idx, key=int):
    print(f"\n== FY{year} ==", flush=True)
    for f in idx[year]:
        name = name_for(f["label"], year)
        r = fetch(f["url"], AGENCY, DATASET, filename=name, subdir=f"FY{year}", sess=s,
                  timeout=900, retries=2,
                  notes=f"FDA FY{year} residue monitoring: {f['label']} (direct from agency)")
        if r["ok"]:
            direct += 1
            print(f"  [direct ] {r['bytes']:>12,}  {name}", flush=True)
        else:
            r2 = fetch_via_wayback(f["url"], AGENCY, DATASET, filename=name,
                                   subdir=f"FY{year}", sess=s,
                                   notes=f"FDA FY{year}: {f['label']}")
            if r2["ok"]:
                wayback += 1
                print(f"  [wayback] {r2['bytes']:>12,}  {name} (capture {r2.get('capture')})", flush=True)
            else:
                failed += 1
                print(f"  [FAIL   ] {name}: direct={r['status']} archive={r2['status']}", flush=True)
        time.sleep(1.0)
print(f"\nFDA residue: {direct} direct, {wayback} via archive, {failed} failed")
