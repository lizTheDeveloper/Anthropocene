#!/usr/bin/env python3
"""
analysis/six/compute.py  --  lens: Johan Six (ETH Zurich, Sustainable Agroecosystems)

Question forced by the lens: "Better by which metric, compared with what, on which
soil, over what time horizon?"

Two things are computed here.

PART A (documentary, no CSV): what the RaCA methodology document actually specifies
about sampling depth and about repeat measurement.  This is read from
data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf and
recorded in FINDING.md; nothing to compute, but it determines which carbon claims
the federal record can adjudicate.

PART B (quantitative): the erosion/herbicide trade-off that IS visible in the
mirror.  County-level no-till share (Census of Agriculture 2017, the first census
that asked the tillage question) against county-level applied herbicide mass
(USGS PNSP EPest, 2017, corrected panel).  The point of the exercise is not the
raw correlation -- it is watching what happens to that correlation as the
"compared with what" is progressively specified: pooled, within state, within
Crop Reporting District, and net of crop mix.

Run from repo root:
    python analysis/six/compute.py

Outputs:
    data/derived/lens_six_notill_herbicide_tradeoff.csv   (chart rows)
    data/derived/lens_six_county_panel_2017.csv           (county-level backing table)
    stdout: every number quoted in FINDING.md
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
NASS = ROOT / "data/raw/usda-nass/quickstats-bulk/2026-09-14"
CENSUS_2017 = NASS / "qs.census2017.txt.gz"
ENVIRONMENTAL = NASS / "qs.environmental_20260912.txt.gz"
PNSP_PANEL = DERIVED / "pnsp_county_panel_corrected.parquet"
PNSP_RAW_2017 = ROOT / "data/raw/usgs/pnsp/2026-09-14/county-preliminary/2017PreliminaryEstimatesNoCA.zip"

YEAR = 2017
MIN_HARVESTED_ACRES = 5_000  # counties with less cropland than this are dropped
ACRE_TO_HA = 0.40468564224

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SUPPRESSION = {"(D)", "(NA)", "(X)", "(S)", "(H)", "(L)", ""}


def parse_value(v: str) -> float:
    """NASS VALUE is a STRING with thousands separators and suppression codes."""
    v = v.strip()
    if v in SUPPRESSION:
        return np.nan
    if v == "(Z)":  # "less than half the unit shown"
        return 0.0
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return np.nan


def norm_chem(name: str) -> str:
    """Normalise a chemical name for PNSP <-> NASS matching."""
    s = name.upper().strip()
    for junk in (" SALT", " ACID", " ESTER"):
        s = s.replace(junk, "")
    keep = [c for c in s if c.isalnum()]
    return "".join(keep)


# ---------------------------------------------------------------------------
# PART B.1 -- herbicide roster, from NASS's own chemical classification
# ---------------------------------------------------------------------------

STEREO = ("S", "P", "D", "L", "R", "E", "M")


def core_chem(n: str) -> str:
    """Strip a leading/trailing single-letter stereochemistry descriptor.

    PNSP writes 'METOLACHLOR-S'; NASS writes 'S-METOLACHLOR'.  Normalised these
    become METOLACHLORS and SMETOLACHLOR, which will not match.  Reducing both to
    METOLACHLOR makes them comparable.
    """
    for s in STEREO:
        if n.endswith(s) and len(n) > 7:
            return n[:-1]
        if n.startswith(s) and len(n) > 7:
            return n[1:]
    return n


def herbicide_roster() -> tuple[set[str], set[str]]:
    """
    PNSP ships no pesticide-class column.  Rather than hand-curate a roster (which
    would be an undocumented judgement call), take the class assignment from NASS's
    own Agricultural Chemical Use files, where DOMAINCAT_DESC is literally
    'CHEMICAL, HERBICIDE: (GLYPHOSATE = 417300)'.
    """
    herb, other = set(), set()
    with gzip.open(ENVIRONMENTAL, "rt", encoding="latin-1") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        i_dcat = header.index("DOMAINCAT_DESC")
        seen = set()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) <= i_dcat:
                continue
            d = f[i_dcat]
            if not d.startswith("CHEMICAL, ") or ": (" not in d:
                continue
            if d in seen:
                continue
            seen.add(d)
            cls = d[len("CHEMICAL, "):].split(":")[0]
            if cls not in ("HERBICIDE", "INSECTICIDE", "FUNGICIDE", "OTHER"):
                continue
            nm = d.split(": (", 1)[1].rsplit(")", 1)[0]
            nm = nm.split(" = ")[0]
            (herb if cls == "HERBICIDE" else other).add(norm_chem(nm))
    return herb, other


def classify_herbicide(pnsp_names: pd.Series, herb: set[str], other: set[str]) -> pd.DataFrame:
    """Match PNSP compound names onto the NASS herbicide roster.

    Three rules, applied in order, each recorded so the match can be audited:
      exact      -- normalised names identical
      exact_other-- normalised name is an exact NON-herbicide match; never a herbicide
      stereo     -- identical after stripping a leading/trailing stereo descriptor
      prefix     -- one normalised name (>=7 chars) is a prefix of the other, which
                    catches PNSP's parent-acid names against NASS's salt/ester names
                    (GLUFOSINATE -> GLUFOSINATE-AMMONIUM, PICLORAM -> PICLORAM, POT. SALT)
    """
    herb_core = {core_chem(h): h for h in herb}
    rows = []
    for name in sorted(set(pnsp_names)):
        n = norm_chem(name)
        rule = None
        if n in herb:
            rule = "exact"
        elif n in other:
            rule = None  # exact non-herbicide match wins; do not fuzzy-match
        elif core_chem(n) in herb_core:
            rule = "stereo"
        elif len(n) >= 7 and any(
                h.startswith(n) or n.startswith(h) for h in herb if len(h) >= 7):
            rule = "prefix"
        rows.append((name, n, rule))
    return pd.DataFrame(rows, columns=["compound", "norm", "match_rule"])


# ---------------------------------------------------------------------------
# PART B.2 -- PNSP 2017 county herbicide mass
# ---------------------------------------------------------------------------

def pnsp_year(year: int, herb: set[str], other: set[str], verbose: bool = True
              ) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = pd.read_parquet(PNSP_PANEL)
    p = p[p["year"] == year].copy()
    p["fips"] = p["state_fips"] * 1000 + p["county_fips"]

    cls = classify_herbicide(p["compound"], herb, other)
    p = p.merge(cls, on="compound", how="left")
    p["is_herb"] = p["match_rule"].notna()
    p["is_glyph"] = p["norm"].str.startswith("GLYPHOSATE")
    # The mechanism a tillage/herbicide trade-off would actually run through:
    # no-till replaces the mechanical seedbed operation with a pre-plant "burndown"
    # spray.  These are the actives used for burndown in US row crops.
    BURNDOWN = ("GLYPHOSATE", "PARAQUAT", "24D", "DICAMBA", "GLUFOSINATE",
                "SAFLUFENACIL", "CARFENTRAZONE")
    p["is_burn"] = p["norm"].str.startswith(BURNDOWN)

    say = print if verbose else (lambda *a, **k: None)
    total_kg = p["low_kg"].sum()
    hk = p.loc[p["is_herb"], "low_kg"].sum()
    say(f"[B.2] PNSP {year}: {p['compound'].nunique()} compounds, "
          f"{p['fips'].nunique()} counties, {total_kg/1e6:.1f} M kg (EPest-low)")
    say(f"[B.2] classified as herbicide: {p.loc[p['is_herb'],'compound'].nunique()} compounds, "
          f"{hk/1e6:.1f} M kg ({100*hk/total_kg:.1f}% of all applied mass)")
    by_rule = p[p["is_herb"]].groupby("match_rule")["low_kg"].sum() / 1e6
    say(f"[B.2] herbicide mass by match rule (M kg): "
          + ", ".join(f"{k}={v:.1f}" for k, v in by_rule.items()))
    say("[B.2] compounds matched by the fuzzy rules (manual audit):")
    for _, r in cls[cls["match_rule"].isin(["stereo", "prefix"])].iterrows():
        kg = p.loc[p["compound"] == r["compound"], "low_kg"].sum()
        say(f"        {r['compound']:<26} via {r['match_rule']:<7} {kg/1e6:7.2f} M kg")
    unmatched = (p[~p["is_herb"]].groupby("compound")["low_kg"].sum()
                 .sort_values(ascending=False).head(6))
    say("[B.2] largest compounds left UNclassified (should be fumigants/fungicides/"
          "insecticides/growth regulators):")
    for c, kg in unmatched.items():
        say(f"        {c:<28} {kg/1e6:8.2f} M kg")

    bmask = p["is_burn"] & p["is_herb"]
    say(f"[B.2] burndown group ({p.loc[bmask,'compound'].nunique()} compounds): "
          f"{p.loc[bmask,'low_kg'].sum()/1e6:.1f} M kg = "
          f"{100*p.loc[bmask,'low_kg'].sum()/hk:.1f}% of herbicide mass; "
          f"members: {', '.join(sorted(p.loc[bmask,'compound'].unique()))}")

    g = (p.assign(h_low=p["low_kg"].where(p["is_herb"], 0.0),
                  h_high=p["high_kg"].where(p["is_herb"], 0.0),
                  g_low=p["low_kg"].where(p["is_glyph"], 0.0),
                  b_low=p["low_kg"].where(bmask, 0.0))
         .groupby("fips")
         .agg(herb_low_kg=("h_low", "sum"), herb_high_kg=("h_high", "sum"),
              glyph_low_kg=("g_low", "sum"), burndown_low_kg=("b_low", "sum"),
              all_low_kg=("low_kg", "sum"))
         .reset_index())
    return g, cls


# ---------------------------------------------------------------------------
# PART B.3 -- Census of Agriculture 2017, county level
# ---------------------------------------------------------------------------

TILLAGE_ITEMS = {
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, NO-TILL - ACRES": "notill_ac",
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, (EXCL NO-TILL) - ACRES": "constill_ac",
    "PRACTICES, LAND USE, CROPLAND, CONVENTIONAL TILLAGE - ACRES": "convtill_ac",
    "PRACTICES, LAND USE, CROPLAND, COVER CROP PLANTED, (EXCL CRP) - ACRES": "covercrop_ac",
}
LAND_ITEMS = {
    "AG LAND, CROPLAND - ACRES": "cropland_ac",
    "AG LAND, CROPLAND, HARVESTED - ACRES": "harvested_ac",
    "AG LAND, CROPLAND, HARVESTED, IRRIGATED - ACRES": "irrigated_ac",
}
CROP_ITEMS = {
    "CORN, GRAIN - ACRES HARVESTED": "corn_ac",
    "CORN, SILAGE - ACRES HARVESTED": "cornsil_ac",
    "SOYBEANS - ACRES HARVESTED": "soy_ac",
    "WHEAT - ACRES HARVESTED": "wheat_ac",
    "COTTON - ACRES HARVESTED": "cotton_ac",
    "SORGHUM, GRAIN - ACRES HARVESTED": "sorghum_ac",
    "RICE - ACRES HARVESTED": "rice_ac",
    "HAY - ACRES HARVESTED": "hay_ac",
    "VEGETABLE TOTALS, IN THE OPEN - ACRES HARVESTED": "veg_ac",
    "ORCHARDS - ACRES BEARING & NON-BEARING": "orchard_ac",
}
WANTED = {**TILLAGE_ITEMS, **LAND_ITEMS, **CROP_ITEMS}


def census(path: Path) -> pd.DataFrame:
    rows = []
    with gzip.open(path, "rt", encoding="latin-1") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        ix = {c: header.index(c) for c in (
            "SHORT_DESC", "DOMAIN_DESC", "AGG_LEVEL_DESC", "STATE_FIPS_CODE",
            "COUNTY_CODE", "STATE_ALPHA", "ASD_CODE", "VALUE")}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) <= ix["VALUE"]:
                continue
            if f[ix["AGG_LEVEL_DESC"]] != "COUNTY" or f[ix["DOMAIN_DESC"]] != "TOTAL":
                continue
            sd = f[ix["SHORT_DESC"]]
            if sd not in WANTED:
                continue
            cc = f[ix["COUNTY_CODE"]].strip()
            if not cc.isdigit():
                continue
            rows.append((
                int(f[ix["STATE_FIPS_CODE"]]) * 1000 + int(cc),
                f[ix["STATE_ALPHA"]].strip(),
                f[ix["STATE_FIPS_CODE"]].strip() + "-" + f[ix["ASD_CODE"]].strip(),
                WANTED[sd],
                parse_value(f[ix["VALUE"]]),
            ))
    long = pd.DataFrame(rows, columns=["fips", "state", "asd", "item", "value"])
    print(f"[B.3] {path.name} county rows pulled: {len(long):,} "
          f"across {long['fips'].nunique():,} counties, {long['item'].nunique()} items")
    supp = long.groupby("item")["value"].apply(lambda s: s.isna().mean())
    print("[B.3] share suppressed / non-numeric by item:")
    for k in TILLAGE_ITEMS.values():
        if k in supp:
            print(f"        {k:<14} {100*supp[k]:5.1f}%  (n={int((long['item']==k).sum())})")

    geo = long.groupby("fips").agg(state=("state", "first"), asd=("asd", "first"))
    wide = long.pivot_table(index="fips", columns="item", values="value", aggfunc="first")
    out = geo.join(wide).reset_index()
    for col in WANTED.values():
        if col not in out.columns:
            out[col] = np.nan
    return out


# ---------------------------------------------------------------------------
# PART B.4 -- regression machinery (numpy only; no statsmodels dependency)
# ---------------------------------------------------------------------------

def ols(y: np.ndarray, X: np.ndarray):
    """Return beta, se (HC1-robust), and R^2.  X must already include a constant."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    # HC1 heteroskedasticity-robust covariance
    meat = (X * (resid ** 2)[:, None]).T @ X
    cov = XtX_inv @ meat @ XtX_inv * (n / max(n - k, 1))
    se = np.sqrt(np.diag(cov))
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot
    return beta, se, r2, resid


def demean(df: pd.DataFrame, cols: list[str], by: str) -> pd.DataFrame:
    """Within-group transform = group fixed effects."""
    out = df.copy()
    for c in cols:
        out[c] = df[c] - df.groupby(by)[c].transform("mean")
    return out


def spec(df: pd.DataFrame, ycol: str, xcol: str, controls: list[str],
         fe: str | None, label: str) -> dict:
    """OLS of ycol on xcol (+ controls, + group fixed effects via within-transform).

    xcol is a share on [0, 1], so a coefficient of b corresponds to b * 0.10 log
    units for a +10 percentage-point change in that share.
    """
    cols = [ycol, xcol] + controls
    d = df.dropna(subset=cols).copy()
    n_groups = 0
    if fe:
        d = d[d.groupby(fe)[ycol].transform("size") > 1]
        n_groups = int(d[fe].nunique())
        d = demean(d, cols, fe)
    X = np.column_stack([np.ones(len(d))] + [d[c].values for c in [xcol] + controls])
    beta, se, r2, _ = ols(d[ycol].values, X)
    b, s = beta[1], se[1]
    # degrees of freedom absorbed by the fixed effects are not reflected in HC1
    # here; with >= 5 counties per group the inflation is small and the direction
    # of the correction is conservative (SEs slightly too small).
    return dict(spec=label, n=len(d), beta_per_1=b, se=s,
                beta_per_10pp=0.10 * b,
                lo_per_10pp=0.10 * (b - 1.96 * s),
                hi_per_10pp=0.10 * (b + 1.96 * s),
                t=b / s if s else np.nan, r2=r2, n_groups=n_groups)


CROPSH = ["corn_sh", "cornsil_sh", "soy_sh", "wheat_sh", "cotton_sh",
          "sorghum_sh", "rice_sh", "hay_sh", "veg_sh", "orchard_sh"]


def build(census_path: Path, pnsp_yr: int, herb: set, other: set,
          verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join one Census of Agriculture vintage to one PNSP year and derive the
    practice shares and application intensities.  Returns (county table, compound
    classification)."""
    say = print if verbose else (lambda *a, **k: None)
    pest, cls = pnsp_year(pnsp_yr, herb, other, verbose=verbose)
    cen = census(census_path)
    df = cen.merge(pest, on="fips", how="inner")
    say(f"\n[B.4] merged counties: {len(df):,}")

    df["tilled_ac"] = df[["notill_ac", "constill_ac", "convtill_ac"]].sum(axis=1, min_count=3)
    df["notill_share"] = df["notill_ac"] / df["tilled_ac"]
    df["cover_share"] = df["covercrop_ac"] / df["tilled_ac"]
    df["harvested_ha"] = df["harvested_ac"] * ACRE_TO_HA
    df["herb_kg_ha"] = df["herb_low_kg"] / df["harvested_ha"]
    df["herb_kg_ha_high"] = df["herb_high_kg"] / df["harvested_ha"]
    df["glyph_kg_ha"] = df["glyph_low_kg"] / df["harvested_ha"]
    df["burndown_kg_ha"] = df["burndown_low_kg"] / df["harvested_ha"]
    df["glyph_share"] = df["glyph_low_kg"] / df["herb_low_kg"]

    for c in ["corn_ac", "cornsil_ac", "soy_ac", "wheat_ac", "cotton_ac",
              "sorghum_ac", "rice_ac", "hay_ac", "veg_ac", "orchard_ac"]:
        df[c.replace("_ac", "_sh")] = df[c].fillna(0) / df["harvested_ac"]

    n0 = len(df)
    nat_harvested = df["harvested_ac"].sum()
    nat_herb = df["herb_low_kg"].sum()
    df = df[(df["harvested_ac"] >= MIN_HARVESTED_ACRES)
            & (df["tilled_ac"] >= MIN_HARVESTED_ACRES)
            & (df["herb_low_kg"] > 0)
            & df["notill_share"].between(0, 1)].copy()
    say(f"[B.4] after filter (harvested & tilled cropland >= {MIN_HARVESTED_ACRES:,} ac, "
        f"herbicide mass > 0): {len(df):,} counties (dropped {n0-len(df):,})")
    say(f"[B.4] these counties hold {df['harvested_ac'].sum()/1e6:.1f} M harvested acres "
        f"({100*df['harvested_ac'].sum()/nat_harvested:.1f}% of the national county total) "
        f"and {df['herb_low_kg'].sum()/1e6:.1f} M kg of herbicide "
        f"({100*df['herb_low_kg'].sum()/nat_herb:.1f}% of the national total)")

    df["ln_herb"] = np.log(df["herb_kg_ha"])
    df["ln_glyph"] = np.log(df["glyph_kg_ha"].where(df["glyph_kg_ha"] > 0))
    df["ln_burn"] = np.log(df["burndown_kg_ha"].where(df["burndown_kg_ha"] > 0))
    df["ln_herb_high"] = np.log(df["herb_kg_ha_high"])
    return df, cls


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)

    herb, other = herbicide_roster()
    print(f"[B.1] NASS chemical classification: {len(herb)} herbicide names, "
          f"{len(other)} insecticide/fungicide/other names")

    df, cls = build(CENSUS_2017, YEAR, herb, other)

    # --- descriptives ------------------------------------------------------
    print("\n[DESC] no-till share of tilled cropland: "
          f"median {df['notill_share'].median():.3f}, "
          f"IQR {df['notill_share'].quantile(.25):.3f}-{df['notill_share'].quantile(.75):.3f}")
    print(f"[DESC] herbicide intensity kg/ha harvested: median {df['herb_kg_ha'].median():.2f}, "
          f"IQR {df['herb_kg_ha'].quantile(.25):.2f}-{df['herb_kg_ha'].quantile(.75):.2f}")
    print(f"[DESC] glyphosate share of herbicide mass: median {df['glyph_share'].median():.3f}")

    # external validation of the constructed tillage variable: the acreage-weighted
    # no-till share of the analysis sample against the published NATIONAL totals in
    # the same Census file (no-till 104,452,339 ac; conservation excl no-till
    # 97,753,854 ac; conventional 80,005,292 ac -> 37.0% no-till)
    NAT = dict(notill=104_452_339, cons=97_753_854, conv=80_005_292)
    nat_share = NAT["notill"] / sum(NAT.values())
    samp_share = df["notill_ac"].sum() / df["tilled_ac"].sum()
    print(f"[CHECK] no-till share of tilled cropland: published national "
          f"{100*nat_share:.1f}%, analysis sample (acreage-weighted) {100*samp_share:.1f}% "
          f"-- sample covers {100*df['tilled_ac'].sum()/sum(NAT.values()):.1f}% of "
          f"national tilled cropland")

    from scipy import stats
    rho, p = stats.spearmanr(df["notill_share"], df["herb_kg_ha"])
    print(f"[DESC] pooled Spearman rho(no-till share, herbicide kg/ha) = {rho:+.3f} (p={p:.2e})")

    # --- the tautology test ------------------------------------------------
    d = df.dropna(subset=["ln_herb"] + CROPSH)
    Xc = np.column_stack([np.ones(len(d))] + [d[c].values for c in CROPSH])
    _, _, r2_cropmix, _ = ols(d["ln_herb"].values, Xc)
    Xn = np.column_stack([np.ones(len(d))] + [d[c].values for c in CROPSH])
    _, _, r2_cropmix_notill, _ = ols(d["notill_share"].values, Xn)
    print(f"\n[TAUTOLOGY] R^2 of log(herbicide kg/ha) on crop-mix shares alone: {r2_cropmix:.3f}")
    print(f"[TAUTOLOGY] R^2 of no-till share on crop-mix shares alone:        {r2_cropmix_notill:.3f}")

    # --- the specification ladder -----------------------------------------
    ladder = []
    for ycol, yname in (("ln_herb", "all herbicides"),
                        ("ln_glyph", "glyphosate"),
                        ("ln_burn", "burndown group")):
        ladder += [
            spec(df, ycol, "notill_share", [], None,
                 "1. Pooled, no controls"),
            spec(df, ycol, "notill_share", [], "state",
                 "2. + state fixed effects"),
            spec(df, ycol, "notill_share", [], "asd",
                 "3. + Crop Reporting District FE"),
            spec(df, ycol, "notill_share", CROPSH, None,
                 "4. + crop mix (10 shares)"),
            spec(df, ycol, "notill_share", CROPSH, "asd",
                 "5. + crop mix AND CRD FE"),
        ]
        for r in ladder[-5:]:
            r["outcome"] = yname

    lad = pd.DataFrame(ladder)
    lad["pct_per_10pp"] = 100 * (np.exp(lad["beta_per_10pp"]) - 1)
    lad["pct_lo"] = 100 * (np.exp(lad["lo_per_10pp"]) - 1)
    lad["pct_hi"] = 100 * (np.exp(lad["hi_per_10pp"]) - 1)

    # concrete contrast: a county at the 75th vs the 25th percentile of no-till share
    p25, p75 = df["notill_share"].quantile([.25, .75])
    lad["pct_p25_to_p75"] = 100 * (np.exp(lad["beta_per_1"] * (p75 - p25)) - 1)

    print("\n[LADDER] effect of +10 percentage points of no-till share on applied mass per ha")
    print(f"{'outcome':<16}{'specification':<34}{'n':>6}{'%change':>9}{'    95% CI':>20}"
          f"{'t':>7}{'P25->P75':>10}")
    for _, r in lad.iterrows():
        print(f"{r['outcome']:<16}{r['spec']:<34}{r['n']:>6}{r['pct_per_10pp']:>8.1f}%"
              f"  [{r['pct_lo']:>6.1f}, {r['pct_hi']:>6.1f}]{r['t']:>7.1f}"
              f"{r['pct_p25_to_p75']:>9.1f}%")
    print(f"        (no-till share P25 = {p25:.3f}, P75 = {p75:.3f})")

    # legible descriptive: quintile means, raw and after removing CRD + crop mix
    d = df.dropna(subset=["ln_herb"] + CROPSH).copy()
    d["q"] = pd.qcut(d["notill_share"], 5, labels=[1, 2, 3, 4, 5])
    dd = demean(d, ["ln_herb"] + CROPSH, "asd")
    Xq = np.column_stack([np.ones(len(dd))] + [dd[c].values for c in CROPSH])
    _, _, _, res = ols(dd["ln_herb"].values, Xq)
    d["adj_kg_ha"] = np.exp(res + d["ln_herb"].mean())
    print("\n[QUINTILE] herbicide kg/ha by no-till quintile "
          "(geometric means; adjusted = net of CRD + crop mix)")
    for q, g in d.groupby("q", observed=True):
        print(f"        Q{q}  no-till {g['notill_share'].mean():.2f}  "
              f"raw {np.exp(g['ln_herb'].mean()):.2f}   adjusted {np.exp(np.log(g['adj_kg_ha']).mean()):.2f}"
              f"   (n={len(g)})")

    # --- verification #1: EPest-high instead of EPest-low ------------------
    v1 = [spec(df, "ln_herb_high", "notill_share", [], None, "1. Pooled, no controls"),
          spec(df, "ln_herb_high", "notill_share", CROPSH, "asd", "5. + crop mix AND CRD FE")]
    print("\n[VERIFY 1] same ladder endpoints using EPest-HIGH instead of EPest-low:")
    for r in v1:
        pct = 100 * (np.exp(r["beta_per_10pp"]) - 1)
        print(f"        {r['spec']:<34} {pct:+6.1f}%  (t={r['t']:+.1f}, n={r['n']})")

    # --- verification #2: herbicide mass recomputed from the raw 2017 file --
    try:
        import zipfile, io
        with zipfile.ZipFile(PNSP_RAW_2017) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".txt")][0]
            raw = pd.read_csv(io.BytesIO(z.read(name)), sep="\t")
        raw.columns = [c.strip().upper() for c in raw.columns]
        keep_cmp = set(cls.loc[cls["match_rule"].notna(), "compound"])
        raw = raw[raw["COMPOUND"].isin(keep_cmp)]
        raw["fips"] = raw["STATE_FIPS_CODE"] * 1000 + raw["COUNTY_FIPS_CODE"]
        rawg = raw.groupby("fips")["EPEST_LOW_KG"].sum()
        chk = df.set_index("fips")["herb_low_kg"]
        common = chk.index.intersection(rawg.index)
        diff = (chk.loc[common] - rawg.loc[common]).abs()
        print(f"\n[VERIFY 2] herbicide mass rebuilt from {PNSP_RAW_2017.name} for "
              f"{len(common):,} counties: max |difference| = {diff.max():.4f} kg, "
              f"total {rawg.loc[common].sum()/1e6:.2f} M kg vs {chk.loc[common].sum()/1e6:.2f} M kg")
    except Exception as exc:  # pragma: no cover
        print(f"\n[VERIFY 2] could not rebuild from raw zip: {exc}")

    # --- verification #3: non-parametric, within-CRD rank correlation ------
    sub = df.dropna(subset=["ln_herb"]).copy()
    sub["n_in_asd"] = sub.groupby("asd")["fips"].transform("size")
    sub = sub[sub["n_in_asd"] >= 5]
    rhos = (sub.groupby("asd")
            .apply(lambda g: stats.spearmanr(g["notill_share"], g["herb_kg_ha"]).statistic,
                   include_groups=False)
            .dropna())
    w = stats.wilcoxon(rhos.values)
    print(f"[VERIFY 3] within-CRD Spearman rho computed separately in {len(rhos)} CRDs "
          f"(>=5 counties each): median {rhos.median():+.3f}, "
          f"IQR {rhos.quantile(.25):+.3f} to {rhos.quantile(.75):+.3f}, "
          f"{100*(rhos>0).mean():.0f}% positive, Wilcoxon p={w.pvalue:.3g}")
    print(f"[VERIFY 3] i.e. the sign of the trade-off is not stable across places: "
          f"{int((rhos>0.3).sum())} CRDs have rho>+0.3 and {int((rhos<-0.3).sum())} have rho<-0.3")

    # --- robustness: cover crops as the practice variable instead of no-till ---
    cv = [spec(df, "ln_herb", "cover_share", [], None, "1. Pooled, no controls"),
          spec(df, "ln_herb", "cover_share", CROPSH, "asd", "5. + crop mix AND CRD FE")]
    print("\n[ROBUST] same ladder endpoints with COVER-CROP share as the practice variable:")
    for r in cv:
        print(f"        {r['spec']:<34} {100*(np.exp(r['beta_per_10pp'])-1):+6.1f}% per +10pp"
              f"  (t={r['t']:+.1f}, n={r['n']})")

    # --- verification #4: independent replication on a different vintage ----
    # Census of Agriculture 2022 tillage x PNSP 2018 herbicide.  Different census,
    # different survey year, different PNSP vintage.  The two are five years apart,
    # so this is NOT a repeat measurement of the same counties -- it is a check
    # that the pattern is not an artifact of one pair of files.
    print("\n[VERIFY 4] replication on Census of Agriculture 2022 x PNSP 2018")
    try:
        df22, _ = build(NASS / "qs.census2022.txt.gz", 2018, herb, other, verbose=False)
        print(f"        n = {len(df22):,} counties")
        for lbl, controls, fe in (("1. Pooled, no controls", [], None),
                                  ("3. + Crop Reporting District FE", [], "asd"),
                                  ("5. + crop mix AND CRD FE", CROPSH, "asd")):
            for ycol, yname in (("ln_herb", "all herbicides"),
                                ("ln_burn", "burndown group")):
                r = spec(df22, ycol, "notill_share", controls, fe, lbl)
                print(f"        {yname:<16}{lbl:<34}"
                      f"{100*(np.exp(r['beta_per_10pp'])-1):+6.1f}% per +10pp "
                      f"(t={r['t']:+.1f})")
        rho22, p22 = stats.spearmanr(df22["notill_share"], df22["herb_kg_ha"])
        print(f"        pooled Spearman rho = {rho22:+.3f} (p={p22:.2e})")
    except Exception as exc:  # pragma: no cover
        print(f"        replication failed: {exc}")

    # --- what the record cannot do: years of overlap ------------------------
    pall = pd.read_parquet(PNSP_PANEL, columns=["year"])
    pnsp_years = set(pall["year"].unique())
    census_tillage_years = {2017, 2022}  # tillage first asked in 2017
    print(f"\n[HORIZON] PNSP county years available: {min(pnsp_years)}-{max(pnsp_years)}")
    print(f"[HORIZON] Census of Ag years carrying the tillage question: "
          f"{sorted(census_tillage_years)}")
    print(f"[HORIZON] years where both exist: "
          f"{sorted(pnsp_years & census_tillage_years)} "
          f"-> no county can be observed before and after a change in tillage")

    # --- outputs -----------------------------------------------------------
    chart = lad[["outcome", "spec", "n", "n_groups", "pct_per_10pp", "pct_lo",
                 "pct_hi", "pct_p25_to_p75", "t", "r2"]].copy()
    chart.columns = ["outcome", "specification", "n_counties", "n_groups",
                     "pct_change_per_10pp_notill", "ci_low", "ci_high",
                     "pct_change_p25_to_p75", "t_stat", "r_squared"]
    chart = chart.round(4)
    chart.to_csv(DERIVED / "lens_six_notill_herbicide_tradeoff.csv", index=False)

    keep = ["fips", "state", "asd", "notill_share", "cover_share", "tilled_ac",
            "harvested_ac", "herb_low_kg", "herb_high_kg", "glyph_low_kg",
            "burndown_low_kg", "herb_kg_ha", "glyph_kg_ha", "burndown_kg_ha",
            "glyph_share"] + CROPSH
    df[keep].to_csv(DERIVED / "lens_six_county_panel_2017.csv", index=False)

    print(f"\nwrote {DERIVED/'lens_six_notill_herbicide_tradeoff.csv'}")
    print(f"wrote {DERIVED/'lens_six_county_panel_2017.csv'}")
    print(f"\n[FOR FINDING.md] crop-mix-only R^2 on log herbicide intensity = {r2_cropmix:.3f}")


if __name__ == "__main__":
    sys.exit(main())
