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

def herbicide_roster() -> set[str]:
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
    # a name classified as a herbicide anywhere wins; a handful of actives are
    # registered in more than one class (e.g. some growth regulators)
    return herb


# ---------------------------------------------------------------------------
# PART B.2 -- PNSP 2017 county herbicide mass
# ---------------------------------------------------------------------------

def pnsp_2017(herb: set[str]) -> pd.DataFrame:
    p = pd.read_parquet(PNSP_PANEL)
    p = p[p["year"] == YEAR].copy()
    p["fips"] = p["state_fips"] * 1000 + p["county_fips"]
    p["norm"] = p["compound"].map(norm_chem)
    p["is_herb"] = p["norm"].isin(herb)
    p["is_glyph"] = p["norm"].str.startswith("GLYPHOSATE")

    total_kg = p["low_kg"].sum()
    matched_kg = p.loc[p["norm"].isin(herb) | p["norm"].isin(set()), "low_kg"].sum()
    print(f"[B.2] PNSP {YEAR}: {p['compound'].nunique()} compounds, "
          f"{p['fips'].nunique()} counties, {total_kg/1e6:.1f} M kg (EPest-low)")
    print(f"[B.2] classified as herbicide: {p.loc[p['is_herb'],'compound'].nunique()} compounds, "
          f"{p.loc[p['is_herb'],'low_kg'].sum()/1e6:.1f} M kg "
          f"({100*p.loc[p['is_herb'],'low_kg'].sum()/total_kg:.1f}% of mass)")
    unmatched = (p[~p["is_herb"]].groupby("compound")["low_kg"].sum()
                 .sort_values(ascending=False).head(8))
    print("[B.2] largest NON-herbicide-classified compounds (sanity check):")
    for c, kg in unmatched.items():
        print(f"        {c:<28} {kg/1e6:8.2f} M kg")

    g = p.groupby("fips").agg(
        herb_low_kg=("low_kg", lambda s: s[p.loc[s.index, "is_herb"]].sum()),
        herb_high_kg=("high_kg", lambda s: s[p.loc[s.index, "is_herb"]].sum()),
        glyph_low_kg=("low_kg", lambda s: s[p.loc[s.index, "is_glyph"]].sum()),
        all_low_kg=("low_kg", "sum"),
    ).reset_index()
    return g


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


def census_2017() -> pd.DataFrame:
    rows = []
    with gzip.open(CENSUS_2017, "rt", encoding="latin-1") as fh:
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
    print(f"[B.3] Census 2017 county rows pulled: {len(long):,} "
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
    d = df.dropna(subset=[ycol, xcol] + controls).copy()
    cols = [ycol, xcol] + controls
    if fe:
        d = demean(d, cols, fe)
        # groups of size 1 contribute nothing after demeaning
        sizes = df.dropna(subset=cols).groupby(fe)[ycol].transform("size")
        d = d[sizes.reindex(d.index).values > 1]
    X = np.column_stack([np.ones(len(d))] + [d[c].values for c in [xcol] + controls])
    beta, se, r2, _ = ols(d[ycol].values, X)
    b, s = beta[1], se[1]
    return dict(spec=label, n=len(d), beta_per_1=b, se=s,
                beta_per_10pp=10 * b, lo_per_10pp=10 * (b - 1.96 * s),
                hi_per_10pp=10 * (b + 1.96 * s),
                t=b / s if s else np.nan, r2=r2,
                n_groups=int(d[fe].nunique()) if fe else 0)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)

    herb = herbicide_roster()
    print(f"[B.1] NASS herbicide roster: {len(herb)} normalised active-ingredient names")

    pest = pnsp_2017(herb)
    cen = census_2017()

    df = cen.merge(pest, on="fips", how="inner")
    print(f"\n[B.4] merged counties: {len(df):,}")

    # --- construct ---------------------------------------------------------
    df["tilled_ac"] = df[["notill_ac", "constill_ac", "convtill_ac"]].sum(axis=1, min_count=3)
    df["notill_share"] = df["notill_ac"] / df["tilled_ac"]
    df["cover_share"] = df["covercrop_ac"] / df["tilled_ac"]
    df["harvested_ha"] = df["harvested_ac"] * ACRE_TO_HA
    df["herb_kg_ha"] = df["herb_low_kg"] / df["harvested_ha"]
    df["herb_kg_ha_high"] = df["herb_high_kg"] / df["harvested_ha"]
    df["glyph_kg_ha"] = df["glyph_low_kg"] / df["harvested_ha"]
    df["glyph_share"] = df["glyph_low_kg"] / df["herb_low_kg"]

    for c in ["corn_ac", "cornsil_ac", "soy_ac", "wheat_ac", "cotton_ac",
              "sorghum_ac", "rice_ac", "hay_ac", "veg_ac", "orchard_ac"]:
        df[c.replace("_ac", "_sh")] = df[c].fillna(0) / df["harvested_ac"]
    CROPSH = ["corn_sh", "cornsil_sh", "soy_sh", "wheat_sh", "cotton_sh",
              "sorghum_sh", "rice_sh", "hay_sh", "veg_sh", "orchard_sh"]

    n0 = len(df)
    df = df[(df["harvested_ac"] >= MIN_HARVESTED_ACRES)
            & (df["tilled_ac"] >= MIN_HARVESTED_ACRES)
            & (df["herb_low_kg"] > 0)
            & df["notill_share"].between(0, 1)]
    print(f"[B.4] after filter (harvested & tilled cropland >= {MIN_HARVESTED_ACRES:,} ac, "
          f"herbicide mass > 0): {len(df):,} counties (dropped {n0-len(df):,})")
    print(f"[B.4] these counties hold {df['harvested_ac'].sum()/1e6:.1f} M harvested acres "
          f"and {df['herb_low_kg'].sum()/1e6:.1f} M kg of herbicide")

    df["ln_herb"] = np.log(df["herb_kg_ha"])
    df["ln_glyph"] = np.log(df["glyph_kg_ha"].where(df["glyph_kg_ha"] > 0))

    # --- descriptives ------------------------------------------------------
    print("\n[DESC] no-till share of tilled cropland: "
          f"median {df['notill_share'].median():.3f}, "
          f"IQR {df['notill_share'].quantile(.25):.3f}-{df['notill_share'].quantile(.75):.3f}")
    print(f"[DESC] herbicide intensity kg/ha harvested: median {df['herb_kg_ha'].median():.2f}, "
          f"IQR {df['herb_kg_ha'].quantile(.25):.2f}-{df['herb_kg_ha'].quantile(.75):.2f}")
    print(f"[DESC] glyphosate share of herbicide mass: median {df['glyph_share'].median():.3f}")

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
    for ycol, yname in (("ln_herb", "all herbicides"), ("ln_glyph", "glyphosate")):
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

    print("\n[LADDER] effect of +10 percentage points of no-till share on applied mass per ha")
    print(f"{'outcome':<16}{'specification':<34}{'n':>6}{'%change':>10}{'  95% CI':>20}{'t':>8}")
    for _, r in lad.iterrows():
        print(f"{r['outcome']:<16}{r['spec']:<34}{r['n']:>6}{r['pct_per_10pp']:>9.1f}%"
              f"  [{r['pct_lo']:>6.1f}, {r['pct_hi']:>6.1f}]{r['t']:>8.1f}")

    # --- verification #1: EPest-high instead of EPest-low ------------------
    df["ln_herb_high"] = np.log(df["herb_kg_ha_high"])
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
        raw["norm"] = raw["COMPOUND"].map(norm_chem)
        raw = raw[raw["norm"].isin(herb)]
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
          f"{100*(rhos>0).mean():.0f}% positive, Wilcoxon p={w.pvalue:.3g}")

    # --- outputs -----------------------------------------------------------
    chart = lad[["outcome", "spec", "n", "pct_per_10pp", "pct_lo", "pct_hi", "t", "r2"]].copy()
    chart.columns = ["outcome", "specification", "n_counties",
                     "pct_change_per_10pp_notill", "ci_low", "ci_high", "t_stat", "r_squared"]
    chart.to_csv(DERIVED / "lens_six_notill_herbicide_tradeoff.csv", index=False)

    keep = ["fips", "state", "asd", "notill_share", "cover_share", "tilled_ac",
            "harvested_ac", "herb_low_kg", "herb_high_kg", "glyph_low_kg",
            "herb_kg_ha", "glyph_kg_ha", "glyph_share"] + CROPSH
    df[keep].to_csv(DERIVED / "lens_six_county_panel_2017.csv", index=False)

    print(f"\nwrote {DERIVED/'lens_six_notill_herbicide_tradeoff.csv'}")
    print(f"wrote {DERIVED/'lens_six_county_panel_2017.csv'}")
    print(f"\n[FOR FINDING.md] crop-mix-only R^2 on log herbicide intensity = {r2_cropmix:.3f}")


if __name__ == "__main__":
    sys.exit(main())
