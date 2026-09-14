"""Iron deficiency in American women, 1999-2023, from NHANES.

Why this measure, out of everything in the lab files: iron deficiency is the
most common nutritional deficiency in the world, it lands hardest on women of
reproductive age and young children, and its consequences are not abstract --
fatigue that costs people work and study, worse pregnancy outcomes, and, in
children, cognitive effects that do not fully reverse with later repletion.
It is also cheap to fix. That combination is what makes it worth measuring.

Method notes that decide whether the numbers mean anything:

  * NHANES is a stratified, multistage probability sample with deliberate
    oversampling. An unweighted prevalence is NOT an estimate for the US
    population -- it describes who was sampled. WTMEC2YR (the examination
    weight) is applied throughout; for the 2017-2020 pre-pandemic file the
    equivalent is WTMECPRP.
  * Serum ferritin below 15 ng/mL is the conventional threshold for iron
    deficiency in women of reproductive age (WHO; CDC uses the same cut).
    Ferritin is an acute-phase reactant, so inflammation inflates it -- meaning
    this threshold UNDERCOUNTS deficiency rather than over-counting it. The
    direction of that bias matters: reported prevalence is a floor.
  * Confidence intervals here come from the weighted binomial and ignore the
    design effect, so they are NARROWER than a correct Taylor-series or
    replicate-weight interval. They indicate precision, they are not for
    formal testing. Flagged rather than silently presented.
"""
import glob, os, re
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"; OUT.mkdir(parents=True, exist_ok=True)

def find(pat):
    m = sorted(glob.glob(str(ROOT / pat), recursive=True))
    return m[0] if m else None

def xpt(p):
    return pd.read_sas(p, format="xport") if p else None

# NHANES file suffixes by cycle. The 2017-2020 pre-pandemic release uses a
# P_ prefix and its own weight variable; it is not a 2-year cycle.
CYCLES = [
    ("1999-2000", "",    "DEMO.xpt",   "LAB06.xpt"),
    ("2001-2002", "_B",  "DEMO_B.xpt", "L06_2_B.xpt"),
    ("2003-2004", "_C",  "DEMO_C.xpt", "L06TFR_C.xpt"),
    ("2005-2006", "_D",  "DEMO_D.xpt", "FERTIN_D.xpt"),
    ("2007-2008", "_E",  "DEMO_E.xpt", "FERTIN_E.xpt"),
    ("2009-2010", "_F",  "DEMO_F.xpt", "FERTIN_F.xpt"),
    ("2015-2016", "_I",  "DEMO_I.xpt", "FERTIN_I.xpt"),
    ("2017-2018", "_J",  "DEMO_J.xpt", "FERTIN_J.xpt"),
    ("2017-2020", "_P",  "P_DEMO.xpt", "P_FERTIN.xpt"),
    ("2021-2023", "_L",  "DEMO_L.xpt", "FERTIN_L.xpt"),
]

rows = []
for cycle, suf, demofile, ferfile in CYCLES:
    dp = find(f"data/raw/cdc-nhanes/demographics/**/{demofile}")
    fp = find(f"data/raw/cdc-nhanes/lab-and-dietary/**/{ferfile}")
    if not dp or not fp:
        print(f"  [skip] {cycle}: demo={bool(dp)} ferritin={bool(fp)}")
        continue
    d, f = xpt(dp), xpt(fp)
    fer_col = next((c for c in ["LBXFER"] if c in f.columns), None)
    if fer_col is None:
        print(f"  [skip] {cycle}: no LBXFER in {ferfile} (cols {list(f.columns)[:8]})")
        continue
    wt_col = "WTMECPRP" if "WTMECPRP" in d.columns else "WTMEC2YR"
    keep = ["SEQN", "RIAGENDR", "RIDAGEYR", wt_col]
    keep += [c for c in ["INDFMPIR", "RIDRETH1", "RIDRETH3"] if c in d.columns]
    m = d[keep].merge(f[["SEQN", fer_col]], on="SEQN", how="inner")
    m = m.rename(columns={wt_col: "wt", fer_col: "ferritin"})

    # Women of reproductive age, with a valid ferritin and a usable weight.
    w = m[(m.RIAGENDR == 2) & m.RIDAGEYR.between(12, 49)
          & m.ferritin.notna() & (m.wt > 0)].copy()
    if len(w) < 100:
        print(f"  [skip] {cycle}: only {len(w)} women with ferritin")
        continue
    w["deficient"] = (w.ferritin < 15).astype(int)
    pw = float(np.average(w.deficient, weights=w.wt))
    # Kish effective n, so the interval reflects weight variability at least.
    n_eff = w.wt.sum() ** 2 / (w.wt ** 2).sum()
    se = np.sqrt(max(pw * (1 - pw), 1e-12) / n_eff)
    rows.append({"cycle": cycle, "n": len(w), "n_eff": round(n_eff),
                 "pct_deficient": 100 * pw,
                 "ci_lo": 100 * max(pw - 1.96 * se, 0), "ci_hi": 100 * (pw + 1.96 * se),
                 "median_ferritin": float(np.median(w.ferritin))})
    print(f"  [ok  ] {cycle}: n={len(w):,}  ID={100*pw:.1f}%")

t = pd.DataFrame(rows)
t.to_csv(OUT / "iron_deficiency_women.csv", index=False)

print("\n=== Iron deficiency (ferritin < 15 ng/mL), US women aged 12-49 ===")
print("    survey-weighted; CIs ignore the design effect and are optimistic\n")
print(f"{'cycle':<12} {'n':>6} {'% deficient':>12} {'95% CI':>16} {'median ferritin':>16}")
print("-" * 68)
for _, r in t.iterrows():
    print(f"{r.cycle:<12} {int(r.n):>6,} {r.pct_deficient:>11.1f}% "
          f"{f'{r.ci_lo:.1f}–{r.ci_hi:.1f}':>16} {r.median_ferritin:>16.1f}")

if len(t) >= 2:
    a, b = t.iloc[0], t.iloc[-1]
    print(f"\n   {a.cycle} -> {b.cycle}: {a.pct_deficient:.1f}% -> {b.pct_deficient:.1f}% "
          f"({b.pct_deficient - a.pct_deficient:+.1f} points)")
    print(f"   median ferritin {a.median_ferritin:.1f} -> {b.median_ferritin:.1f} ng/mL "
          f"({100*(b.median_ferritin-a.median_ferritin)/a.median_ferritin:+.0f}%)")
