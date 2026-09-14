"""Who carries nutritional deficiency and pesticide exposure? NHANES, 2015-2023.

National prevalence of iron deficiency in women is flat over sixteen years. That
null is worth having, and it is also the wrong question. A stable 15% average can
sit on top of a population where one group is at 8% and another at 25%, and for
anyone in the second group the stability is not reassurance.

This asks the distributional question across three measures that bear directly
on how people live:

  ferritin  - iron deficiency: fatigue, pregnancy outcomes, child cognition
  RBC folate- folate status: neural tube defects, anaemia
  25(OH)D   - vitamin D: bone, immune function

and against two exposure measures in the SAME individuals:

  urinary glyphosate  - the most-applied herbicide in the country
  urinary TCPy        - the chlorpyrifos metabolite

Stratifiers are income (family poverty-income ratio, where 1.0 is the federal
poverty line) and age. PIR is the better axis than race here because it is the
mechanism people can actually name -- what food costs, and what work exposes you
to -- though the two are entangled in the US and the race breakdown is reported
alongside rather than instead.

Survey weights (WTMEC2YR / WTMECPRP) are applied to every prevalence. The
pesticide panels are SUBSAMPLES with their own weights (WTSSBJ2Y, WTSB2YR) and
are NOT nationally representative under the MEC weight -- using the wrong weight
on them is a real error, so each is used with its own.
"""
import glob
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"

def find(pat):
    m = sorted(glob.glob(str(ROOT / pat), recursive=True))
    return m[0] if m else None
def xpt(p): return pd.read_sas(p, format="xport") if p else None

def wmean(v, w):
    v = np.asarray(v, float); w = np.asarray(w, float)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.sum() else np.nan

# Pool the three most recent cycles for stratified cells with usable n.
CYC = [("2015-2016", "DEMO_I.xpt", "_I"), ("2017-2018", "DEMO_J.xpt", "_J"),
       ("2021-2023", "DEMO_L.xpt", "_L")]

frames = []
for cycle, demofile, suf in CYC:
    d = xpt(find(f"data/raw/cdc-nhanes/demographics/**/{demofile}"))
    if d is None: continue
    wt = "WTMECPRP" if "WTMECPRP" in d.columns else "WTMEC2YR"
    base = d[["SEQN", "RIAGENDR", "RIDAGEYR", "INDFMPIR", "RIDRETH3", wt]].rename(columns={wt: "wt"})
    base["cycle"] = cycle
    for label, fname, col in [("ferritin", f"FERTIN{suf}.xpt", "LBXFER"),
                              ("rbc_folate", f"FOLATE{suf}.xpt", "LBDRFO"),
                              ("vit_d", f"VID{suf}.xpt", "LBXVIDMS")]:
        f = xpt(find(f"data/raw/cdc-nhanes/lab-and-dietary/**/{fname}"))
        if f is not None and col in f.columns:
            base = base.merge(f[["SEQN", col]].rename(columns={col: label}), on="SEQN", how="left")
        else:
            base[label] = np.nan
    frames.append(base)

df = pd.concat(frames, ignore_index=True)
# Weights must be divided by the number of pooled cycles.
df["wt"] = df.wt / len(frames)
print(f"pooled respondents: {len(df):,} across {len(frames)} cycles")

df["pir_grp"] = pd.cut(df.INDFMPIR, [0, 1.0, 2.0, 4.0, 100],
                       labels=["<1.0 (below poverty)", "1.0–1.99", "2.0–3.99", "4.0+"])

print("\n" + "=" * 78)
print("IRON DEFICIENCY (ferritin < 15 ng/mL), women 12-49, by family income")
print("=" * 78)
w = df[(df.RIAGENDR == 2) & df.RIDAGEYR.between(12, 49) & df.ferritin.notna() & (df.wt > 0)].copy()
w["def"] = (w.ferritin < 15).astype(int)
rows = []
for g, s in w.groupby("pir_grp", observed=True):
    if len(s) < 60: continue
    p = 100 * wmean(s["def"], s.wt)
    rows.append({"group": str(g), "n": len(s), "pct": p, "median_ferritin": float(s.ferritin.median())})
    print(f"   {str(g):<24} n={len(s):>5,}   {p:>5.1f}% deficient   median ferritin {s.ferritin.median():>5.1f}")
if len(rows) >= 2:
    lo = rows[0]["pct"]; hi = rows[-1]["pct"]
    print(f"\n   poorest vs richest: {lo:.1f}% vs {hi:.1f}%  ->  {lo/hi:.2f}x")
pd.DataFrame(rows).to_csv(OUT / "iron_by_income.csv", index=False)

print("\n" + "=" * 78)
print("IRON DEFICIENCY, women 12-49, by race/ethnicity (RIDRETH3)")
print("=" * 78)
ETH = {1: "Mexican American", 2: "Other Hispanic", 3: "White non-Hispanic",
       4: "Black non-Hispanic", 6: "Asian non-Hispanic", 7: "Other/multi"}
for code, name in ETH.items():
    s = w[w.RIDRETH3 == code]
    if len(s) < 60: continue
    print(f"   {name:<24} n={len(s):>5,}   {100*wmean(s['def'], s.wt):>5.1f}% deficient")

print("\n" + "=" * 78)
print("OTHER DEFICIENCIES by income (all adults 20+)")
print("=" * 78)
a = df[(df.RIDAGEYR >= 20) & (df.wt > 0)]
for label, col, thresh, unit in [("Vitamin D deficiency (<50 nmol/L)", "vit_d", 50, "nmol/L"),
                                 ("Folate insufficiency (RBC <748 nmol/L)", "rbc_folate", 340, "ng/mL")]:
    print(f"\n   {label}")
    sub = a[a[col].notna()]
    if len(sub) < 200:
        print("      insufficient data"); continue
    for g, s in sub.groupby("pir_grp", observed=True):
        if len(s) < 60: continue
        p = 100 * wmean((s[col] < thresh).astype(int), s.wt)
        print(f"      {str(g):<24} n={len(s):>5,}   {p:>5.1f}%   median {s[col].median():>6.1f} {unit}")
