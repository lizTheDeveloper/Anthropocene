#!/usr/bin/env python3
"""
Redesign or substitution? Quantifying the concentration of the US agricultural
pesticide mixture, 1992-2018, against the one redesign indicator the federal
record carries (Census of Agriculture cover-crop and tillage acreage).

Lens: the efficiency / input-substitution / redesign transition sequence used in
agroecology (Hill 1985; MacRae et al. 1990; Gliessman 2007; applied in
Nicholls, Altieri & Vazquez 2016).  See FINDING.md for the argument and the
attribution rules.  This script only produces numbers.

Run from the repository root:

    python analysis/altieri/compute.py

Requires pandas + pyarrow + numpy + scipy.

Outputs (all written under data/derived/):
    lens_altieri_simplification.csv   <- the chart series (tidy long)
    lens_altieri_class_shares.csv     <- herbicide/insecticide/fungicide/other mass shares
    lens_altieri_state_panel.csv      <- state-level cover crop vs chemistry, 2012 & 2017
    lens_altieri_compound_classes.csv <- the compound -> pesticide-class map actually used
and prints a verification block to stdout.
"""
from __future__ import annotations

import gzip
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
NASS = ROOT / "data" / "raw" / "usda-nass" / "quickstats-bulk" / "2026-09-14"
ENVFILE = NASS / "qs.environmental_20260912.txt.gz"
CENSUS = {y: NASS / f"qs.census{y}.txt.gz" for y in (2012, 2017, 2022)}

PANEL = DERIVED / "pnsp_county_panel_corrected.parquet"

# ---------------------------------------------------------------------------
# 1.  Pesticide-class map
# ---------------------------------------------------------------------------
# The PNSP county panel carries no pesticide class.  USDA NASS does: in the
# Agricultural Chemical Use file, DOMAIN_DESC is "CHEMICAL, HERBICIDE" /
# "INSECTICIDE" / "FUNGICIDE" / "OTHER" and DOMAINCAT_DESC names the active
# ingredient and its EPA PC code.  That is a federal, in-mirror mapping.
#
# Two gaps have to be closed by hand and are declared here rather than buried:
#   (a) 23 active ingredients appear under more than one NASS class.  Resolved
#       by NASS record count (the class the ingredient is overwhelmingly
#       surveyed under).  All the mass-heavy cases resolve the textbook way -
#       sulfur -> fungicide, paraquat -> herbicide, methyl bromide -> other.
#   (b) 164 PNSP compounds (12.1% of 1992-2018 mass) have no NASS entry, mostly
#       because PNSP and NASS spell them differently (METOLACHLOR-S vs
#       S-METOLACHLOR) or because NASS never surveyed them.  The table below
#       assigns the ones that matter; it is ordered by applied mass and covers
#       down to ~0.007% of national mass each.  Everything still unassigned is
#       reported as UNCLASSIFIED, not silently dropped, and FINDING.md reports
#       the herbicide-share result with all of it forced to non-herbicide as a
#       lower bound.
MANUAL_CLASS = {
    # fumigants and soil sterilants -> OTHER (they are not weed-, insect- or
    # disease-specific and NASS itself files methyl bromide under OTHER)
    "METAM": "OTHER",
    "SULFCARBAMIDE": "OTHER",
    "DIMETHYL DISULFIDE": "OTHER",
    "ALLYL ISOTHIOCYANATE": "OTHER",
    "METHYL IODIDE": "OTHER",
    # plant growth regulators, desiccants, adjuvants, minerals -> OTHER
    "DECAN-1-OL": "OTHER",
    "MALEIC HYDRAZIDE": "OTHER",
    "MEPIQUAT": "OTHER",
    "KAOLIN CLAY": "OTHER",
    "PHOSPHORIC ACID": "OTHER",
    "SILICATES": "OTHER",
    "HYDRATED LIME": "OTHER",
    "POTASSIUM BICARBONATE": "OTHER",
    "POTASSIUM OLEATE": "OTHER",
    "CALCIUM CHLORIDE": "OTHER",
    "ZINC": "OTHER",
    "BARIUM POLYSULFIDE": "OTHER",
    "BUTRALIN": "OTHER",
    "DIMETHYLARSINIC ACID": "OTHER",
    # herbicides
    "METOLACHLOR-S": "HERBICIDE",
    "GLUFOSINATE": "HERBICIDE",
    "BENTAZONE": "HERBICIDE",
    "PICLORAM": "HERBICIDE",
    "ACIFLUORFEN": "HERBICIDE",
    "DICLOFOP": "HERBICIDE",
    "ASULAM": "HERBICIDE",
    "FLUAZIFOP": "HERBICIDE",
    "DIQUAT": "HERBICIDE",
    "CHLORIMURON": "HERBICIDE",
    "BENFLURALIN": "HERBICIDE",
    "QUIZALOFOP": "HERBICIDE",
    "DIFLUFENZOPYR": "HERBICIDE",
    "CHLORIDAZON": "HERBICIDE",
    "MECOPROP": "HERBICIDE",
    "CHLORAMBEN": "HERBICIDE",
    "THIENCARBAZONE-METHYL": "HERBICIDE",
    "HALOSULFURON": "HERBICIDE",
    "MCPB": "HERBICIDE",
    "PYRASULFOTOLE": "HERBICIDE",
    "PROPYZAMIDE": "HERBICIDE",
    "METSULFURON": "HERBICIDE",
    "CLODINAFOP": "HERBICIDE",
    "FLUMICLORAC": "HERBICIDE",
    "ENDOTHAL": "HERBICIDE",
    "CYHALOFOP": "HERBICIDE",
    # insecticides / acaricides / nematicides
    "PARATHION": "INSECTICIDE",
    "ETHOPROPHOS": "INSECTICIDE",
    "CYHALOTHRIN-LAMBDA": "INSECTICIDE",
    "BACILLUS THURINGIENSIS": "INSECTICIDE",
    "SPINOSYN": "INSECTICIDE",
    "FORMETANATE": "INSECTICIDE",
    # fungicides / bactericides
    "BACILLUS AMYLOLIQUIFACIEN": "FUNGICIDE",
    "QUINTOZENE": "FUNGICIDE",
    "COPPER": "FUNGICIDE",
    "FENTIN": "FUNGICIDE",
    "COPPER OXYCHLORIDE S": "FUNGICIDE",
    "PROPAMOCARB HCL": "FUNGICIDE",
    "FOSETYL": "FUNGICIDE",
    "CUPROUS OXIDE": "FUNGICIDE",
    "BURKHOLDERIA SPP": "FUNGICIDE",
}
CLASSES = ["HERBICIDE", "INSECTICIDE", "FUNGICIDE", "OTHER", "UNCLASSIFIED"]


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def build_class_map(compounds) -> pd.DataFrame:
    """compound -> {HERBICIDE, INSECTICIDE, FUNGICIDE, OTHER, UNCLASSIFIED}."""
    counts: dict[tuple[str, str], int] = {}
    pat = re.compile(r"^CHEMICAL, (HERBICIDE|INSECTICIDE|FUNGICIDE|OTHER)$")
    aipat = re.compile(r":\s*\((.*?)\s*=\s*\d+\)$")
    with gzip.open(ENVFILE, "rt", encoding="latin-1") as fh:
        next(fh)
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 12:
                continue
            m = pat.match(f[10])
            if not m:
                continue
            a = aipat.search(f[11])
            if not a:
                continue
            counts[(_norm(a.group(1)), m.group(1))] = (
                counts.get((_norm(a.group(1)), m.group(1)), 0) + 1
            )
    nass = (
        pd.DataFrame(
            [{"k": k, "cls": c, "n": v} for (k, c), v in counts.items()]
        )
        .sort_values("n", ascending=False)
        .drop_duplicates("k")
        .set_index("k")["cls"]
    )
    rows = []
    for c in compounds:
        k = _norm(c)
        if c in MANUAL_CLASS:
            rows.append((c, MANUAL_CLASS[c], "manual"))
        elif k in nass.index:
            rows.append((c, nass.loc[k], "nass_domaincat"))
        else:
            rows.append((c, "UNCLASSIFIED", "none"))
    return pd.DataFrame(rows, columns=["compound", "pesticide_class", "class_source"])


# ---------------------------------------------------------------------------
# 2.  Diversity of the applied mixture
# ---------------------------------------------------------------------------
def hill_numbers(shares: np.ndarray) -> tuple[float, float, float]:
    """(inverse Simpson = effective no. of compounds, exp(Shannon), top-1 share)."""
    q = shares[shares > 0]
    q = q / q.sum()
    return float(1.0 / np.sum(q ** 2)), float(np.exp(-np.sum(q * np.log(q)))), float(q.max())


def national_series(panel: pd.DataFrame, cls: pd.DataFrame) -> pd.DataFrame:
    cy = panel.groupby(["year", "compound"], as_index=False)[["low_kg", "high_kg"]].sum()
    cy = cy.merge(cls, on="compound", how="left")
    cy["pesticide_class"] = cy.pesticide_class.fillna("UNCLASSIFIED")
    # a fixed roster = compounds reported in every one of the 27 years, so the
    # growing compound roster (270 -> 343) cannot manufacture the trend
    present = cy[cy.high_kg > 0].groupby("compound").year.nunique()
    stable = set(present[present == panel.year.nunique()].index)

    out = []
    for y, g in cy.groupby("year"):
        gh = g[g.high_kg > 0]
        inv_h, shn_h, top_h = hill_numbers(gh.high_kg.values)
        gl = g[g.low_kg > 0]
        inv_l, _, top_l = hill_numbers(gl.low_kg.values)
        gs = gh[gh.compound.isin(stable)]
        inv_s, _, _ = hill_numbers(gs.high_kg.values)
        tot = gh.high_kg.sum()
        cum = np.sort(gh.high_kg.values)[::-1].cumsum() / tot
        row = dict(
            year=int(y),
            total_high_Mkg=tot / 1e6,
            n_compounds=int(len(gh)),
            eff_compounds_national=inv_h,
            exp_shannon_national=shn_h,
            top1_compound=gh.loc[gh.high_kg.idxmax(), "compound"],
            top1_share_pct=top_h * 100,
            glyphosate_share_pct=gh.loc[gh.compound == "GLYPHOSATE", "high_kg"].sum() / tot * 100,
            # herbicide share computed on the NASS-classified subset only, as a
            # sensitivity against the 12% of mass classed by the manual table
            herbicide_share_nass_only_pct=(
                gh.loc[(gh.pesticide_class == "HERBICIDE") & (gh.class_source == "nass_domaincat"), "high_kg"].sum()
                / gh.loc[gh.class_source == "nass_domaincat", "high_kg"].sum() * 100
            ),
            eff_compounds_national_low=inv_l,
            top1_share_pct_low=top_l * 100,
            eff_compounds_national_stable_roster=inv_s,
            n_compounds_for_50pct_mass=int(np.searchsorted(cum, 0.50) + 1),
            n_compounds_for_80pct_mass=int(np.searchsorted(cum, 0.80) + 1),
        )
        for c in CLASSES:
            row[f"share_{c.lower()}_pct"] = gh.loc[gh.pesticide_class == c, "high_kg"].sum() / tot * 100
        out.append(row)
    return pd.DataFrame(out)


def county_series(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel[panel.high_kg > 0].copy()
    p["fips"] = p.state_fips * 1000 + p.county_fips
    tot = p.groupby(["year", "fips"], as_index=False).high_kg.sum().rename(columns={"high_kg": "tot"})
    p = p.merge(tot, on=["year", "fips"])
    p["q"] = p.high_kg / p.tot
    agg = (
        p.groupby(["year", "fips"])
        .agg(sumq2=("q", lambda s: float(np.sum(s.values ** 2))), n=("q", "size"), tot=("tot", "first"))
        .reset_index()
    )
    agg["eff"] = 1.0 / agg.sumq2
    gly = p[p.compound == "GLYPHOSATE"].groupby(["year", "fips"]).q.sum().rename("gly")
    agg = agg.merge(gly, on=["year", "fips"], how="left")
    agg["gly"] = agg.gly.fillna(0.0)
    out = (
        agg.groupby("year")
        .apply(
            lambda g: pd.Series(
                {
                    "n_counties": float(len(g)),
                    "eff_compounds_county_median": g.eff.median(),
                    "eff_compounds_county_mean": g.eff.mean(),
                    "eff_compounds_county_masswt": float(np.average(g.eff, weights=g.tot)),
                    "n_compounds_county_median": g.n.median(),
                    "pct_counties_glyphosate_over_25pct": (g.gly > 0.25).mean() * 100,
                    "pct_counties_glyphosate_over_50pct": (g.gly > 0.50).mean() * 100,
                    "glyphosate_share_masswt_pct": float(np.average(g.gly, weights=g.tot)) * 100,
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    out["year"] = out.year.astype(int)
    return out, agg


# ---------------------------------------------------------------------------
# 3.  Census of Agriculture: the redesign indicator
# ---------------------------------------------------------------------------
PRACTICE_SERIES = {
    "AG LAND, CROPLAND - ACRES": "cropland_acres",
    "PRACTICES, LAND USE, CROPLAND, COVER CROP PLANTED, (EXCL CRP) - ACRES": "cover_crop_acres",
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, NO-TILL - ACRES": "notill_acres",
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, (EXCL NO-TILL) - ACRES": "constill_acres",
    "PRACTICES, LAND USE, CROPLAND, CONVENTIONAL TILLAGE - ACRES": "convtill_acres",
}


def _value(v: str) -> float:
    """NASS VALUE is a string with thousands separators and suppression codes."""
    v = v.strip()
    if not v or v.startswith("("):  # (D), (Z), (NA), (X)
        return np.nan
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return np.nan


def census_practices() -> pd.DataFrame:
    rows = []
    for year, path in CENSUS.items():
        with gzip.open(path, "rt", encoding="latin-1") as fh:
            next(fh)
            for line in fh:
                f = line.rstrip("\n").split("\t")
                if len(f) < 38:
                    continue
                name = PRACTICE_SERIES.get(f[9])
                if name is None or f[10] != "TOTAL":
                    continue
                lvl = f[12]
                if lvl not in ("NATIONAL", "STATE"):
                    continue
                rows.append(
                    dict(
                        census_year=year,
                        level=lvl,
                        state_fips=int(f[14]) if lvl == "STATE" and f[14].strip() else -1,
                        state=f[16],
                        series=name,
                        acres=_value(f[37]),
                    )
                )
    df = pd.DataFrame(rows)
    out = df.pivot_table(
        index=["census_year", "level", "state_fips", "state"],
        columns="series",
        values="acres",
        aggfunc="sum",
    ).reset_index()
    out.columns.name = None
    return out


# ---------------------------------------------------------------------------
def main() -> None:
    panel = pd.read_parquet(
        PANEL, columns=["compound", "year", "state_fips", "county_fips", "low_kg", "high_kg"]
    )
    cls = build_class_map(sorted(panel.compound.unique()))
    cls.to_csv(DERIVED / "lens_altieri_compound_classes.csv", index=False)

    nat = national_series(panel, cls)
    cty, county_year = county_series(panel)
    nat = nat.merge(cty, on="year")

    cen = census_practices()
    natcen = cen[cen.level == "NATIONAL"].copy()
    for c in ("cover_crop", "notill", "constill", "convtill"):
        natcen[f"{c}_pct_cropland"] = natcen[f"{c}_acres"] / natcen["cropland_acres"] * 100

    # ---- the chart CSV: one tidy long table ------------------------------
    long = []
    for _, r in nat.iterrows():
        for metric, val, unit in [
            ("eff_compounds_county_median", r.eff_compounds_county_median, "effective number of compounds"),
            ("eff_compounds_national", r.eff_compounds_national, "effective number of compounds"),
            ("n_compounds_county_median", r.n_compounds_county_median, "count"),
            ("glyphosate_share_pct", r.glyphosate_share_pct, "percent of applied kg"),
            ("top1_compound_share_pct", r.top1_share_pct, "percent of applied kg"),
            ("herbicide_share_pct", r.share_herbicide_pct, "percent of applied kg"),
            ("insecticide_share_pct", r.share_insecticide_pct, "percent of applied kg"),
            ("fungicide_share_pct", r.share_fungicide_pct, "percent of applied kg"),
            ("pct_counties_glyphosate_over_25pct", r.pct_counties_glyphosate_over_25pct, "percent of counties"),
            ("total_applied_Mkg", r.total_high_Mkg, "million kg"),
        ]:
            long.append(dict(year=int(r.year), metric=metric, value=float(val), unit=unit, source="USGS PNSP (corrected, no CA)"))
    for _, r in natcen.iterrows():
        for metric, val in [
            ("cover_crop_pct_cropland", r.cover_crop_pct_cropland),
            ("notill_pct_cropland", r.notill_pct_cropland),
            ("constill_pct_cropland", r.constill_pct_cropland),
        ]:
            if pd.notna(val):
                long.append(dict(year=int(r.census_year), metric=metric, value=float(val),
                                 unit="percent of cropland acres", source="USDA Census of Agriculture"))
    long_df = pd.DataFrame(long).sort_values(["metric", "year"])
    long_df.to_csv(DERIVED / "lens_altieri_simplification.csv", index=False)

    nat[["year", "total_high_Mkg"] + [f"share_{c.lower()}_pct" for c in CLASSES]].to_csv(
        DERIVED / "lens_altieri_class_shares.csv", index=False
    )

    # ---- state panel: cover crops vs chemistry ---------------------------
    p = panel[panel.high_kg > 0].copy()
    st_rows = []
    for y in (2012, 2017):
        g = p[p.year == y]
        tot = g.groupby("state_fips").high_kg.sum()
        for sf, gg in g.groupby("state_fips"):
            inv, shn, top = hill_numbers(gg.groupby("compound").high_kg.sum().values)
            gly = gg.loc[gg.compound == "GLYPHOSATE", "high_kg"].sum()
            st_rows.append(dict(year=y, state_fips=int(sf), total_high_kg=float(tot[sf]),
                                eff_compounds=inv, glyphosate_share_pct=gly / tot[sf] * 100))
    st = pd.DataFrame(st_rows)
    cs = cen[cen.level == "STATE"].copy()
    cs["cover_crop_pct_cropland"] = cs.cover_crop_acres / cs.cropland_acres * 100
    cs["notill_pct_cropland"] = cs.notill_acres / cs.cropland_acres * 100
    cs = cs[cs.census_year.isin([2012, 2017])][
        ["census_year", "state_fips", "state", "cover_crop_pct_cropland", "notill_pct_cropland", "cropland_acres"]
    ].rename(columns={"census_year": "year"})
    sp = st.merge(cs, on=["year", "state_fips"], how="inner").dropna(
        subset=["cover_crop_pct_cropland", "eff_compounds"]
    )
    sp.to_csv(DERIVED / "lens_altieri_state_panel.csv", index=False)

    # ---- verification ----------------------------------------------------
    print("=" * 78)
    print("VERIFICATION")
    print("=" * 78)

    # (1) glyphosate share and total mass must reproduce the independently
    #     built national file (eda_04_corrected_series.py)
    ref = pd.read_csv(DERIVED / "pnsp_national_corrected.csv")
    chk = nat.merge(ref[["year", "glyphosate_pct", "total_high_Mkg"]], on="year", suffixes=("", "_ref"))
    print(f"[1] glyphosate share vs pnsp_national_corrected.glyphosate_pct: "
          f"max abs diff = {(chk.glyphosate_share_pct - chk.glyphosate_pct).abs().max():.2e} pp")
    print(f"[1] total mass vs pnsp_national_corrected.total_high_Mkg: "
          f"max abs diff = {(chk.total_high_Mkg - chk.total_high_Mkg_ref).abs().max():.2e} M kg")

    # (2) recompute effective compounds from the *independently built*
    #     compound x year matrix rather than from the parquet.  That matrix is
    #     California-corrected but NOT aggregate-corrected: it still carries the
    #     double-counted "METOLACHLOR & METOLACHLOR-S" and "DIMETHENAMID &
    #     DIMETHENAMID-P" columns, which exist only from 2016.  So the two
    #     routes must agree exactly for 1992-2015, and must agree for 2016-2018
    #     only once those columns are dropped.
    mx = pd.read_csv(DERIVED / "pnsp_compound_year_matrix_noCA.csv").set_index("year")
    aggcols = [c for c in mx.columns if "&" in c]
    a = nat.set_index("year").eff_compounds_national

    def _inv_simpson_row(row):
        v = pd.to_numeric(row, errors="coerce").fillna(0).values
        v = v[v > 0]
        return float(1.0 / np.sum((v / v.sum()) ** 2)) if v.size else np.nan

    raw = mx.apply(_inv_simpson_row, axis=1)
    fixed = mx.drop(columns=aggcols).apply(_inv_simpson_row, axis=1)
    pre = (raw.loc[:2015] - a.loc[:2015]).abs().max()
    post = (fixed - a.reindex(fixed.index)).abs().max()
    print(f"[2] eff. compounds from pnsp_compound_year_matrix_noCA.csv, 1992-2015: "
          f"max abs diff = {pre:.2e}")
    print(f"[2] ... same matrix with the {len(aggcols)} double-counted aggregate columns dropped, "
          f"all years: max abs diff = {post:.2e}")
    print(f"[2] ... leaving them in inflates 2018 to {raw.loc[2018]:.3f} vs {a.loc[2018]:.3f} "
          f"(the known PNSP aggregate artifact, established finding #2)")

    # (3) mass-weighted mean county glyphosate share must equal the national share
    d3 = (nat.glyphosate_share_masswt_pct - nat.glyphosate_share_pct).abs().max()
    print(f"[3] mass-weighted county glyphosate share vs national share: max abs diff = {d3:.2e} pp")

    # (4) census: national acreage must equal the sum of the state rows
    for y in (2012, 2017, 2022):
        n = natcen[natcen.census_year == y]
        s = cen[(cen.level == "STATE") & (cen.census_year == y)]
        for col in ("cover_crop_acres", "notill_acres", "cropland_acres"):
            nv, sv = float(n[col].iloc[0]), float(s[col].sum())
            print(f"[4] {y} {col:<18} national={nv:>13,.0f} sum(states)={sv:>13,.0f} "
                  f"diff={nv - sv:>+12,.0f} ({(nv - sv) / nv * 100:+.3f}%)")

    # (5) class-map coverage and the herbicide-share lower bound
    cm = panel.groupby("compound", as_index=False).high_kg.sum().merge(cls, on="compound")
    tot = cm.high_kg.sum()
    print("[5] class map coverage by 1992-2018 mass:")
    for src, g in cm.groupby("class_source"):
        print(f"      {src:<15} {g.high_kg.sum() / tot * 100:6.2f}%  ({len(g)} compounds)")
    for y in (1992, 2018):
        r = nat[nat.year == y].iloc[0]
        print(f"      {y}: herbicide {r.share_herbicide_pct:5.1f}%  "
              f"unclassified {r.share_unclassified_pct:.2f}%  "
              f"| herbicide share on the NASS-classified subset alone: "
              f"{r.herbicide_share_nass_only_pct:5.1f}%")

    # ---- headline numbers -----------------------------------------------
    print("=" * 78)
    print("HEADLINES")
    print("=" * 78)
    a, b = nat[nat.year == 1992].iloc[0], nat[nat.year == 2018].iloc[0]
    trough = nat.loc[nat.eff_compounds_national.idxmin()]
    print(f"national effective compounds  1992 {a.eff_compounds_national:6.2f} -> "
          f"2018 {b.eff_compounds_national:6.2f}  ({(b.eff_compounds_national / a.eff_compounds_national - 1) * 100:+.1f}%), "
          f"trough {trough.eff_compounds_national:.2f} in {int(trough.year)}")
    print(f"  fixed-roster version        1992 {a.eff_compounds_national_stable_roster:6.2f} -> "
          f"2018 {b.eff_compounds_national_stable_roster:6.2f}")
    print(f"  EPest-low version           1992 {a.eff_compounds_national_low:6.2f} -> "
          f"2018 {b.eff_compounds_national_low:6.2f}")
    print(f"county median eff. compounds  1992 {a.eff_compounds_county_median:6.2f} -> "
          f"2018 {b.eff_compounds_county_median:6.2f}  ({(b.eff_compounds_county_median / a.eff_compounds_county_median - 1) * 100:+.1f}%)")
    print(f"county median compound COUNT  1992 {a.n_compounds_county_median:6.0f} -> 2018 {b.n_compounds_county_median:6.0f}")
    print(f"registered compound roster    1992 {a.n_compounds:6.0f} -> 2018 {b.n_compounds:6.0f}")
    print(f"total applied mass (M kg)     1992 {a.total_high_Mkg:6.1f} -> 2018 {b.total_high_Mkg:6.1f} "
          f"({(b.total_high_Mkg / a.total_high_Mkg - 1) * 100:+.1f}%)")
    print(f"herbicide share of mass       1992 {a.share_herbicide_pct:6.1f}% -> 2018 {b.share_herbicide_pct:6.1f}%")
    print(f"insecticide share of mass     1992 {a.share_insecticide_pct:6.1f}% -> 2018 {b.share_insecticide_pct:6.1f}%")
    print(f"fungicide share of mass       1992 {a.share_fungicide_pct:6.1f}% -> 2018 {b.share_fungicide_pct:6.1f}%")
    print(f"counties >25% glyphosate      1992 {a.pct_counties_glyphosate_over_25pct:6.2f}% -> "
          f"2018 {b.pct_counties_glyphosate_over_25pct:6.2f}%")
    print(f"compounds to reach 50% mass   1992 {a.n_compounds_for_50pct_mass:6.0f} -> 2018 {b.n_compounds_for_50pct_mass:6.0f} "
          f"(2012: {int(nat.loc[nat.year == 2012, 'n_compounds_for_50pct_mass'].iloc[0])})")
    print(f"compounds to reach 80% mass   1992 {a.n_compounds_for_80pct_mass:6.0f} -> 2018 {b.n_compounds_for_80pct_mass:6.0f}")
    print(f"glyphosate as % of HERBICIDE mass  1992 {a.glyphosate_share_pct / a.share_herbicide_pct * 100:5.1f}% -> "
          f"2018 {b.glyphosate_share_pct / b.share_herbicide_pct * 100:5.1f}%")
    print("herbicide share, 5-yr means:  1992-96 "
          f"{nat[nat.year.between(1992, 1996)].share_herbicide_pct.mean():.1f}% -> 2014-18 "
          f"{nat[nat.year.between(2014, 2018)].share_herbicide_pct.mean():.1f}%")
    print("insecticide share, 5-yr means:1992-96 "
          f"{nat[nat.year.between(1992, 1996)].share_insecticide_pct.mean():.1f}% -> 2008-12 "
          f"{nat[nat.year.between(2008, 2012)].share_insecticide_pct.mean():.1f}%  "
          "(2015+ not comparable: USGS dropped seed-treatment estimates)")
    print()
    print(natcen[["census_year", "cropland_acres", "cover_crop_acres", "cover_crop_pct_cropland",
                  "notill_pct_cropland", "constill_pct_cropland", "convtill_pct_cropland"]]
          .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print()

    # ---- the tension, at state level ------------------------------------
    print("=" * 78)
    print("STATE-LEVEL: does cover cropping go with chemical de-concentration?")
    print("=" * 78)
    for y in (2012, 2017):
        g = sp[sp.year == y]
        for xcol in ("eff_compounds", "glyphosate_share_pct"):
            rho, pv = stats.spearmanr(g.cover_crop_pct_cropland, g[xcol])
            print(f"  {y} n={len(g):3d}  cover-crop % vs {xcol:<22} rho={rho:+.3f}  p={pv:.4f}")
        rho, pv = stats.spearmanr(g.notill_pct_cropland, g.glyphosate_share_pct)
        print(f"  {y} n={len(g):3d}  no-till    % vs glyphosate_share_pct   rho={rho:+.3f}  p={pv:.4f}")
    w = sp.pivot_table(index=["state_fips", "state"], columns="year",
                       values=["cover_crop_pct_cropland", "eff_compounds", "glyphosate_share_pct"])
    w = w.dropna()
    d_cover = w[("cover_crop_pct_cropland", 2017)] - w[("cover_crop_pct_cropland", 2012)]
    d_eff = w[("eff_compounds", 2017)] - w[("eff_compounds", 2012)]
    d_gly = w[("glyphosate_share_pct", 2017)] - w[("glyphosate_share_pct", 2012)]
    for lbl, d in (("d_eff_compounds", d_eff), ("d_glyphosate_share_pct", d_gly)):
        rho, pv = stats.spearmanr(d_cover, d)
        print(f"  2012->2017 change, n={len(w):3d}  d cover-crop % vs {lbl:<24} rho={rho:+.3f}  p={pv:.4f}")
    print(f"  states where cover-crop share rose 2012->2017: {(d_cover > 0).sum()}/{len(w)}")
    print(f"  ... of those, states where effective compounds ALSO rose: "
          f"{((d_cover > 0) & (d_eff > 0)).sum()}/{(d_cover > 0).sum()}")
    for y in (2012, 2017):
        g = sp[sp.year == y].sort_values("notill_pct_cropland")
        lo, hi = g.head(10), g.tail(10)
        print(f"  {y}: 10 states with the LOWEST no-till share  -> mean glyphosate share "
              f"{lo.glyphosate_share_pct.mean():5.1f}%, mean eff. compounds {lo.eff_compounds.mean():5.2f}")
        print(f"  {y}: 10 states with the HIGHEST no-till share -> mean glyphosate share "
              f"{hi.glyphosate_share_pct.mean():5.1f}%, mean eff. compounds {hi.eff_compounds.mean():5.2f}")

    print()
    print("wrote:")
    for f in ("lens_altieri_simplification.csv", "lens_altieri_class_shares.csv",
              "lens_altieri_state_panel.csv", "lens_altieri_compound_classes.csv"):
        print("  data/derived/" + f)


if __name__ == "__main__":
    main()
