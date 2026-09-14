"""Is national pesticide use related to how much we monitor for it in water?

This is the claim the WQP data supports directly, without any inference about
concentration: the compounds applied in greatest quantity are not the ones the
monitoring network measures most. Use comes from PNSP (2018, California
excluded, aggregates removed); monitoring effort from the count of distinct WQP
monitoring locations that ever reported that analyte since 2000.

Monitoring sites, not detections, is the right effort measure here -- detections
depend on concentration and method sensitivity, whereas site count is a direct
measure of where the network chose to look.
"""
import glob, os
from pathlib import Path
import pandas as pd
from scipy import stats as st

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"

p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")
use2018 = p[p.year == 2018].groupby("compound").high_kg.sum() / 1e6

# WQP analyte name -> PNSP compound name.
NAME = {"Glyphosate": "GLYPHOSATE", "Atrazine": "ATRAZINE", "Metolachlor": "METOLACHLOR",
        "24D": "2,4-D", "Acetochlor": "ACETOCHLOR", "Pendimethalin": "PENDIMETHALIN",
        "Chlorothalonil": "CHLOROTHALONIL", "Trifluralin": "TRIFLURALIN",
        "Chlorpyrifos": "CHLORPYRIFOS", "Paraquat": "PARAQUAT", "Alachlor": "ALACHLOR",
        "Dicamba": "DICAMBA", "Simazine": "SIMAZINE", "Acephate": "ACEPHATE",
        "Glufosinate": "GLUFOSINATE", "Metribuzin": "METRIBUZIN",
        "Imidacloprid": "IMIDACLOPRID", "Diuron": "DIURON"}

rows = []
for f in sorted(glob.glob(str(ROOT / "data/raw/epa-usgs-wqp/*/*/results/*.csv"))):
    slug = os.path.basename(f).replace("wqp_results_", "").replace(".csv", "")
    cols = ["MonitoringLocationIdentifier", "ResultMeasureValue", "ResultDetectionConditionText"]
    d = pd.read_csv(f, low_memory=False, usecols=lambda c: c in cols)
    v = pd.to_numeric(d["ResultMeasureValue"], errors="coerce")
    pnsp = NAME.get(slug)
    rows.append({
        "analyte": slug, "pnsp_compound": pnsp,
        "use_2018_Mkg": float(use2018.get(pnsp, float("nan"))) if pnsp else float("nan"),
        "wqp_samples": len(d),
        "wqp_sites": d["MonitoringLocationIdentifier"].nunique(),
        "numeric_values": int(v.notna().sum()),
        "positive_values": int((v > 0).sum()),
    })

t = pd.DataFrame(rows).dropna(subset=["use_2018_Mkg"]).sort_values("use_2018_Mkg", ascending=False)
t["sites_per_Mkg"] = t.wqp_sites / t.use_2018_Mkg
t.to_csv(OUT / "use_vs_monitoring.csv", index=False)

print("=== national use (PNSP 2018, excl. CA) vs water-monitoring effort (WQP, 2000+) ===\n")
print(f"{'compound':<16} {'use M kg':>9} {'WQP sites':>10} {'samples':>9} {'sites/Mkg':>10}")
print("-" * 60)
for _, r in t.iterrows():
    print(f"{r.analyte:<16} {r.use_2018_Mkg:>9,.1f} {r.wqp_sites:>10,} {r.wqp_samples:>9,} {r.sites_per_Mkg:>10,.0f}")

x, y = t.use_2018_Mkg, t.wqp_sites
rho, pv = st.spearmanr(x, y)
print(f"\nSpearman rank correlation, use vs monitoring sites: rho = {rho:+.3f}  (p = {pv:.3f}, n = {len(t)})")
print("A positive rho would mean we monitor most what we use most.")

top = t.nlargest(3, "use_2018_Mkg"); bot = t.nsmallest(3, "use_2018_Mkg")
print(f"\n  3 most-used compounds  : {top.wqp_sites.mean():>8,.0f} sites on average "
      f"({top.use_2018_Mkg.mean():.1f} M kg avg use)")
print(f"  3 least-used compounds : {bot.wqp_sites.mean():>8,.0f} sites on average "
      f"({bot.use_2018_Mkg.mean():.1f} M kg avg use)")

g = t[t.analyte == "Glyphosate"].iloc[0]; a = t[t.analyte == "Atrazine"].iloc[0]
print(f"\n  glyphosate: {g.use_2018_Mkg:.1f} M kg used, {g.wqp_sites:,} sites")
print(f"  atrazine  : {a.use_2018_Mkg:.1f} M kg used, {a.wqp_sites:,} sites")
print(f"  -> glyphosate is used {g.use_2018_Mkg/a.use_2018_Mkg:.1f}x as much and monitored at "
      f"{100*g.wqp_sites/a.wqp_sites:.0f}% as many sites.")
