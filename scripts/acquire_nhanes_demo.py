"""NHANES demographics -- without these the lab data cannot describe people.

The biomarker files carry a respondent id (SEQN) and a measurement. Everything
that makes a finding about human beings rather than about test tubes -- age,
sex, income, race/ethnicity -- lives in the DEMO file, and so does the piece
that makes any national statement legitimate at all:

  WTMEC2YR / WTMECPRP : the examination sample weight
  SDMVPSU, SDMVSTRA   : the variance units of the complex survey design

NHANES is a stratified, multistage, oversampled probability sample. An unweighted
mean from it is not an estimate of anything in the US population -- it is a
statistic about who happened to be sampled, and NHANES deliberately oversamples
some groups. Any prevalence reported without these weights is wrong, not
approximate.
"""
import re, sys, json, time, pathlib; sys.path.insert(0, 'scripts')
from fetchlib import fetch, session

AGENCY, DATASET = "cdc-nhanes", "demographics"
s = session()
r = s.get("https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Demographics", timeout=240)
OUT = pathlib.Path("data/raw/cdc-nhanes/_discovery"); OUT.mkdir(parents=True, exist_ok=True)
(OUT / "Demographics.html").write_text(r.text)

rows = []
for m in re.finditer(r'<tr>(.*?)</tr>', r.text, re.S):
    tr = m.group(1)
    xpt = re.search(r'href="([^"]+\.(?:XPT|xpt))"', tr)
    doc = re.search(r'href="([^"]+\.(?:htm|html))"', tr)
    tds = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
    if xpt:
        u = xpt.group(1)
        rows.append({"cycle": tds[0] if tds else "", "name": tds[1] if len(tds) > 1 else "",
                     "xpt": ("https://wwwn.cdc.gov" + u) if u.startswith("/") else u,
                     "doc": ("https://wwwn.cdc.gov" + doc.group(1)) if doc and doc.group(1).startswith("/") else ""})
print(f"{len(rows)} demographics files found")
for r_ in rows:
    cycle = (r_["cycle"] or "unknown").replace(" ", "")
    res = fetch(r_["xpt"], AGENCY, DATASET, subdir=f"{cycle}/data", sess=s, timeout=900,
                notes=f"NHANES demographics {cycle}: {r_['name']} (carries MEC weights + design vars)")
    print(f"  [{'ok ' if res['ok'] else 'FAIL'}] {res.get('bytes',0):>9,}  {cycle} {r_['xpt'].split('/')[-1]}", flush=True)
    if r_["doc"]:
        fetch(r_["doc"], AGENCY, DATASET, subdir=f"{cycle}/docs", sess=s, timeout=300,
              notes="NHANES demographics codebook")
    time.sleep(0.7)
