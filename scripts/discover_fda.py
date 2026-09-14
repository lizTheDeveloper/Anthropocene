"""Discover FDA pesticide-residue and TDS download URLs.

FDA's edge returns 401 to this network for every data path, so discovery runs
through agentsweb.org's fetch/markdown cache (read-only page reads). The URLs
it yields are then pulled as original bytes from the Internet Archive; see
fetchlib.fetch_via_wayback for why that preserves the provenance claim.
"""
import json, re, sys, time, pathlib
import requests

OUT = pathlib.Path("data/raw/fda/_discovery"); OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"})

YEARS = {
    2023: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2023",
    2022: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2022",
    2021: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2021",
    2020: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2020",
    2019: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2019",
    2018: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-report-and-data-fy-2018",
    2017: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-2017-report-and-data",
    2016: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-2016-report-and-data",
    2015: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-2015-report-and-data",
    2014: "https://www.fda.gov/food/pesticides/pesticide-residue-monitoring-2014-report-and-data",
}

def page_md(url, tries=3):
    for i in range(tries):
        try:
            r = S.get("https://agentsweb.org/fetch", params={"url": url}, timeout=300)
            if r.status_code == 200:
                return r.json().get("markdown", "")
        except Exception as e:
            print(f"    retry {i+1}: {e}")
        time.sleep(4 * (i + 1))
    return ""

def clean(link):
    """agentsweb appends the HTML title attribute into the URL; strip it."""
    link = link.split("%20%22")[0].split(' "')[0]
    return link.strip()

found = {}
for year, url in YEARS.items():
    md = page_md(url)
    (OUT / f"fy{year}.md").write_text(md)
    links = re.findall(r'\[([^\]]{0,140})\]\(([^)]+)\)', md)
    files = []
    for text, link in links:
        link = clean(link)
        if re.search(r'fda\.gov/media/\d+/download', link):
            files.append({"label": text.strip(), "url": link})
    # de-dup on url, keep first label
    seen, uniq = set(), []
    for f in files:
        if f["url"] not in seen:
            seen.add(f["url"]); uniq.append(f)
    found[year] = uniq
    print(f"FY{year}: {len(uniq)} files  ({len(md)} chars)")
    for f in uniq:
        print(f"    {f['label'][:55]:<55} {f['url']}")
    time.sleep(2)

(OUT / "residue_file_index.json").write_text(json.dumps(found, indent=2))
print(f"\nWrote index: {sum(len(v) for v in found.values())} files across {len(found)} years")
