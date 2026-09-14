"""The defensible national pesticide-use series, with all three corrections applied.

Three artifacts, each of which alone is enough to produce a wrong trend:

  1. CALIFORNIA is absent from 2017-18 (USGS substitutes CA DPR PUR there).
     California is 12-13% of national mass, so the published 2016->2018 fall is
     mostly this. Fix: drop California from every year.
  2. AGGREGATE DOUBLE-COUNTING. From 2016 PNSP publishes "METOLACHLOR &
     METOLACHLOR-S" and "DIMETHENAMID & DIMETHENAMID-P" ALONGSIDE their
     components. The aggregate equals the component sum exactly (ratio 1.000),
     so naive summation inflates 2016-18 by 8-9%. Fix: drop the aggregate rows.
  3. A CHANGING COMPOUND ROSTER (270 compounds in 1992, 332 in 2018) means part
     of any rise is simply more things being surveyed. Reported as a sensitivity
     rather than a correction, because restricting to the stable roster discards
     real new chemistry.

Everything downstream should use `pnsp_national_corrected.csv` from this script,
not a fresh groupby over the raw panel.
"""
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
AGGREGATES = ["METOLACHLOR & METOLACHLOR-S", "DIMETHENAMID & DIMETHENAMID-P"]

p = pd.read_parquet(OUT / "pnsp_county_panel.parquet")
p = p[(p.state_fips != 6) & (~p.compound.isin(AGGREGATES))]
p.to_parquet(OUT / "pnsp_county_panel_corrected.parquet", index=False)

by = p.groupby(["year", "compound"]).high_kg.sum().unstack(fill_value=0) / 1e6
tot = by.sum(axis=1)

n_years = p.year.nunique()
stable = by.columns[(by > 0).sum() == n_years]
tot_stable = by[stable].sum(axis=1)

out = pd.DataFrame({
    "total_high_Mkg": tot,
    "total_high_Mkg_stable_roster": tot_stable,
    "n_compounds": (by > 0).sum(axis=1),
    "glyphosate_Mkg": by["GLYPHOSATE"],
    "glyphosate_pct": 100 * by["GLYPHOSATE"] / tot,
})
out.index.name = "year"
out.to_csv(OUT / "pnsp_national_corrected.csv")

print("=== CORRECTED national agricultural pesticide use ===")
print("    (California excluded from every year; aggregate rows removed)\n")
print(f"{'year':<6} {'total M kg':>11} {'stable roster':>14} {'n cmpd':>7} {'glyphosate':>11} {'glyp %':>7}")
for y, r in out.iterrows():
    print(f"{y:<6} {r.total_high_Mkg:>11,.1f} {r.total_high_Mkg_stable_roster:>14,.1f} "
          f"{int(r.n_compounds):>7} {r.glyphosate_Mkg:>11,.1f} {r.glyphosate_pct:>6.1f}%")

def pct(s, a, b): return 100 * (s.loc[b] - s.loc[a]) / s.loc[a]

print("\n=== headline changes, corrected basis ===")
for a, b in [(1992, 2018), (1992, 2012), (2008, 2018), (2012, 2018), (2016, 2018)]:
    print(f"   total mass   {a} -> {b}: {pct(tot, a, b):>+7.1f}%   "
          f"| stable roster: {pct(tot_stable, a, b):>+7.1f}%")

print("\n=== what the correction changes about the published story ===")
naive = pd.read_parquet(OUT / "pnsp_county_panel.parquet").groupby("year").high_kg.sum() / 1e6
print(f"   2016->2018 as published (all rows, CA missing 2017-18): {pct(naive, 2016, 2018):>+6.1f}%")
print(f"   2016->2018 corrected                                  : {pct(tot,   2016, 2018):>+6.1f}%")
print("   The published series implies a fall. Corrected, use is flat to slightly down,")
print("   and the apparent fall is an artifact of California's absence plus double-counting.")
