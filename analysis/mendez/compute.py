#!/usr/bin/env python3
"""
lens: mendez -- "who defined what got measured?"

Builds a map of which farming is legible to the federal pesticide-use
measurement system, by contrasting two USDA NASS products that share one
controlled vocabulary (COMMODITY_DESC):

  A. The Agricultural Chemical Use Program (ACUP) survey record
     -- qs.environmental_*.txt.gz, SOURCE_DESC = SURVEY,
        DOMAIN_DESC containing "CHEMICAL".
     This is the federal record of *what got measured*: which crop, in which
     state, in which year, NASS published a pesticide-use estimate for.

  B. The 2022 Census of Agriculture crop inventory
     -- qs.census2022.txt.gz, SECTOR_DESC = CROPS.
     This is the denominator of *what is actually grown*: acres and number of
     operations, by crop, by county.

Outputs (repo-root relative):
  data/derived/lens_mendez_county_coverage.csv   <- primary chart CSV
  data/derived/lens_mendez_crop_coverage.csv     <- crop-level ledger
  data/derived/lens_mendez_state_coverage.csv    <- state roll-up

Run from repo root:  python3 analysis/mendez/compute.py
"""

import os
import sys
import math
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BULK = os.path.join(ROOT, "data/raw/usda-nass/quickstats-bulk/2026-09-14")
ENV = os.path.join(BULK, "qs.environmental_20260912.txt.gz")
CEN = os.path.join(BULK, "qs.census2022.txt.gz")
OUT = os.path.join(ROOT, "data/derived")

READ_KW = dict(sep="\t", encoding="latin-1", dtype=str, quoting=3, chunksize=400_000,
               na_filter=False, low_memory=False)

# Census commodity rows that are roll-ups of other rows in the same table.
# Including them would double-count acreage.
ROLLUPS = {
    "HAY & HAYLAGE",          # = HAY + HAYLAGE
    "BERRY TOTALS", "CITRUS TOTALS", "NON-CITRUS TOTALS", "TREE NUT TOTALS",
    "ORCHARDS", "FRUIT & TREE NUT TOTALS",
    "FLORICULTURE TOTALS", "NURSERY TOTALS", "NURSERY & FLORICULTURE TOTALS",
    "BEDDING PLANT TOTALS", "CUT FLOWERS & CUT CULTIVATED GREENS",
    "VEGETABLE TOTALS", "CROP TOTALS", "FIELD CROP TOTALS",
    "SOD & SEED TOTALS", "PROPAGATIVE MATERIAL TOTALS",
    "HORTICULTURE TOTALS", "FOOD CROPS GROWN UNDER PROTECTION",
}

SUPPRESSED = {"(D)", "(Z)", "(NA)", "(X)", "(L)", "(H)", "(S)", ""}

RECENT_FROM = 2013   # two full ACUP rotation cycles back from 2025


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
    """(commodity, state, year) cells for which a chemical-use estimate exists."""
    keep = []
    for ch in pd.read_csv(ENV, **READ_KW):
        ch.columns = [c.strip() for c in ch.columns]
        m = (ch.SOURCE_DESC == "SURVEY") & ch.DOMAIN_DESC.str.contains("CHEMICAL", na=False)
        if m.any():
            keep.append(ch.loc[m, ["COMMODITY_DESC", "AGG_LEVEL_DESC", "STATE_ALPHA",
                                   "STATE_FIPS_CODE", "YEAR", "DOMAIN_DESC"]])
    a = pd.concat(keep, ignore_index=True)
    a["YEAR"] = a.YEAR.astype(int)
    st = a[a.AGG_LEVEL_DESC == "STATE"].copy()
    return a, st


# ------------------------------------------------------- B. Census crop inventory
def load_census(level):
    """Census 2022 crop acres + operations at `level` ('COUNTY' | 'STATE' | 'NATIONAL')."""
    keep = []
    for ch in pd.read_csv(CEN, **READ_KW):
        ch.columns = [c.strip() for c in ch.columns]
        m = ((ch.SECTOR_DESC == "CROPS")
             & (ch.AGG_LEVEL_DESC == level)
             & (ch.DOMAIN_DESC == "TOTAL")
             & (ch.PRODN_PRACTICE_DESC == "ALL PRODUCTION PRACTICES")
             & (ch.UNIT_DESC.isin(["ACRES", "OPERATIONS"]))
             & (ch.STATISTICCAT_DESC.isin(
                 ["AREA HARVESTED", "AREA BEARING", "AREA GROWN", "AREA IN PRODUCTION"])))
        if m.any():
            cols = ["GROUP_DESC", "COMMODITY_DESC", "CLASS_DESC", "UTIL_PRACTICE_DESC",
                    "STATISTICCAT_DESC", "UNIT_DESC", "VALUE",
                    "STATE_ALPHA", "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME"]
            keep.append(ch.loc[m, cols])
    d = pd.concat(keep, ignore_index=True)

    # one area concept per crop group, so tree-fruit "bearing" and row-crop
    # "harvested" are not stacked on top of each other
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

    # De-duplicate the two NASS hierarchy axes. Where an "ALL ..." roll-up row
    # exists for a commodity within a geography, it *is* the total and the
    # sub-rows are its parts; where it does not, the sub-rows are the total.
    def dedupe(sub, col, allval):
        if (sub[col] == allval).any():
            return sub[sub[col] == allval]
        return sub

    out = []
    for _, sub in p.groupby(geo + ["COMMODITY_DESC"], sort=False):
        sub = dedupe(sub, "CLASS_DESC", "ALL CLASSES")
        sub = dedupe(sub, "UTIL_PRACTICE_DESC", "ALL UTILIZATION PRACTICES")
        out.append(sub)
    p = pd.concat(out, ignore_index=True)

    return (p.groupby(geo + ["GROUP_DESC", "COMMODITY_DESC"], as_index=False)
             [["ACRES", "OPERATIONS"]].sum(min_count=1))


# -------------------------------------------------------------------- coverage
def flag(cen, acup_state, acup_any):
    """Attach ACUP coverage flags to a census crop x geography table."""
    ever_any = set(acup_any.COMMODITY_DESC.unique())
    recent_any = set(acup_any.loc[acup_any.YEAR >= RECENT_FROM, "COMMODITY_DESC"].unique())
    ever_st = set(zip(acup_state.COMMODITY_DESC, acup_state.STATE_ALPHA))
    recent_st = set(zip(acup_state.loc[acup_state.YEAR >= RECENT_FROM, "COMMODITY_DESC"],
                        acup_state.loc[acup_state.YEAR >= RECENT_FROM, "STATE_ALPHA"]))

    c = cen.copy()
    c["surveyed_ever_us"] = c.COMMODITY_DESC.isin(ever_any)
    c["surveyed_recent_us"] = c.COMMODITY_DESC.isin(recent_any)
    if "STATE_ALPHA" in c.columns:
        pair = list(zip(c.COMMODITY_DESC, c.STATE_ALPHA))
        c["surveyed_ever_here"] = [p in ever_st for p in pair]
        c["surveyed_recent_here"] = [p in recent_st for p in pair]
    return c


def hill1(x):
    """Effective number of crops = exp(Shannon entropy) of the acreage share vector."""
    x = np.asarray([v for v in x if v is not None and not math.isnan(v) and v > 0], float)
    if x.size == 0:
        return np.nan
    p = x / x.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def main():
    os.makedirs(OUT, exist_ok=True)

    acup_any, acup_state = load_acup()
    print(f"ACUP chemical-use rows: {len(acup_any):,}")
    print(f"  distinct commodities ever: {acup_any.COMMODITY_DESC.nunique()}")
    print(f"  distinct commodities {RECENT_FROM}-2025: "
          f"{acup_any.loc[acup_any.YEAR>=RECENT_FROM].COMMODITY_DESC.nunique()}")
    print(f"  distinct (commodity,state) cells ever: "
          f"{len(set(zip(acup_state.COMMODITY_DESC, acup_state.STATE_ALPHA)))}")
    print(f"  years: {acup_any.YEAR.min()}-{acup_any.YEAR.max()}")

    # ---- crop-level ledger (national) ----
    nat = load_census("NATIONAL")
    nat = flag(nat, acup_state, acup_any)
    nat = nat.sort_values("ACRES", ascending=False)
    nat.to_csv(os.path.join(OUT, "lens_mendez_crop_coverage.csv"), index=False)

    tot_a, tot_o = nat.ACRES.sum(), nat.OPERATIONS.sum()
    print(f"\nCensus 2022 crop base: {tot_a:,.0f} acres across "
          f"{nat.COMMODITY_DESC.nunique()} commodities")
    for col, lab in [("surveyed_ever_us", "ever in ACUP"),
                     ("surveyed_recent_us", f"in ACUP {RECENT_FROM}+")]:
        s = nat[nat[col]]
        print(f"  {lab}: {s.COMMODITY_DESC.nunique()} commodities, "
              f"{s.ACRES.sum()/tot_a:6.1%} of acres, "
              f"{s.OPERATIONS.sum()/tot_o:6.1%} of crop-growing operations")

    # ---- state roll-up ----
    st = flag(load_census("STATE"), acup_state, acup_any)
    stg = (st.assign(a_ever=st.ACRES.where(st.surveyed_ever_here),
                     a_recent=st.ACRES.where(st.surveyed_recent_here),
                     o_ever=st.OPERATIONS.where(st.surveyed_ever_here))
             .groupby("STATE_ALPHA", as_index=False)
             .agg(acres=("ACRES", "sum"), ops=("OPERATIONS", "sum"),
                  acres_ever=("a_ever", "sum"), acres_recent=("a_recent", "sum"),
                  ops_ever=("o_ever", "sum"), n_crops=("COMMODITY_DESC", "nunique")))
    stg["cov_acres_ever"] = stg.acres_ever / stg.acres
    stg["cov_acres_recent"] = stg.acres_recent / stg.acres
    stg["cov_ops_ever"] = stg.ops_ever / stg.ops
    stg = stg.sort_values("cov_acres_recent", ascending=False)
    stg.to_csv(os.path.join(OUT, "lens_mendez_state_coverage.csv"), index=False)

    # ---- county level: the chart table ----
    cty = flag(load_census("COUNTY"), acup_state, acup_any)
    cty = cty[cty.fips.str.len() == 5]
    g = (cty.assign(a_ever=cty.ACRES.where(cty.surveyed_ever_here),
                    a_recent=cty.ACRES.where(cty.surveyed_recent_here))
            .groupby(["fips", "STATE_ALPHA", "COUNTY_NAME"], as_index=False)
            .agg(acres=("ACRES", "sum"), acres_ever=("a_ever", "sum"),
                 acres_recent=("a_recent", "sum"),
                 n_crops=("COMMODITY_DESC", "nunique"),
                 ops=("OPERATIONS", "sum")))
    div = (cty.groupby("fips")["ACRES"].apply(hill1).rename("eff_crops").reset_index())
    g = g.merge(div, on="fips", how="left")
    g["cov_acres_ever"] = g.acres_ever / g.acres
    g["cov_acres_recent"] = g.acres_recent / g.acres

    # counties with a real cropland base and a measurable diversity figure
    g = g[(g.acres >= 1000) & g.eff_crops.notna()].copy()
    g.to_csv(os.path.join(OUT, "lens_mendez_county_coverage.csv"), index=False)

    print(f"\nCounties with >=1,000 census crop acres: {len(g):,}")
    from scipy.stats import spearmanr
    rho, p = spearmanr(g.eff_crops, g.cov_acres_recent)
    print(f"  Spearman rho(effective crops, coverage {RECENT_FROM}+) = "
          f"{rho:+.3f}  p = {p:.3g}")
    q = pd.qcut(g.eff_crops, 5, labels=["Q1 least diverse", "Q2", "Q3", "Q4",
                                        "Q5 most diverse"])
    print((g.groupby(q, observed=True)
             .apply(lambda d: pd.Series({
                 "counties": len(d),
                 "median_eff_crops": d.eff_crops.median(),
                 "acres_M": d.acres.sum() / 1e6,
                 "cov_acres_recent": d.acres_recent.sum() / d.acres.sum(),
                 "cov_acres_ever": d.acres_ever.sum() / d.acres.sum()}),
                    include_groups=False)).to_string())

    print("\nwrote:")
    for f in ("lens_mendez_crop_coverage.csv", "lens_mendez_state_coverage.csv",
              "lens_mendez_county_coverage.csv"):
        print("  data/derived/" + f)


if __name__ == "__main__":
    main()
