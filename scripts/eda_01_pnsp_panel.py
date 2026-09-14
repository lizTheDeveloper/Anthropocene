"""Build the PNSP county-year-compound panel, 1992-2018, and audit its comparability.

Three discontinuities in this series will silently corrupt a trend line:

  1. 1992-2012 are FINAL estimates; 2013-2018 are PRELIMINARY and subject to
     revision. Mixing them without a flag conflates real change with estimate
     maturity.
  2. 2017 and 2018 EXCLUDE CALIFORNIA (the files are named "noCA"/"NoDPR")
     because USGS substitutes CA DPR's full-census PUR data there. A national
     total from those years is not comparable to earlier ones.
  3. The compound roster changes between years -- compounds enter and leave the
     survey -- so a national total is partly a function of what was surveyed.

Every one of those is recorded as a column rather than smoothed over.
"""
import glob, io, re, zipfile
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"; OUT.mkdir(parents=True, exist_ok=True)
BASE = ROOT / "data/raw/usgs/pnsp/2026-09-14"

def read_txt(buf, year, status, has_ca):
    d = pd.read_csv(buf, sep="\t")
    d.columns = [c.strip().upper() for c in d.columns]
    d = d.rename(columns={"EPEST_LOW_KG": "low_kg", "EPEST_HIGH_KG": "high_kg",
                          "STATE_FIPS_CODE": "state_fips", "COUNTY_FIPS_CODE": "county_fips",
                          "COMPOUND": "compound", "YEAR": "year"})
    d["year"] = int(year)
    d["estimate_status"] = status
    d["includes_california"] = has_ca
    return d[["compound", "year", "state_fips", "county_fips", "low_kg", "high_kg",
              "estimate_status", "includes_california"]]

frames = []
for y in range(1992, 2013):
    frames.append(read_txt(BASE / f"county-final/EPest.county.estimates.{y}.txt", y, "final", True))
for y in (2013, 2014):
    frames.append(read_txt(BASE / f"county-preliminary/EPest.county.estimates.{y}.txt", y, "preliminary", True))
for y, zname in [(2015, "2015PreliminaryEstimates.zip"), (2016, "2016PreliminaryEstimates.zip"),
                 (2017, "2017PreliminaryEstimatesNoCA.zip"), (2018, "2018PreliminaryEstimatesNoCA.zip")]:
    zp = BASE / "county-preliminary" / zname
    with zipfile.ZipFile(zp) as zf:
        member = next(n for n in zf.namelist() if n.lower().endswith(".txt"))
        with zf.open(member) as fh:
            frames.append(read_txt(io.BytesIO(fh.read()), y, "preliminary", y < 2017))

panel = pd.concat(frames, ignore_index=True)
panel.to_parquet(OUT / "pnsp_county_panel.parquet", index=False)

print(f"panel rows: {len(panel):,}   years {panel.year.min()}-{panel.year.max()}")
print(f"compounds (all years): {panel.compound.nunique()}")
print(f"memory: {panel.memory_usage(deep=True).sum()/1e6:.0f} MB")

# --- verify the California flag is real, not just a filename claim -----------
ca = panel[panel.state_fips == 6].groupby("year").size()
print("\nCalifornia (FIPS 6) rows per year -- confirms the noCA exclusion:")
for y in range(2012, 2019):
    print(f"   {y}: {ca.get(y, 0):>7,}")

# --- national totals, with comparability flags ------------------------------
nat = (panel.groupby(["year", "estimate_status", "includes_california"])
            .agg(low_kg=("low_kg", "sum"), high_kg=("high_kg", "sum"),
                 compounds=("compound", "nunique"), counties=("county_fips", "size"))
            .reset_index())
nat.to_csv(OUT / "pnsp_national_totals.csv", index=False)
print("\n=== national agricultural pesticide use, EPest high estimate ===")
print(f"{'year':<6} {'high_kg (M)':>12} {'low_kg (M)':>11} {'compounds':>10} {'status':>12} {'incl. CA':>9}")
for _, r in nat.iterrows():
    print(f"{int(r.year):<6} {r.high_kg/1e6:>12,.1f} {r.low_kg/1e6:>11,.1f} {int(r.compounds):>10} "
          f"{r.estimate_status:>12} {str(bool(r.includes_california)):>9}")
