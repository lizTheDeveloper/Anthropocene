#!/usr/bin/env python3
"""
lens: mendez -- "who defined what got measured, and whose farming is absent?"

Maps the reach of the federal pesticide-use *measurement* programme against the
federal inventory of what is actually farmed, using two USDA NASS products that
share one controlled vocabulary (COMMODITY_DESC):

  A. Agricultural Chemical Use Program (ACUP) survey record
     qs.environmental_*.txt.gz, SOURCE_DESC = SURVEY, DOMAIN_DESC ~ "CHEMICAL".
     The record of *what got measured*: crop x state x year cells for which
     NASS ever published a pesticide-use estimate.

  B. 2022 Census of Agriculture crop inventory
     qs.census2022.txt.gz, SECTOR_DESC = CROPS.
     The denominator of *what is grown*: acres and operations, by crop, by
     county.

  C. (cross-check) USGS PNSP state x crop-group pesticide mass, 1992-2016,
     which reports mass for crop groups -- Alfalfa, Pasture_and_hay -- that
     never appear in the public NASS survey record.

Outputs (repo-root relative):
  data/derived/lens_mendez_county_coverage.csv        <- primary chart CSV
  data/derived/lens_mendez_diversity_bins.csv         <- binned chart series
  data/derived/lens_mendez_crop_coverage.csv          <- crop-level ledger
  data/derived/lens_mendez_state_coverage.csv         <- state roll-up

Run from repo root:  python3 analysis/mendez/compute.py
"""

import os
import io
import math
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BULK = os.path.join(ROOT, "data/raw/usda-nass/quickstats-bulk/2026-09-14")
ENV = os.path.join(BULK, "qs.environmental_20260912.txt.gz")
CEN = os.path.join(BULK, "qs.census2022.txt.gz")
PNSP_CROP = os.path.join(
    ROOT, "data/raw/usgs/pnsp/2026-09-14/state-level/AgPestUsebyCropGroup92to16.zip")
OUT = os.path.join(ROOT, "data/derived")

READ_KW = dict(sep="\t", encoding="latin-1", dtype=str, quoting=3,
               chunksize=400_000, na_filter=False, low_memory=False)

# Census commodity rows that are roll-ups of other rows in the same table.
# Keeping them would double-count acreage.
ROLLUPS = {
    "HAY & HAYLAGE",                 # = HAY + HAYLAGE
    "GRASSES & LEGUMES TOTALS",      # = GRASSES + LEGUMES + GRASSES & LEGUMES, OTHER
    "BERRY TOTALS", "CITRUS TOTALS", "NON-CITRUS TOTALS", "TREE NUT TOTALS",
    "ORCHARDS", "FRUIT & TREE NUT TOTALS",
    "FLORICULTURE TOTALS", "NURSERY TOTALS", "NURSERY & FLORICULTURE TOTALS",
    "BEDDING PLANT TOTALS", "CUT FLOWERS & CUT CULTIVATED GREENS",
    "VEGETABLE TOTALS", "CROP TOTALS", "FIELD CROP TOTALS",
    "SOD & SEED TOTALS", "PROPAGATIVE MATERIAL TOTALS", "HORTICULTURE TOTALS",
    "FOOD CROPS GROWN UNDER PROTECTION",
}

SUPPRESSED = {"(D)", "(Z)", "(NA)", "(X)", "(L)", "(H)", "(S)", ""}

RECENT_FROM = 2013     # ~two full ACUP rotation cycles back from 2025
MIN_COUNTY_ACRES = 1000


def to_num(v):
    v = v.strip()
    if v in SUPPRESSED:
        return np.nan
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return np.nan


# ---------------------------------------------------------------- A. ACUP frame
def load_acup():
    keep = []
    for ch in pd.read_csv(ENV, **READ_KW):
        ch.columns = [c.strip() for c in ch.columns]
        m = (ch.SOURCE_DESC == "SURVEY") & ch.DOMAIN_DESC.str.contains("CHEMICAL", na=False)
        if m.any():
            keep.append(ch.loc[m, ["COMMODITY_DESC", "AGG_LEVEL_DESC", "STATE_ALPHA",
                                   "YEAR", "DOMAIN_DESC"]])
    a = pd.concat(keep, ignore_index=True)
    a["YEAR"] = a.YEAR.astype(int)
    return a, a[a.AGG_LEVEL_DESC == "STATE"].copy()


# ------------------------------------------------------- B. Census crop inventory
def load_census(level):
    """Census 2022 crop acres + operations at `level`, class/util de-duplicated."""
    keep = []
    cols = ["GROUP_DESC", "COMMODITY_DESC", "CLASS_DESC", "UTIL_PRACTICE_DESC",
            "STATISTICCAT_DESC", "UNIT_DESC", "VALUE",
            "STATE_ALPHA", "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME"]
    for ch in pd.read_csv(CEN, **READ_KW):
        ch.columns = [c.strip() for c in ch.columns]
        m = ((ch.SECTOR_DESC == "CROPS")
             & (ch.AGG_LEVEL_DESC == level)
             & (ch.DOMAIN_DESC == "TOTAL")
             & (ch.PRODN_PRACTICE_DESC == "ALL PRODUCTION PRACTICES")
             & ch.UNIT_DESC.isin(["ACRES", "OPERATIONS"])
             & ch.STATISTICCAT_DESC.isin(["AREA HARVESTED", "AREA BEARING",
                                          "AREA GROWN", "AREA IN PRODUCTION"]))
        if m.any():
            keep.append(ch.loc[m, cols])
    d = pd.concat(keep, ignore_index=True)

    # One area concept per crop group, so tree-fruit "bearing" acres and row-crop
    # "harvested" acres are not stacked on top of each other.
    pref = {"FIELD CROPS": "AREA HARVESTED", "VEGETABLES": "AREA HARVESTED",
            "FRUIT & TREE NUTS": "AREA BEARING", "HORTICULTURE": "AREA IN PRODUCTION"}
    d = d[[pref.get(g) == s for g, s in zip(d.GROUP_DESC, d.STATISTICCAT_DESC)]].copy()
    d = d[~d.COMMODITY_DESC.isin(ROLLUPS)]
    d["v"] = d.VALUE.map(to_num)

    if level == "COUNTY":
        d["fips"] = d.STATE_FIPS_CODE.str.zfill(2) + d.COUNTY_CODE.str.zfill(3)
        geo = ["fips", "STATE_ALPHA", "COUNTY_NAME"]
    elif level == "STATE":
        geo = ["STATE_ALPHA"]
    else:
        geo = []

    p = d.pivot_table(index=geo + ["GROUP_DESC", "COMMODITY_DESC", "CLASS_DESC",
                                   "UTIL_PRACTICE_DESC"],
                      columns="UNIT_DESC", values="v", aggfunc="first").reset_index()
    for c in ("ACRES", "OPERATIONS"):
        if c not in p.columns:
            p[c] = np.nan

    # De-duplicate NASS's two hierarchy axes. Where an "ALL ..." roll-up row exists
    # for a commodity within a geography it *is* the total and the sub-rows are its
    # parts; where it does not, the sub-rows together are the total.
    key = geo + ["COMMODITY_DESC"]
    for col, allval in (("CLASS_DESC", "ALL CLASSES"),
                        ("UTIL_PRACTICE_DESC", "ALL UTILIZATION PRACTICES")):
        has_all = (p[col] == allval).groupby([p[k] for k in key]).transform("any")
        p = p[(~has_all) | (p[col] == allval)]

    return (p.groupby(geo + ["GROUP_DESC", "COMMODITY_DESC"], as_index=False)
             [["ACRES", "OPERATIONS"]].sum(min_count=1))


# -------------------------------------------------------------------- coverage
def flag(cen, acup_state, acup_any):
    ever_us = set(acup_any.COMMODITY_DESC)
    recent_us = set(acup_any.loc[acup_any.YEAR >= RECENT_FROM, "COMMODITY_DESC"])
    ever_here = set(zip(acup_state.COMMODITY_DESC, acup_state.STATE_ALPHA))
    r = acup_state[acup_state.YEAR >= RECENT_FROM]
    recent_here = set(zip(r.COMMODITY_DESC, r.STATE_ALPHA))

    c = cen.copy()
    c["surveyed_ever_us"] = c.COMMODITY_DESC.isin(ever_us)
    c["surveyed_recent_us"] = c.COMMODITY_DESC.isin(recent_us)
    if "STATE_ALPHA" in c.columns:
        pair = list(zip(c.COMMODITY_DESC, c.STATE_ALPHA))
        c["surveyed_ever_here"] = [x in ever_here for x in pair]
        c["surveyed_recent_here"] = [x in recent_here for x in pair]
    return c


def hill1(x):
    """Effective number of crops: exp(Shannon entropy) of the acreage share vector."""
    x = np.asarray([v for v in x if v is not None and not math.isnan(v) and v > 0], float)
    if x.size == 0:
        return np.nan
    p = x / x.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


# ------------------------------------------------------------ C. PNSP crop groups
def pnsp_forage_share():
    """Share of PNSP-attributed pesticide mass assigned to Alfalfa + Pasture_and_hay."""
    if not os.path.exists(PNSP_CROP):
        return None
    with zipfile.ZipFile(PNSP_CROP) as z:
        name = [n for n in z.namelist() if n.startswith("HighEstimate")][0]
        d = pd.read_csv(io.BytesIO(z.read(name)), sep="\t", dtype=str)
    crops = ["Corn", "Soybeans", "Wheat", "Cotton", "Vegetables_and_fruit", "Rice",
             "Orchards_and_grapes", "Alfalfa", "Pasture_and_hay", "Other_crops"]
    for c in crops:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    tot = d[crops].sum().sum()
    forage = d[["Alfalfa", "Pasture_and_hay"]].sum().sum()
    return dict(total_kg=tot, forage_kg=forage, forage_share=forage / tot,
                years=f"{d.Year.min()}-{d.Year.max()}")


def main():
    os.makedirs(OUT, exist_ok=True)

    acup_any, acup_state = load_acup()
    print("=" * 72)
    print("A. THE FEDERAL PESTICIDE-USE SURVEY RECORD (NASS ACUP)")
    print("=" * 72)
    print(f"chemical-use rows                 : {len(acup_any):,}")
    print(f"years spanned                     : {acup_any.YEAR.min()}-{acup_any.YEAR.max()}")
    print(f"distinct commodities ever         : {acup_any.COMMODITY_DESC.nunique()}")
    print(f"distinct commodities {RECENT_FROM}-2025    : "
          f"{acup_any.loc[acup_any.YEAR >= RECENT_FROM].COMMODITY_DESC.nunique()}")
    print(f"distinct (commodity,state) cells  : "
          f"{len(set(zip(acup_state.COMMODITY_DESC, acup_state.STATE_ALPHA)))}")
    yrs = acup_any.groupby("COMMODITY_DESC").YEAR.nunique().sort_values(ascending=False)
    print(f"median years of coverage per crop : {yrs.median():.0f} of "
          f"{acup_any.YEAR.nunique()} years present in the record")
    print("  most-surveyed crops :", ", ".join(f"{k} ({v})" for k, v in yrs.head(5).items()))
    once = sorted(yrs[yrs == 1].index)
    print(f"  crops surveyed in exactly one year ({len(once)}): {', '.join(once)}")

    # ---- crop-level ledger ----
    nat = flag(load_census("NATIONAL"), acup_state, acup_any).sort_values(
        "ACRES", ascending=False)
    last_yr = acup_any.groupby("COMMODITY_DESC").YEAR.max()
    nat["last_surveyed_year"] = nat.COMMODITY_DESC.map(last_yr)
    nat["n_years_surveyed"] = nat.COMMODITY_DESC.map(yrs)
    nat["status"] = np.where(nat.surveyed_recent_us, f"surveyed {RECENT_FROM}+",
                             np.where(nat.surveyed_ever_us, "lapsed", "never surveyed"))
    nat.to_csv(os.path.join(OUT, "lens_mendez_crop_coverage.csv"), index=False)

    tot_a, tot_o = nat.ACRES.sum(), nat.OPERATIONS.sum()
    print()
    print("=" * 72)
    print("B. AGAINST THE 2022 CENSUS OF AGRICULTURE CROP INVENTORY")
    print("=" * 72)
    print(f"crop base: {tot_a:,.0f} acres, {tot_o:,.0f} crop-growing operation-records,"
          f" {nat.COMMODITY_DESC.nunique()} commodities")
    for st_lab in [f"surveyed {RECENT_FROM}+", "lapsed", "never surveyed"]:
        s = nat[nat.status == st_lab]
        print(f"  {st_lab:<18}: {s.COMMODITY_DESC.nunique():>3} commodities  "
              f"{s.ACRES.sum()/tot_a:>6.1%} of acres  "
              f"{s.OPERATIONS.sum()/tot_o:>6.1%} of operation-records")
    print("\n  largest never-surveyed crops:")
    nev = nat[~nat.surveyed_ever_us].sort_values("ACRES", ascending=False).head(8)
    for _, r in nev.iterrows():
        print(f"    {r.COMMODITY_DESC:<28} {r.ACRES:>12,.0f} ac  "
              f"{r.OPERATIONS:>9,.0f} farms")
    print("\n  crops ranked by number of farms growing them (top 8):")
    for _, r in nat.sort_values("OPERATIONS", ascending=False).head(8).iterrows():
        print(f"    {r.COMMODITY_DESC:<28} {r.OPERATIONS:>9,.0f} farms  "
              f"{r.ACRES:>12,.0f} ac   {r.status}")

    # ---- state roll-up ----
    st = flag(load_census("STATE"), acup_state, acup_any)
    stg = (st.assign(a_ever=st.ACRES.where(st.surveyed_ever_here),
                     a_recent=st.ACRES.where(st.surveyed_recent_here),
                     a_recent_us=st.ACRES.where(st.surveyed_recent_us))
             .groupby("STATE_ALPHA", as_index=False)
             .agg(acres=("ACRES", "sum"), ops=("OPERATIONS", "sum"),
                  acres_ever=("a_ever", "sum"), acres_recent=("a_recent", "sum"),
                  acres_recent_us=("a_recent_us", "sum"),
                  n_crops=("COMMODITY_DESC", "nunique")))
    for c in ("ever", "recent", "recent_us"):
        stg["cov_" + c] = stg["acres_" + c] / stg.acres
    stg = stg.sort_values("cov_recent", ascending=False)
    stg.to_csv(os.path.join(OUT, "lens_mendez_state_coverage.csv"), index=False)
    print("\n  state coverage (share of census crop acres inside the published "
          f"{RECENT_FROM}+ frame):")
    print("    highest:", ", ".join(f"{r.STATE_ALPHA} {r.cov_recent:.0%}"
                                    for _, r in stg.head(6).iterrows()))
    print("    lowest :", ", ".join(f"{r.STATE_ALPHA} {r.cov_recent:.0%}"
                                    for _, r in stg.tail(6).iterrows()))

    # ---- county level: the chart table ----
    cty = flag(load_census("COUNTY"), acup_state, acup_any)
    cty = cty[cty.fips.str.len() == 5]
    g = (cty.assign(a_ever=cty.ACRES.where(cty.surveyed_ever_here),
                    a_recent=cty.ACRES.where(cty.surveyed_recent_here),
                    a_recent_us=cty.ACRES.where(cty.surveyed_recent_us),
                    a_forage=cty.ACRES.where(cty.COMMODITY_DESC.isin(["HAY", "HAYLAGE"])))
            .groupby(["fips", "STATE_ALPHA", "COUNTY_NAME"], as_index=False)
            .agg(acres=("ACRES", "sum"), acres_ever=("a_ever", "sum"),
                 acres_recent=("a_recent", "sum"),
                 acres_recent_us=("a_recent_us", "sum"),
                 acres_hay=("a_forage", "sum"),
                 n_crops=("COMMODITY_DESC", "nunique"), ops=("OPERATIONS", "sum")))
    g = g.merge(cty.groupby("fips")["ACRES"].apply(hill1).rename("eff_crops").reset_index(),
                on="fips", how="left")
    for c in ("ever", "recent", "recent_us"):
        g["cov_" + c] = g["acres_" + c] / g.acres
    g["hay_share"] = g.acres_hay / g.acres
    g = g[(g.acres >= MIN_COUNTY_ACRES) & g.eff_crops.notna()].copy()
    g.to_csv(os.path.join(OUT, "lens_mendez_county_coverage.csv"), index=False)

    print()
    print("=" * 72)
    print("C. GEOGRAPHY OF COVERAGE vs CROP DIVERSITY")
    print("=" * 72)
    print(f"counties with >= {MIN_COUNTY_ACRES:,} census crop acres: {len(g):,} "
          f"({g.acres.sum()/1e6:.1f}M acres, {g.acres.sum()/tot_a:.1%} of the national base)")
    rho, p = spearmanr(g.eff_crops, g.cov_recent)
    print(f"Spearman rho(effective crops, coverage) = {rho:+.3f} (p={p:.2g}) "
          "-- NOT monotone; see bins")

    # decile bins -> the chart series
    g["bin"] = pd.qcut(g.eff_crops, 10, labels=False, duplicates="drop")
    b = (g.groupby("bin")
           .apply(lambda d: pd.Series({
               "counties": len(d),
               "eff_crops_min": d.eff_crops.min(),
               "eff_crops_max": d.eff_crops.max(),
               "eff_crops_median": d.eff_crops.median(),
               "acres": d.acres.sum(),
               "cov_recent": d.acres_recent.sum() / d.acres.sum(),
               "cov_ever": d.acres_ever.sum() / d.acres.sum(),
               "cov_recent_us": d.acres_recent_us.sum() / d.acres.sum(),
               "hay_share": d.acres_hay.sum() / d.acres.sum(),
               "median_county_cov": d.cov_recent.median()}),
                  include_groups=False)
           .reset_index())
    b["decile"] = b.bin + 1
    b.to_csv(os.path.join(OUT, "lens_mendez_diversity_bins.csv"), index=False)
    pd.set_option("display.width", 200)
    print(b[["decile", "counties", "eff_crops_median", "acres", "cov_recent",
             "cov_ever", "hay_share"]].to_string(index=False,
             formatters={"acres": "{:,.0f}".format, "cov_recent": "{:.1%}".format,
                         "cov_ever": "{:.1%}".format, "hay_share": "{:.1%}".format,
                         "eff_crops_median": "{:.2f}".format}))
    peak = b.loc[b.cov_recent.idxmax()]
    print(f"\ncoverage peaks in decile {int(peak.decile)} "
          f"(effective crops {peak.eff_crops_min:.2f}-{peak.eff_crops_max:.2f}, "
          f"median {peak.eff_crops_median:.2f}) at {peak.cov_recent:.1%}; "
          f"D1 {b.cov_recent.iloc[0]:.1%}, D10 {b.cov_recent.iloc[-1]:.1%}")

    # ---- verification pass ----
    print()
    print("=" * 72)
    print("D. VERIFICATION")
    print("=" * 72)
    ctyn = (cty.assign(a_us=cty.ACRES.where(cty.surveyed_recent_us))
               .agg({"ACRES": "sum", "a_us": "sum"}))
    print(f"[1] recent-frame acre share, national census rows : "
          f"{nat.loc[nat.surveyed_recent_us,'ACRES'].sum()/tot_a:.3%}")
    print(f"    same, rebuilt by summing all county rows      : "
          f"{ctyn.a_us/ctyn.ACRES:.3%}")
    stn = st.ACRES.sum()
    print(f"[2] crop-acre base  national rows: {tot_a:,.0f} | "
          f"state rows: {stn:,.0f} ({stn/tot_a-1:+.2%}) | "
          f"county rows: {ctyn.ACRES:,.0f} ({ctyn.ACRES/tot_a-1:+.2%})")
    hay = nat[nat.COMMODITY_DESC == "HAY"].iloc[0]
    hay_st = st[st.COMMODITY_DESC == "HAY"]
    print(f"[3] HAY: national {hay.OPERATIONS:,.0f} farms / {hay.ACRES:,.0f} ac ; "
          f"summed over states {hay_st.OPERATIONS.sum():,.0f} / {hay_st.ACRES.sum():,.0f}")
    print(f"    HAY in ACUP chemical-use record: "
          f"{(acup_any.COMMODITY_DESC == 'HAY').sum()} rows  "
          f"(ANY forage commodity: "
          f"{acup_any.COMMODITY_DESC.str.contains('HAY|ALFALFA|GRASS|PASTURE|FORAGE').sum()})")
    fs = pnsp_forage_share()
    if fs:
        print(f"[4] USGS PNSP state x crop-group ({fs['years']}): "
              f"{fs['forage_kg']/1e6:,.1f} M kg of {fs['total_kg']/1e6:,.1f} M kg "
              f"({fs['forage_share']:.1%}) attributed to Alfalfa + Pasture_and_hay "
              "-- crop groups with no public NASS survey behind them.")

    print("\nwrote:")
    for f in ("lens_mendez_county_coverage.csv", "lens_mendez_diversity_bins.csv",
              "lens_mendez_crop_coverage.csv", "lens_mendez_state_coverage.csv"):
        print("  data/derived/" + f)


if __name__ == "__main__":
    main()
