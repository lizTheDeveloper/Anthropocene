"""USDA AMS Pesticide Data Program -- full annual archive plus codebooks.

~310k samples / 126 commodities since 1992. Each annual zip holds the sample
records plus that year's reference tables; the schema is stable enough to
concatenate across years, but the commodity set rotates annually in
coordination with EPA, so year-over-year commodity coverage is NOT balanced.
Treat "detections rose" claims carefully: the commodity mix moved too.

Downloading the annual summary PDFs alongside the data is deliberate -- they
carry the sampling design and the EPA benchmark comparisons that make the
numbers interpretable.
"""
import sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session

MEDIA = "https://www.ams.usda.gov/sites/default/files/media/"
AGENCY, DATASET = "usda-ams", "pdp"

# 2006, 2015-2017 are served with an uppercase .ZIP extension.
UPPER = {2006, 2015, 2016, 2017}
data = [f"{MEDIA}{y}PDPDatabase.{'ZIP' if y in UPPER else 'zip'}" for y in range(1992, 2025)]

codebooks = [
    f"{MEDIA}PDPDatabaseInstructions.pdf",
    f"{MEDIA}PDPSearchAppDataDictionary.pdf",
    f"{MEDIA}PDPSearchAppUserGuide.pdf",
    f"{MEDIA}PDPAnnualSummary.pdf",
]

summaries = [f"{MEDIA}{y}%20PDP%20Annual%20Summary.pdf" for y in range(1992, 2012)] + [
    f"{MEDIA}{y}PDPSummary.pdf" for y in (2012, 2013, 2014, 2015, 2022)
] + [
    f"{MEDIA}2016PDPAnnualSummary.pdf.pdf",
    f"{MEDIA}2017PDPAnnualSummary.pdf",
    f"{MEDIA}2019PDPAnnualSummary.pdf",
    f"{MEDIA}2020PDPAnnualSummary.pdf",
    f"{MEDIA}2021PDPAnnualSummary.pdf",
    f"{MEDIA}2023PDPAnnualSummary.pdf",
]

s = session()
print("== PDP annual databases 1992-2024 ==")
fetch_all(data, AGENCY, DATASET, subdir="annual", sess=s, timeout=900,
          notes="annual sample + reference tables; commodity set rotates yearly")
print("== PDP codebooks ==")
fetch_all(codebooks, AGENCY, DATASET, subdir="codebooks", sess=s,
          notes="schema/data dictionary -- required to interpret the annual zips")
print("== PDP annual summary reports ==")
fetch_all(summaries, AGENCY, DATASET, subdir="annual-summaries", sess=s,
          notes="published summary incl. sampling design and EPA benchmark comparison")
