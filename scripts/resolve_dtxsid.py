"""Resolve crosswalk compounds to EPA DTXSIDs.

DTXSID is EPA's universal substance identifier and the join key into CompTox /
ToxCast / Tox21, and onward to CAS and PubChem. Adding it to the compound
crosswalk is what lets the toxicology pillar be joined to the use and residue
pillars without another round of name matching.

Only the CompTox dashboard search endpoint is used -- it is the one the
dashboard UI itself calls, needs no key, and is confirmed working. Matching is
restricted to exact name equality after normalisation: the endpoint is a
prefix search, so "Atrazine" also returns "Atrazine-2-Ethoxy" and
"Atrazine-acetochlor mixt.", which are different substances with different
toxicology. Accepting a prefix hit would silently attach the wrong hazard data
to a compound.
"""
import csv, json, sys, time; sys.path.insert(0, 'scripts')
from fetchlib import session, RAW, today, record, utcstamp, sha256_file, append_manifest

API = "https://comptox.epa.gov/dashboard-api/ccdapp1/search/chemical/start-with/"
s = session()
s.headers.update({"Accept": "application/json"})

def norm(x):
    return "".join(c for c in str(x).upper() if c.isalnum())

rows = list(csv.DictReader(open("data/derived/compound_crosswalk.csv")))
# Only compounds that actually appear in the use data are worth resolving.
targets = [r for r in rows if r.get("pnsp_compound")]
print(f"resolving {len(targets)} PNSP compounds to DTXSID")

out, exact, ambiguous, missing = [], 0, 0, 0
for i, r in enumerate(targets):
    name = r["pnsp_compound"].split("|")[0].strip()
    hit = {"dtxsid": "", "matched_name": "", "match": "none"}
    try:
        resp = s.get(API + name, timeout=60)
        if resp.status_code == 200 and resp.text.strip():
            cands = resp.json()
            want = norm(name)
            ex = [c for c in cands if norm(c.get("searchWord", "")) == want]
            if ex:
                hit = {"dtxsid": ex[0].get("dtxsid", ""), "matched_name": ex[0].get("searchWord", ""),
                       "match": "exact"}
                exact += 1
            elif cands:
                hit["match"] = f"prefix_only({len(cands)})"
                ambiguous += 1
            else:
                missing += 1
        else:
            missing += 1
    except Exception as e:
        hit["match"] = f"error:{type(e).__name__}"
        missing += 1
    out.append({"pnsp_compound": name, "normalized": r["normalized"],
                "pur_chem_code": r.get("pur_chem_code", ""),
                "cfr180_section": r.get("cfr180_section", ""), **hit})
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(targets)}  exact={exact} prefix_only={ambiguous} none={missing}", flush=True)
    time.sleep(0.25)

p = "data/derived/compound_dtxsid.csv"
with open(p, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["pnsp_compound", "normalized", "pur_chem_code",
                                       "cfr180_section", "dtxsid", "matched_name", "match"])
    w.writeheader(); w.writerows(out)
print(f"\nexact DTXSID matches : {exact}")
print(f"prefix-only (rejected): {ambiguous}")
print(f"no result            : {missing}")
print(f"written: {p}")
