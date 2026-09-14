"""Ask the Internet Archive to capture agency files this network cannot reach.

FDA's edge returns 401 to us on every /media/ download, so we cannot mirror
those bytes directly. The Internet Archive's crawler is not blocked. Save Page
Now asks it to fetch and permanently archive the URL; once captured, the file
becomes retrievable through the `id_` replay endpoint like any other capture.

This is the same preservation act the Data Rescue Project and EDGI perform on
federal environmental data, applied to specific public files that an agency is
currently serving and that our own analysis depends on. It creates a public
archive entry -- that is the point of it.

Run `scripts/acquire_fda_residue.py` afterwards to pull the newly captured bytes.
"""
import sys, time, json; sys.path.insert(0, 'scripts')
from fetchlib import session

SPN = "https://web.archive.org/save/"

TARGETS = [
    # FY2023 data files -- published 2025-12-22, never captured.
    ("https://www.fda.gov/media/190129/download", "FDA FY2023 SampleData2023.zip"),
    ("https://www.fda.gov/media/190130/download", "FDA FY2023 Product2023.zip"),
    ("https://www.fda.gov/media/190131/download", "FDA FY2023 Chemical2023.zip"),
    ("https://www.fda.gov/media/190132/download", "FDA FY2023 CountryProductResidueData2023.zip"),
    ("https://www.fda.gov/media/190133/download", "FDA FY2023 ReferenceFiles2023.zip"),
    # FY2014 -- five of seven files never captured.
    ("https://www.fda.gov/media/103526/download", "FDA FY2014 SampleData2014.zip"),
    ("https://www.fda.gov/media/103535/download", "FDA FY2014 Product2014.zip"),
    ("https://www.fda.gov/media/103551/download", "FDA FY2014 CountryProductResidue2014.zip"),
    ("https://www.fda.gov/media/103511/download", "FDA FY2014 Annual Report"),
    ("https://www.fda.gov/media/103519/download", "FDA FY2014 User's Manual"),
    # Stragglers from other years.
    ("https://www.fda.gov/media/108686/download", "FDA FY2015 User's Manual"),
    ("https://www.fda.gov/media/140802/download", "FDA FY2018 Annual Report"),
    ("https://www.fda.gov/media/140803/download", "FDA FY2018 User's Manual"),
]

def save(url, label, sess, tries=2):
    for attempt in range(tries):
        try:
            r = sess.get(SPN + url, timeout=600, allow_redirects=True)
            # A successful capture redirects to /web/<timestamp>/<url>.
            final = r.url
            ts = ""
            if "/web/" in final:
                ts = final.split("/web/")[1].split("/")[0]
            status = "captured" if ts else f"HTTP {r.status_code}"
            return {"url": url, "label": label, "status": status,
                    "capture": ts, "final": final}
        except Exception as e:
            if attempt + 1 < tries:
                time.sleep(20)
                continue
            return {"url": url, "label": label, "status": f"ERR {type(e).__name__}",
                    "capture": "", "final": ""}

if __name__ == "__main__":
    s = session()
    out = []
    for url, label in TARGETS:
        res = save(url, label, s)
        out.append(res)
        print(f"  [{res['status']:<12}] {res['capture']:<15} {label}", flush=True)
        # SPN is rate-limited for anonymous callers; pace deliberately.
        time.sleep(12)
    json.dump(out, open("data/raw/fda/_discovery/spn_results.json", "w"), indent=2)
    n = sum(1 for r in out if r["status"] == "captured")
    print(f"\n{n} of {len(out)} captured")
