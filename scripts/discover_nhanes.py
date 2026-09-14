"""Rediscover NHANES laboratory and dietary file URLs.

The original discovery index lived under data/raw/ and so was gitignored; it did
not survive the move between machines. This rebuilds it from the CDC component
listing pages, which is cheap and keeps the index reproducible rather than a
one-off artifact.
"""
import json, re, sys, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import session

OUT = pathlib.Path("data/raw/cdc-nhanes/_discovery"); OUT.mkdir(parents=True, exist_ok=True)
s = session()
rows = []
for comp in ["Laboratory", "Dietary"]:
    r = s.get(f"https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component={comp}", timeout=240)
    print(f"{comp}: HTTP {r.status_code} {len(r.text):,} chars")
    if r.status_code != 200:
        continue
    (OUT / f"{comp}.html").write_text(r.text)
    for m in re.finditer(r"<tr>(.*?)</tr>", r.text, re.S):
        tr = m.group(1)
        xpt = re.search(r'href="([^"]+\.(?:XPT|xpt))"', tr)
        doc = re.search(r'href="([^"]+\.(?:htm|html))"', tr)
        tds = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()
               for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if not xpt:
            continue
        absolute = lambda u: ("https://wwwn.cdc.gov" + u) if u.startswith("/") else u
        rows.append({"component": comp,
                     "cycle": tds[0] if tds else "",
                     "name": tds[1] if len(tds) > 1 else "",
                     "xpt": absolute(xpt.group(1)),
                     "doc": absolute(doc.group(1)) if doc else ""})
    time.sleep(2)
(OUT / "nhanes_index.json").write_text(json.dumps(rows, indent=1))
print(f"indexed {len(rows)} XPT files")
