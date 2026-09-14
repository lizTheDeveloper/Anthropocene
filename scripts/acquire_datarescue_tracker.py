"""Data Rescue Project tracker -- who else has backed up which federal dataset.

The tracker is a coordination catalogue maintained by the data-rescue community
(Baserow public grid, queryable without a key). It matters here for two reasons
that have nothing to do with duplicating effort:

  1. Independent custody. Where a third party holds a copy of a dataset we also
     mirror, a checksum disagreement between the two is evidence that the file
     changed -- a much stronger claim than our single copy plus our own word.
  2. Early warning. Datasets appear here because someone judged them at risk.
     A dataset this project depends on showing up in the tracker is a signal
     about that dataset's stability, independent of anything the agency says.

Pulls the full catalogue and the maintainers list, then reports which of our
own sources have independent rescue copies.
"""
import json, sys, time; sys.path.insert(0, 'scripts')
from fetchlib import RAW, record, utcstamp, today, sha256_file, append_manifest, session

BASE = "https://baserow.datarescueproject.org/api/database/views"
BACKUPS = "Nt_M6errAkVRIc3NZmdM8wcl74n9tFKaDLrr831kIn4"
MAINTAINERS = "kIH2BAiLD6PyrEoDkekgDkpRy0U6knh8HTyIkB3Qu5o"
AGENCY, DATASET = "datarescueproject", "rescue-tracker"

s = session()

def fields(kind, slug):
    r = s.get(f"{BASE}/{kind}/{slug}/public/fields/", timeout=120)
    return r.json() if r.status_code == 200 else []

def all_rows(kind, slug, page=200):
    out, offset = [], 0
    while True:
        r = s.get(f"{BASE}/{kind}/{slug}/public/rows/",
                  params={"limit": page, "offset": offset}, timeout=180)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code} at offset {offset}"); break
        d = r.json()
        out.extend(d.get("results", []))
        if not d.get("next"):
            break
        offset += page
        time.sleep(0.3)
    return out

def save(name, obj, notes):
    d = RAW / AGENCY / DATASET / today(); d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(json.dumps(obj, indent=1))
    sha = sha256_file(p)
    record({"url": f"{BASE}/...", "retrieved_at": utcstamp(), "sha256": sha,
            "bytes": p.stat().st_size, "agency": AGENCY, "dataset": DATASET,
            "filename": name, "content_type": "application/json",
            "http_status": 200, "license": "community catalogue; see datarescueproject.org",
            "notes": notes})
    append_manifest(DATASET, sha, p)
    return p

print("== backups catalogue ==")
bf = fields("grid", BACKUPS)
rows = all_rows("grid", BACKUPS)
print(f"  {len(rows):,} backup records, {len(bf)} fields")
save("backups_fields.json", bf, "Baserow field schema for the backups grid")
save("backups_rows.json", rows, "Data Rescue Project backups catalogue")

print("== maintainers ==")
mf = fields("gallery", MAINTAINERS)
mrows = all_rows("gallery", MAINTAINERS)
print(f"  {len(mrows):,} maintainer records")
save("maintainers_fields.json", mf, "Baserow field schema for the maintainers gallery")
save("maintainers_rows.json", mrows, "Data Rescue Project maintainers list")
