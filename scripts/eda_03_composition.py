"""Total applied mass is flat since 1992. So what actually changed?

If aggregate poundage is the metric, there is no story here -- and any argument
built on "we use more and more pesticide" fails on this data. The change is
compositional: which compounds, and with what properties.

All figures exclude California in every year so the series is internally
comparable (see eda_02).
"""
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
p = pd.read_parquet(OUT / "pnsp_county_panel.parquet")
p = p[p.state_fips != 6]                       # California excluded from every year

by = p.groupby(["year", "compound"]).high_kg.sum().unstack(fill_value=0) / 1e6

def show(title, s, unit="M kg"):
    print(f"\n{title}")
    for c, v in s.items():
        print(f"   {c:<26} {v:>12,.1f} {unit}")

e, l = 1992, 2018
present = by.columns[(by.loc[e] > 0) | (by.loc[l] > 0)]
delta = (by.loc[l] - by.loc[e])[present].sort_values()

show(f"BIGGEST INCREASES, {e} -> {l}", delta.nlargest(12))
show(f"BIGGEST DECREASES, {e} -> {l}", delta.nsmallest(12))

print(f"\n=== concentration of use ===")
for y in [1992, 2000, 2012, 2018]:
    row = by.loc[y].sort_values(ascending=False)
    tot = row.sum()
    print(f"   {y}: top compound = {row.index[0]:<14} {100*row.iloc[0]/tot:>5.1f}% of mass   "
          f"| top 5 = {100*row.head(5).sum()/tot:>5.1f}%   | n compounds used = {(row>0).sum()}")

print("\n=== glyphosate trajectory (excl. California) ===")
g = by["GLYPHOSATE"]
print(f"{'year':<6} {'M kg':>9} {'% of national mass':>20}")
for y in [1992, 1996, 2000, 2004, 2008, 2012, 2016, 2018]:
    print(f"{y:<6} {g.loc[y]:>9,.1f} {100*g.loc[y]/by.loc[y].sum():>19.1f}%")
print(f"   1992 -> 2018 multiple: {g.loc[2018]/g.loc[1992]:>.0f}x")

# Herbicide-resistant crop era: did the rest of the market shrink as glyphosate grew?
rest = by.drop(columns=["GLYPHOSATE"]).sum(axis=1)
print("\n=== glyphosate vs everything else (M kg, excl. California) ===")
print(f"{'year':<6} {'glyphosate':>12} {'all others':>12} {'total':>10}")
for y in [1992, 1996, 2000, 2004, 2008, 2012, 2016, 2018]:
    print(f"{y:<6} {g.loc[y]:>12,.1f} {rest.loc[y]:>12,.1f} {g.loc[y]+rest.loc[y]:>10,.1f}")
print(f"\n   glyphosate {1992}->{2018}: {g.loc[2018]-g.loc[1992]:>+8,.1f} M kg")
print(f"   all others {1992}->{2018}: {rest.loc[2018]-rest.loc[1992]:>+8,.1f} M kg")

by.to_csv(OUT / "pnsp_compound_year_matrix_noCA.csv")
print(f"\nwrote {OUT/'pnsp_compound_year_matrix_noCA.csv'}")
