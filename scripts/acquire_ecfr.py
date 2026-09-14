"""eCFR -- 40 CFR Part 180, the complete pesticide tolerance table.

Part 180 is the authoritative list of every pesticide-commodity tolerance
currently in force, plus the exemptions. For a FFDCA 408(d) petition this is
the target list: a petition to revoke tolerances has to name them.

Both the structured XML (parseable into a tolerance table) and the point-in-time
version are captured, because tolerances change and the date of the text you
cite matters.
"""
import sys, datetime; sys.path.insert(0, 'scripts')
from fetchlib import fetch, session

AGENCY, DATASET = "ecfr", "40cfr180-tolerances"
# eCFR only serves issue dates it has actually published; today may be ahead of it.
TODAY = "2026-09-09"  # Title 40 latest_issue_date, read from ecfr_titles.json
s = session()

targets = [
    (f"https://www.ecfr.gov/api/versioner/v1/full/{TODAY}/title-40.xml?part=180",
     f"40CFR180_full_{TODAY}.xml", "full text of Part 180 as of retrieval date"),
    (f"https://www.ecfr.gov/api/versioner/v1/structure/{TODAY}/title-40.json",
     f"title40_structure_{TODAY}.json", "Title 40 hierarchy incl. Part 180 sections"),
    ("https://www.ecfr.gov/api/versioner/v1/titles.json",
     "ecfr_titles.json", "eCFR title index with issue dates"),
    (f"https://www.ecfr.gov/api/versioner/v1/versions/title-40.json?part=180",
     "40CFR180_version_history.json", "amendment history for every section of Part 180"),
]
for url, name, note in targets:
    r = fetch(url, AGENCY, DATASET, filename=name, sess=s, notes=note, timeout=600)
    print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>12,}  {name}")
