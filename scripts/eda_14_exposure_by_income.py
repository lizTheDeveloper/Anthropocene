"""Who carries the pesticide body burden? NHANES urinary metabolites by income and age.

Nutritional deficiency in the US tracks income with a clean gradient. The
question this asks is whether exposure does too, and in which direction --
because the two possibilities point at different interventions. If exposure is
concentrated among the poor, it compounds the deficiency gradient. If it is flat
or inverted, then diet composition, not contamination, is doing the work.

Weights matter more here than anywhere else in this project. The pesticide
panels are RANDOM SUBSAMPLES of the NHANES examined sample, roughly a third of
it, and each carries its OWN weight variable (WTSSBJ2Y for the glyphosate
surplus panel, WTSB2YR for the organophosphate panel). Applying the MEC weight
to a subsample is a real error that produces a confident wrong number.

Urinary concentrations also need creatinine correction in principle -- a dilute
urine reads low for reasons that have nothing to do with exposure. Where the
creatinine variable is not in the same file, results are reported uncorrected
and flagged, because an uncorrected comparison ACROSS groups is still
informative if hydration does not differ systematically by the stratifier, and
silently omitting the caveat would be worse than stating it.

Values below the limit of detection are flagged in the paired LC variable
(1 = below LOD). NHANES fills those with LOD/sqrt(2); detection FREQUENCY is
reported alongside the median because it is the more robust comparison.
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
    v, w = np.asarray(v, float), np.asarray(w, float)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.sum() else np.nan
def wmedian(v, w):
    v, w = np.asarray(v, float), np.asarray(w, float)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[ok], w[ok]
    if not len(v): return np.nan
    i = np.argsort(v); v, w = v[i], w[i]
    c = np.cumsum(w) / w.sum()
    return float(v[np.searchsorted(c, 0.5)])

# The subsample weight variable is RENAMED EVERY CYCLE -- the glyphosate panel
# alone uses WTSSCH2Y (2013-14), WTSSGL2Y (2015-16) and WTSSBJ2Y (2017-18).
# Hard-coding one name silently drops cycles, so it is detected from the file.
PANELS = [
    ("Glyphosate", "SSGLYP{s}.xpt", "SSGLYP", "SSGLYPL",
     ["2013-2014", "2015-2016", "2017-2018"], ["_H", "_I", "_J"]),
    ("TCPy (chlorpyrifos metabolite)", "UPHOPM{s}.xpt", "URXCPM", "URDCPMLC",
     ["2015-2016", "2017-2018"], ["_I", "_J"]),
    ("2,4-D", "UPHOPM{s}.xpt", "URX24D", "URD24DLC",
     ["2015-2016", "2017-2018"], ["_I", "_J"]),
]
DEMOF = {"_H": "DEMO_H.xpt", "_I": "DEMO_I.xpt", "_J": "DEMO_J.xpt"}

def weight_var(f):
    """Pick the subsample weight column; they are named WTS* and vary by cycle."""
    c = [x for x in f.columns if x.upper().startswith("WT")]
    if not c:
        raise KeyError(f"no weight variable among {list(f.columns)}")
    return c[0]

for label, fpat, col, lccol, cycles, sufs in PANELS:
    wtvar = None
    frames = []
    for cycle, suf in zip(cycles, sufs):
        d = xpt(find(f"data/raw/cdc-nhanes/demographics/**/{DEMOF[suf]}"))
        f = xpt(find(f"data/raw/cdc-nhanes/lab-and-dietary/**/{fpat.format(s=suf)}"))
        if d is None or f is None or col not in f.columns: continue
        wtvar = weight_var(f)
        cols = ["SEQN", col, wtvar] + ([lccol] if lccol in f.columns else [])
        m = d[["SEQN", "RIDAGEYR", "INDFMPIR", "RIAGENDR"]].merge(f[cols], on="SEQN", how="inner")
        m = m.rename(columns={col: "val", wtvar: "wt", lccol: "lc"})
        m["cycle"] = cycle
        frames.append(m)
    if not frames:
        print(f"\n### {label}: no data"); continue
    df = pd.concat(frames, ignore_index=True)
    df["wt"] = df.wt / len(frames)
    df = df[(df.wt > 0) & df.val.notna()]
    df["detected"] = (1 - df.lc).astype(float) if "lc" in df.columns else np.nan
    df["pir_grp"] = pd.cut(df.INDFMPIR, [0, 1.0, 2.0, 4.0, 100],
                           labels=["<1.0 (below poverty)", "1.0–1.99", "2.0–3.99", "4.0+"])

    print("\n" + "=" * 78)
    print(f"{label}  —  urinary, ng/mL, uncorrected for creatinine")
    print(f"   n = {len(df):,}   cycles: {', '.join(cycles)}   weight: {wtvar} (subsample)")
    print("=" * 78)
    overall_det = 100 * wmean(df.detected, df.wt) if df.detected.notna().any() else np.nan
    print(f"   overall detection frequency: {overall_det:.1f}%   weighted median: {wmedian(df.val, df.wt):.3f} ng/mL")

    print(f"\n   {'by family income':<24} {'n':>6} {'% detected':>11} {'median':>9}")
    for g, s in df.groupby("pir_grp", observed=True):
        if len(s) < 60: continue
        det = 100 * wmean(s.detected, s.wt) if s.detected.notna().any() else np.nan
        print(f"   {str(g):<24} {len(s):>6,} {det:>10.1f}% {wmedian(s.val, s.wt):>9.3f}")

    df["age_grp"] = pd.cut(df.RIDAGEYR, [0, 11, 19, 39, 59, 120],
                           labels=["3–11 (children)", "12–19", "20–39", "40–59", "60+"])
    print(f"\n   {'by age':<24} {'n':>6} {'% detected':>11} {'median':>9}")
    for g, s in df.groupby("age_grp", observed=True):
        if len(s) < 60: continue
        det = 100 * wmean(s.detected, s.wt) if s.detected.notna().any() else np.nan
        print(f"   {str(g):<24} {len(s):>6,} {det:>10.1f}% {wmedian(s.val, s.wt):>9.3f}")
