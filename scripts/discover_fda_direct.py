"""Rediscover FDA residue file URLs directly from the agency.

The original discovery ran through an archived-HTML route because FDA's edge
refused the cloud container. Where FDA is reachable, reading the live year
pages is simpler and gives the current URL set rather than a historical one.
"""
import json, re, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import session

OUT = pathlib.Path("data/raw/fda/_discovery"); OUT.mkdir(parents=True, exist_ok=True)
YEARS = {y: f"https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-{y}"
         for y in range(2018, 2025)}
YEARS.update({y: f"https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-{y}-report-and-data"
              for y in range(2014, 2018)})

s = session()
found = {}
for year, url in sorted(YEARS.items()):
    try:
        r = s.get(url, timeout=120)
    except Exception as e:
        print(f"FY{year}: ERROR {type(e).__name__}"); continue
    if r.status_code != 200:
        print(f"FY{year}: HTTP {r.status_code}"); continue
    (OUT / f"fy{year}_live.html").write_text(r.text)
    files = []
    for m in re.finditer(r'href="([^"]*?/media/\d+/download[^"]*)"[^>]*>(.{0,160}?)</a>', r.text, re.S):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).replace("\xa0", " ").strip()
        href = m.group(1).split("?")[0]
        if href.startswith("/"):
            href = "https://www.fda.gov" + href
        files.append({"label": label, "url": href})
    seen, uniq = set(), []
    for f in files:
        if f["url"] not in seen:
            seen.add(f["url"]); uniq.append(f)
    found[str(year)] = uniq
    print(f"FY{year}: {len(uniq)} files")
    for f in uniq:
        print(f"    {f['label'][:52]:<52} {f['url']}")
    time.sleep(1)

(OUT / "residue_file_index.json").write_text(json.dumps(found, indent=2))
print(f"\nTOTAL: {sum(len(v) for v in found.values())} files across {len(found)} years")
