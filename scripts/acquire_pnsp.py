"""USGS Pesticide National Synthesis Project -- county-level pesticide use estimates.

County-level estimated annual agricultural use (kg) for ~400 compounds, with
low and high estimates. 1992-2012 are final; 2013+ are preliminary. 2017-2018
exclude California, because USGS substitutes CA DPR's full-census PUR data for
California rather than modeling it (see acquire_cdpr_pur.py).
"""
import sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session

BASE = "https://water.usgs.gov/nawqa/pnsp/usage/maps/county-level/"
AGENCY, DATASET = "usgs", "pnsp"

final = [f"{BASE}PesticideUseEstimates/EPest.county.estimates.{y}.txt" for y in range(1992, 2013)]
prelim = [
    f"{BASE}PreliminaryEstimates/EPest.county.estimates.2013.txt",
    f"{BASE}PreliminaryEstimates/EPest.county.estimates.2014.txt",
    f"{BASE}PreliminaryEstimates/2015PreliminaryEstimates.zip",
    f"{BASE}PreliminaryEstimates/2016PreliminaryEstimates.zip",
    f"{BASE}PreliminaryEstimateNOCa/2017PreliminaryEstimatesNoCA.zip",
    f"{BASE}PreliminaryEstimateNOCa/2018PreliminaryEstimatesNoCA.zip",
]
state = [f"{BASE}StateLevel/AgPestUsebyCropGroup92to16.zip"]

s = session()
print("== PNSP final county estimates 1992-2012 ==")
fetch_all(final, AGENCY, DATASET, subdir="county-final", sess=s,
          notes="final county-level estimates; low+high; DOI 10.5066/F7NP22KM")
print("== PNSP preliminary county estimates 2013-2018 ==")
fetch_all(prelim, AGENCY, DATASET, subdir="county-preliminary", sess=s,
          notes="PRELIMINARY estimates, subject to revision; 2017-2018 exclude California")
print("== PNSP state-level by crop group ==")
fetch_all(state, AGENCY, DATASET, subdir="state-level", sess=s,
          notes="state-level agricultural pesticide use by crop group 1992-2016")
