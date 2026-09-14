"""USDA NASS Quick Stats bulk dumps -- the whole database without an API key.

The Quick Stats API is rate-limited and key-gated; NASS also publishes the same
underlying records as gzipped tab-delimited dumps. `environmental` carries the
Agricultural Chemical Use Program results (percent acres treated, rate,
applications) and `census2022` carries cover crop / tillage acreage by county,
which is the denominator for any regenerative-practice adoption claim.
"""
import sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session

BASE = "https://www.nass.usda.gov/datasets/"
AGENCY, DATASET = "usda-nass", "quickstats-bulk"
STAMP = "20260912"   # NASS stamps the rolling files with a build date

items = [
    (f"{BASE}Readme.txt", "Readme.txt"),
    (f"{BASE}qs.environmental_{STAMP}.txt.gz", None),   # chemical use: the pillar-1 survey data
    (f"{BASE}qs.crops_{STAMP}.txt.gz", None),
    (f"{BASE}qs.economics_{STAMP}.txt.gz", None),
    (f"{BASE}qs.demographics_{STAMP}.txt.gz", None),
    (f"{BASE}qs.animals_products_{STAMP}.txt.gz", None),
    (f"{BASE}qs.census2022.txt.gz", None),              # cover crop + tillage, county level
    (f"{BASE}qs.census2017.txt.gz", None),
    (f"{BASE}qs.census2012.txt.gz", None),
    (f"{BASE}qs.census2007.txt.gz", None),
    (f"{BASE}qs.census2002.txt.gz", None),
]
fetch_all(items, AGENCY, DATASET, sess=session(), pause=1.0, timeout=1800,
          notes="Quick Stats bulk dump; equivalent to API content, no key required")
