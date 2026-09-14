"""Are children really more exposed, or is that a urine-dilution artifact?

Uncorrected urinary concentrations put children highest for every compound
measured. That is exactly the result a well-known artifact would produce:
children have less muscle mass, excrete less creatinine, and therefore show
higher concentrations of anything per millilitre of urine regardless of intake.

So the finding is tested two ways and both are reported:

  1. UNCORRECTED (ng/mL)              - what the raw panel says
  2. CREATININE-CORRECTED (ug/g)      - concentration divided by urinary
                                        creatinine, the standard adjustment for
                                        urine dilution

If the age gradient survives correction, it is about exposure. If it vanishes,
it was dilution and must not be reported as exposure. Detection FREQUENCY is
carried through as a third check, because it is unaffected by dilution at the
population level in the way a median concentration is.

The honest interpretation, either way, is bounded: urinary metabolite
concentration is an internal dose marker over roughly the last day or two. It
says exposure happened, not that harm followed.
"""
import glob
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"

def find(p):
    m = sorted(glob.glob(str(ROOT / p), recursive=True)); return m[0] if m else None
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
    return float(v[np.searchsorted(np.cumsum(w) / w.sum(), 0.5)])
def wq(v, w, q):
    v, w = np.asarray(v, float), np.asarray(w, float)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[ok], w[ok]
    if not len(v): return np.nan
    i = np.argsort(v); v, w = v[i], w[i]
    return float(v[np.searchsorted(np.cumsum(w) / w.sum(), q)])

CYC = {"_H": ("2013-2014", "DEMO_H.xpt", "ALB_CR_H.xpt"),
       "_I": ("2015-2016", "DEMO_I.xpt", "ALB_CR_I.xpt"),
       "_J": ("2017-2018", "DEMO_J.xpt", "ALB_CR_J.xpt")}
PANELS = [("Glyphosate", "SSGLYP{s}.xpt", "SSGLYP", "SSGLYPL", ["_H", "_I", "_J"]),
          ("TCPy (chlorpyrifos metabolite)", "UPHOPM{s}.xpt", "URXCPM", "URDCPMLC", ["_I", "_J"]),
          ("2,4-D", "UPHOPM{s}.xpt", "URX24D", "URD24DLC", ["_I", "_J"])]

summary = []
for label, fpat, col, lccol, sufs in PANELS:
    frames = []
    for suf in sufs:
        cycle, demofile, crfile = CYC[suf]
        d, f = xpt(find(f"data/raw/cdc-nhanes/demographics/**/{demofile}")), xpt(find(f"data/raw/cdc-nhanes/lab-and-dietary/**/{fpat.format(s=suf)}"))
        cr = xpt(find(f"data/raw/cdc-nhanes/lab-and-dietary/**/{crfile}"))
        if d is None or f is None or col not in f.columns: continue
        wt = [c for c in f.columns if c.upper().startswith("WT")][0]
        cols = ["SEQN", col, wt] + ([lccol] if lccol in f.columns else [])
        m = d[["SEQN", "RIDAGEYR", "INDFMPIR"]].merge(f[cols], on="SEQN", how="inner")
        m = m.rename(columns={col: "val", wt: "wt", lccol: "lc"})
        if cr is not None:
            crcol = next((c for c in ["URXUCR"] if c in cr.columns), None)
            if crcol:
                m = m.merge(cr[["SEQN", crcol]].rename(columns={crcol: "creat"}), on="SEQN", how="left")
        if "creat" not in m.columns: m["creat"] = np.nan
        frames.append(m)
    if not frames: continue
    df = pd.concat(frames, ignore_index=True)
    df["wt"] = df.wt / len(frames)
    df = df[(df.wt > 0) & df.val.notna()]
    # ng/mL divided by (mg/dL creatinine) -> ug per g creatinine.
    df["corrected"] = np.where(df.creat > 0, df.val / (df.creat / 100.0), np.nan)
    df["detected"] = (1 - df.lc).astype(float) if "lc" in df.columns else np.nan
    df["age_grp"] = pd.cut(df.RIDAGEYR, [0, 11, 19, 39, 59, 120],
                           labels=["3–11", "12–19", "20–39", "40–59", "60+"])

    print("\n" + "=" * 86)
    print(f"{label}   n={len(df):,}   (creatinine available for {int(df.corrected.notna().sum()):,})")
    print("=" * 86)
    print(f"   {'age':<8} {'n':>6} {'% detected':>11} {'uncorr ng/mL':>14} {'CORRECTED ug/g':>16} {'corr 95th':>11}")
    vals = {}
    for g, s in df.groupby("age_grp", observed=True):
        if len(s) < 60: continue
        det = 100 * wmean(s.detected, s.wt) if s.detected.notna().any() else np.nan
        unc, corr = wmedian(s.val, s.wt), wmedian(s.corrected, s.wt)
        p95 = wq(s.corrected, s.wt, 0.95)
        vals[str(g)] = (det, unc, corr)
        print(f"   {str(g):<8} {len(s):>6,} {det:>10.1f}% {unc:>14.3f} {corr:>16.3f} {p95:>11.3f}")
    if "3–11" in vals and "40–59" in vals:
        c_child, c_adult = vals["3–11"][2], vals["40–59"][2]
        u_child, u_adult = vals["3–11"][1], vals["40–59"][1]
        print(f"\n   children 3–11 vs adults 40–59")
        print(f"      uncorrected : {u_child:.3f} vs {u_adult:.3f}  ->  {u_child/u_adult:.2f}x")
        print(f"      CORRECTED   : {c_child:.3f} vs {c_adult:.3f}  ->  {c_child/c_adult:.2f}x")
        verdict = ("survives correction — a real exposure difference"
                   if c_child / c_adult > 1.15 else
                   "does NOT survive correction — consistent with urine dilution")
        print(f"      verdict: {verdict}")
        summary.append({"compound": label, "child_corr": c_child, "adult_corr": c_adult,
                        "ratio_corrected": c_child / c_adult, "ratio_uncorrected": u_child / u_adult,
                        "child_detect_pct": vals["3–11"][0]})

pd.DataFrame(summary).to_csv(OUT / "child_exposure_ratio.csv", index=False)
print("\n" + "=" * 86)
print("Creatinine correction divides out urine dilution. Where the child/adult ratio")
print("holds after correction, children are genuinely carrying more, not just")
print("producing more concentrated urine.")
