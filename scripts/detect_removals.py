"""Detect federal URLs that were live and are now gone, from the capture record.

"Scrubbed" gets used for three different things, and a petition that conflates
them loses the argument:

  REMOVED      the URL served 200 for years and now 404s or does not resolve.
               The capture history proves it, with dates.
  NEVER COLLECTED  the data does not exist and never did -- e.g. no federal
               pesticide registration test for soil organisms has ever been
               required (40 CFR 158.630). Nothing was taken away.
  UNREACHABLE  the agency still serves it, but refuses this client. NRCS
               answers wget and not curl; FDA refused an entire network.

This script separates the first from the third by asking the Internet Archive
for each URL's status history and comparing it against a live fetch. It cannot
detect the second -- that requires reading the regulation, not the archive.
"""
import subprocess, sys, time, json
sys.path.insert(0, "scripts")
from fetchlib import session

CDX = "https://web.archive.org/cdx/search/cdx"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
s = session()

def history(url, tries=4):
    """Status codes over time for a URL, oldest first."""
    params = [("url", url), ("output", "json"), ("collapse", "timestamp:6"), ("limit", "400")]
    for i in range(tries):
        try:
            r = s.get(CDX, params=params, timeout=200)
            if r.status_code == 200:
                j = r.json()
                return [dict(zip(j[0], x)) for x in j[1:]] if len(j) > 1 else []
        except Exception:
            pass
        time.sleep(5 * (i + 1))
    return None

def live(url):
    """Current status, trying wget where curl is refused (different TLS fingerprint)."""
    c = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "40",
                        "-L", "-A", UA, url], capture_output=True, text=True).stdout.strip()
    if c in ("000", "403"):
        w = subprocess.run(["wget", "-q", "--timeout=25", "--tries=1", "-O", "/dev/null", url],
                           capture_output=True)
        if w.returncode == 0:
            return c, "reachable via wget"
    return c, ""

def classify(url):
    h = history(url)
    now, note = live(url)
    if h is None:
        return {"url": url, "verdict": "INDEX UNREACHABLE", "now": now, "note": note}
    ok = [x for x in h if x.get("statuscode") == "200"]
    gone = [x for x in h if x.get("statuscode") in ("404", "410")]
    first = ok[0]["timestamp"][:8] if ok else None
    last_ok = ok[-1]["timestamp"][:8] if ok else None
    first_gone = gone[0]["timestamp"][:8] if gone else None
    if ok and now in ("404", "410"):
        v = "REMOVED"
    elif ok and now == "200":
        v = "live"
    elif ok and note:
        v = "UNREACHABLE (served, refuses this client)"
    elif ok:
        v = "UNREACHABLE / unresolved"
    else:
        v = "no 200 ever captured"
    return {"url": url, "verdict": v, "captures": len(h), "first_200": first,
            "last_200": last_ok, "first_404": first_gone, "now": now, "note": note}

TARGETS = [
    "https://www.epa.gov/ejscreen",
    "https://ejscreen.epa.gov/mapper/",
    "https://www.usda.gov/climate-solutions",
    "https://www.nrcs.usda.gov/resources/data-and-reports/soil-carbon-monitoring-network",
    "https://ncsslabdatamart.sc.egov.usda.gov/",
    "https://ltar.ars.usda.gov/",
    "https://nassgeodata.gmu.edu/CropScape/",
    "https://water.usgs.gov/nawqa/pnsp/usage/maps/county-level/",
]

if __name__ == "__main__":
    out = []
    print(f"{'verdict':<42} {'now':>5}  {'first 200':>9} {'last 200':>9}  url")
    print("-" * 150)
    for u in TARGETS:
        r = classify(u)
        out.append(r)
        print(f"{r['verdict']:<42} {str(r.get('now')):>5}  {str(r.get('first_200') or '-'):>9} "
              f"{str(r.get('last_200') or '-'):>9}  {u[:70]}")
        if r.get("note"):
            print(f"{'':<42}        {r['note']}")
        time.sleep(2)
    import pathlib
    pathlib.Path("data/derived/removal_audit.json").write_text(json.dumps(out, indent=2))
    print("\nwritten: data/derived/removal_audit.json")
