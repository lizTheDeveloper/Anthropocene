"""Does water monitoring track CURRENT use, HISTORICAL use, or neither?

The naive claim -- "we monitor least what we use most" -- does not survive
testing: across 18 compounds the rank correlation between 2018 use and WQP site
count is -0.14 (p = 0.58), i.e. no relationship.

The table hints at something more specific. Alachlor use collapsed to 0.2 M kg
yet it is monitored at 32,893 sites. Atrazine, metolachlor, simazine, alachlor
and chlorpyrifos -- all heavily monitored -- are the classic organochlorine/
triazine/chloroacetanilide targets of standard multi-residue GC-MS panels.
Glyphosate, glufosinate and paraquat -- all sparsely monitored -- each require a
dedicated method (derivatisation or LC-MS/MS) outside those panels.

Hypothesis: monitoring effort reflects ANALYTICAL METHOD AVAILABILITY and the
historical composition of monitoring panels, not present-day application.
Test it against 1992 use and against method class.
"""
from pathlib import Path
import pandas as pd
from scipy import stats as st

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
t = pd.read_csv(OUT / "use_vs_monitoring.csv")
p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")

for yr in (1992, 2000):
    u = p[p.year == yr].groupby("compound").high_kg.sum() / 1e6
    t[f"use_{yr}_Mkg"] = t.pnsp_compound.map(u).fillna(0.0)
t["peak_use_Mkg"] = t.pnsp_compound.map(
    p.groupby(["compound", "year"]).high_kg.sum().div(1e6).groupby("compound").max())

# Compounds requiring a dedicated analytical method, i.e. absent from the
# standard multi-residue GC-MS panels most monitoring programmes run.
DEDICATED = {"Glyphosate", "Glufosinate", "Paraquat"}
t["needs_dedicated_method"] = t.analyte.isin(DEDICATED)

print("=== rank correlation of WQP site count against use in each era ===")
for col in ["use_1992_Mkg", "use_2000_Mkg", "use_2018_Mkg", "peak_use_Mkg"]:
    rho, pv = st.spearmanr(t[col], t.wqp_sites)
    flag = "  <-- significant" if pv < 0.05 else ""
    print(f"   {col:<16} rho = {rho:>+6.3f}   p = {pv:>6.3f}{flag}")

print("\n=== split by whether the compound needs a dedicated analytical method ===")
for needs, grp in t.groupby("needs_dedicated_method"):
    label = "dedicated method required" if needs else "in standard multi-residue panel"
    print(f"   {label:<34} n={len(grp):>2}  median sites = {grp.wqp_sites.median():>8,.0f}  "
          f"median use = {grp.use_2018_Mkg.median():>5.1f} M kg")
a = t[t.needs_dedicated_method].wqp_sites
b = t[~t.needs_dedicated_method].wqp_sites
u_stat, pv = st.mannwhitneyu(a, b, alternative="less")
print(f"\n   Mann-Whitney (dedicated-method sites < panel sites): p = {pv:.4f}"
      f"{'  <-- significant' if pv < 0.05 else ''}")
print(f"   median sites: dedicated-method {a.median():,.0f}  vs  standard-panel {b.median():,.0f}"
      f"  ({b.median()/a.median():.1f}x)")

print("\n=== monitoring vs use divergence: most over- and under-monitored ===")
t["sites_per_Mkg"] = t.wqp_sites / t.use_2018_Mkg
print(f"{'compound':<16} {'2018 use':>9} {'1992 use':>9} {'sites':>8} {'sites/Mkg':>11}")
for _, r in t.sort_values("sites_per_Mkg", ascending=False).iterrows():
    print(f"{r.analyte:<16} {r.use_2018_Mkg:>9,.1f} {r.use_1992_Mkg:>9,.1f} {r.wqp_sites:>8,} {r.sites_per_Mkg:>11,.0f}")
t.to_csv(OUT / "use_vs_monitoring.csv", index=False)
