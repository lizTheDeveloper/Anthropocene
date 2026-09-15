"""Is the apparent 2016->2018 decline in national pesticide use real?

The naive series falls from 544.6M kg (2016) to 489.5M kg (2018). Two known
artifacts could produce that without any change in the field:
  * 2017-18 exclude California entirely.
  * The compound roster shrinks from 407 compounds to 333.

Test: rebuild the series on a like-for-like basis -- California dropped from
EVERY year, and restricted to the compounds surveyed in every year -- and see
what survives.
"""
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
p = pd.read_parquet(OUT / "pnsp_county_panel.parquet")

# 1. How much of the national total is California, in the years we can see it?
ca_share = (p[p.year.between(2012, 2016)]
            .assign(is_ca=lambda d: d.state_fips == 6)
            .groupby(["year", "is_ca"]).high_kg.sum().unstack())
ca_share["ca_pct"] = 100 * ca_share[True] / (ca_share[True] + ca_share[False])
print("=== California share of national high estimate ===")
for y, r in ca_share.iterrows():
    print(f"   {y}: CA {r[True]/1e6:>6.1f}M kg of {(r[True]+r[False])/1e6:>6.1f}M kg  = {r.ca_pct:>4.1f}%")

# 2. Drop California from every year -> removes artifact 1.
noca = p[p.state_fips != 6]

# 3. Restrict to compounds present in EVERY year -> removes artifact 2.
by_year = noca.groupby("compound").year.nunique()
n_years = noca.year.nunique()
stable = set(by_year[by_year == n_years].index)
print(f"\ncompounds in all {n_years} years: {len(stable)} of {noca.compound.nunique()}")

fixed = noca[noca.compound.isin(stable)]

naive = p.groupby("year").high_kg.sum() / 1e6
exca  = noca.groupby("year").high_kg.sum() / 1e6
both  = fixed.groupby("year").high_kg.sum() / 1e6

comp = pd.DataFrame({"naive_all": naive, "excl_CA": exca, "excl_CA_fixed_compounds": both})
comp.to_csv(OUT / "pnsp_comparability.csv")

print("\n=== national high estimate, M kg, three bases ===")
print(f"{'year':<6} {'naive':>10} {'excl CA':>10} {'excl CA + fixed roster':>24}")
for y, r in comp.iterrows():
    print(f"{y:<6} {r.naive_all:>10,.1f} {r.excl_CA:>10,.1f} {r.excl_CA_fixed_compounds:>24,.1f}")

def chg(s, a, b):
    return 100 * (s.loc[b] - s.loc[a]) / s.loc[a]

print("\n=== the 2016 -> 2018 'decline', measured three ways ===")
for name, s in [("naive (as published)", naive), ("excluding California", exca),
                ("excl. CA + fixed compound roster", both)]:
    print(f"   {name:<34} {chg(s, 2016, 2018):>+7.1f}%")

print("\n=== long-run change on the only defensible basis (excl. CA, fixed roster) ===")
for a, b in [(1992, 2018), (1992, 2012), (2012, 2018), (2008, 2018)]:
    print(f"   {a} -> {b}: {chg(both, a, b):>+7.1f}%")
