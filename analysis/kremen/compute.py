"""
Lens: diversified farming systems / landscape ecology (Kremen framework).

Question: the federal pesticide record is organised by county and the federal
practice record by field-level practice. Neither carries landscape
configuration. Can a county-level crop-composition measure stand in for
landscape simplification well enough to test the Meehan et al. (2011) /
Larsen & Noack (2017) claim that simplified landscapes require more insecticide?

What this script builds
-----------------------
1. County crop-composition diversity from the Census of Agriculture
   (2017 primary -- year-matched to the 2018 PNSP estimates; 2022 as an
   independent recomputation).
     - effective number of crops  ENC = exp(Shannon H) over ~45 mutually
       exclusive crop groups, weighted by harvested acres
     - share of harvested cropland in the single largest crop group
     - dominant crop group (for stratification)
     - coverage = sum(group acres) / Census "harvested cropland" acres
2. County conventional-insecticide + acaricide applied mass from the corrected
   PNSP panel (California already dropped, aggregate rows already removed),
   normalised per acre of harvested cropland.
3. The association between them, overall and WITHIN dominant-crop strata.

The within-stratum split is the whole point. USGS builds the county pesticide
estimate by multiplying Census county harvested acreage of each crop by a Crop
Reporting District median pesticide-by-crop application rate
(Thelin & Stone 2013, USGS SIR 2013-5009; Baker & Stone 2015, USGS DS 907).
The county pesticide number is therefore a function of county crop composition
by construction. Any raw correlation between crop composition and pesticide
intensity is partly definitional and carries no landscape-configuration
information at all.

Run from repo root:
    python analysis/kremen/compute.py
Requires pandas, numpy, scipy, pyarrow.
"""

import gzip
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
NASS = ROOT / "data/raw/usda-nass/quickstats-bulk/2026-09-14"
DERIVED = ROOT / "data/derived"
OUTDIR = ROOT / "analysis/kremen"

CENSUS_FILES = {2017: NASS / "qs.census2017.txt.gz", 2022: NASS / "qs.census2022.txt.gz"}

# PNSP years to use. 2018 is the latest; 2017 is the independent replication.
PNSP_PRIMARY = 2018
PNSP_CHECK = 2017

MIN_HARVESTED_ACRES = 10_000      # drop counties with a trivial cropland base
COVERAGE_LO, COVERAGE_HI = 0.85, 1.15

# ----------------------------------------------------------------------------
# 1. Crop groups
# ----------------------------------------------------------------------------
# Each entry is one "crop" for the diversity index. Keys are the group label;
# values are (COMMODITY_DESC, CLASS_DESC, UTIL_PRACTICE_DESC) triples that are
# summed. All are AREA HARVESTED / ACRES / ALL PRODUCTION PRACTICES /
# DOMAIN_DESC == TOTAL / AGG_LEVEL_DESC == COUNTY, except the three aggregate
# horticultural groups at the bottom which use their own statistic category.
#
# Overlapping NASS hierarchy levels are deliberately excluded:
#   - HAY and HAYLAGE are dropped in favour of HAY & HAYLAGE (their union).
#   - WHEAT sub-classes (WINTER, SPRING) are dropped in favour of ALL CLASSES.
#   - COTTON UPLAND/PIMA dropped in favour of ALL CLASSES.
#   - SUNFLOWER OIL/NON-OIL dropped in favour of ALL CLASSES.
#   - Individual GRASSES/LEGUMES seed classes dropped in favour of
#     GRASSES & LEGUMES TOTALS.
#   - Individual vegetables (incl. potatoes, sweet potatoes) are dropped in
#     favour of VEGETABLE TOTALS, IN THE OPEN.
#   - Individual fruits/nuts dropped in favour of ORCHARDS (= citrus +
#     non-citrus + tree nuts, verified against 2022 national totals); BERRY
#     TOTALS is separate because ORCHARDS excludes berries.
AH = "AREA HARVESTED"
ALLP = "ALL PRODUCTION PRACTICES"
ALLU = "ALL UTILIZATION PRACTICES"

CROP_GROUPS = {
    "Corn":            [("CORN", "ALL CLASSES", "GRAIN"),
                        ("CORN", "ALL CLASSES", "SILAGE"),
                        ("CORN", "TRADITIONAL OR INDIAN", ALLU)],
    "Soybeans":        [("SOYBEANS", "ALL CLASSES", ALLU)],
    "Wheat":           [("WHEAT", "ALL CLASSES", ALLU)],
    "Hay & haylage":   [("HAY & HAYLAGE", "ALL CLASSES", ALLU)],
    "Cotton":          [("COTTON", "ALL CLASSES", ALLU)],
    "Sorghum":         [("SORGHUM", "ALL CLASSES", "GRAIN"),
                        ("SORGHUM", "ALL CLASSES", "SILAGE"),
                        ("SORGHUM", "ALL CLASSES", "SYRUP")],
    "Barley":          [("BARLEY", "ALL CLASSES", ALLU)],
    "Oats":            [("OATS", "ALL CLASSES", ALLU)],
    "Rye":             [("RYE", "ALL CLASSES", ALLU)],
    "Triticale":       [("TRITICALE", "ALL CLASSES", ALLU)],
    "Emmer & spelt":   [("EMMER & SPELT", "ALL CLASSES", ALLU)],
    "Buckwheat":       [("BUCKWHEAT", "ALL CLASSES", ALLU)],
    "Millet":          [("MILLET", "PROSO", ALLU)],
    "Rice":            [("RICE", "ALL CLASSES", ALLU)],
    "Wild rice":       [("WILD RICE", "ALL CLASSES", ALLU)],
    "Popcorn":         [("POPCORN", "ALL CLASSES", "SHELLED")],
    "Peanuts":         [("PEANUTS", "ALL CLASSES", ALLU)],
    "Tobacco":         [("TOBACCO", "ALL CLASSES", ALLU)],
    "Sugarbeets":      [("SUGARBEETS", "ALL CLASSES", ALLU)],
    "Sugarcane":       [("SUGARCANE", "ALL CLASSES", "SUGAR & SEED")],
    "Sunflower":       [("SUNFLOWER", "ALL CLASSES", ALLU)],
    "Canola":          [("CANOLA", "ALL CLASSES", ALLU)],
    "Rapeseed":        [("RAPESEED", "ALL CLASSES", ALLU)],
    "Flaxseed":        [("FLAXSEED", "ALL CLASSES", ALLU)],
    "Safflower":       [("SAFFLOWER", "ALL CLASSES", ALLU)],
    "Sesame":          [("SESAME", "ALL CLASSES", ALLU)],
    "Camelina":        [("CAMELINA", "ALL CLASSES", ALLU)],
    "Mustard seed":    [("MUSTARD", "ALL CLASSES", "SEED")],
    "Dry beans":       [("BEANS", "DRY EDIBLE, (EXCL CHICKPEAS & LIMA)", ALLU),
                        ("BEANS", "DRY EDIBLE, LIMA", ALLU)],
    "Dry peas":        [("PEAS", "DRY EDIBLE", ALLU),
                        ("PEAS", "AUSTRIAN WINTER", ALLU),
                        ("PEAS", "DRY, SOUTHERN (COWPEAS)", ALLU)],
    "Chickpeas":       [("CHICKPEAS", "ALL CLASSES", ALLU)],
    "Lentils":         [("LENTILS", "ALL CLASSES", ALLU)],
    "Hops":            [("HOPS", "ALL CLASSES", ALLU)],
    "Mint":            [("MINT", "ALL CLASSES", "OIL")],
    "Dry herbs":       [("HERBS", "DRY", ALLU)],
    "Grass & legume seed": [("GRASSES & LEGUMES TOTALS", "ALL CLASSES", "SEED")],
    "Switchgrass":     [("SWITCHGRASS", "ALL CLASSES", ALLU)],
    "Miscanthus":      [("MISCANTHUS", "ALL CLASSES", ALLU)],
    "Taro":            [("TARO", "ALL CLASSES", ALLU)],
    "Jojoba":          [("JOJOBA", "ALL CLASSES", ALLU)],
    "Guar":            [("GUAR", "ALL CLASSES", ALLU)],
    "Other field crops": [("FIELD CROPS, OTHER", "ALL CLASSES", ALLU)],
}

# Aggregate horticultural groups, keyed by exact SHORT_DESC.
HORT_GROUPS = {
    "Vegetables": "VEGETABLE TOTALS, IN THE OPEN - ACRES HARVESTED",
    "Orchards (fruit & tree nuts)": "ORCHARDS - ACRES BEARING & NON-BEARING",
    "Berries": "BERRY TOTALS - ACRES GROWN",
}

HARVESTED_CROPLAND = "AG LAND, CROPLAND, HARVESTED - ACRES"

# ----------------------------------------------------------------------------
# 2. Insecticide roster
# ----------------------------------------------------------------------------
# Conventional synthetic insecticides, acaricides and insect-active
# nematicides present in the PNSP compound roster. Deliberately EXCLUDED:
#   - soil fumigants (metam, metam-potassium, 1,3-dichloropropene,
#     chloropicrin, methyl bromide, dimethyl disulfide) -- broad biocides tied
#     to a handful of high-value crops; they would swamp everything else
#   - horticultural oils, sulfur, kaolin clay, lime sulfur, cryolite
#   - microbial / botanical biologicals (Bt, spinosad is retained as a
#     fermentation-derived conventional, neem and azadirachtin are not)
#   - defoliants and plant growth regulators that are organophosphates
#     (tribufos, ethephon)
INSECTICIDES = {
    # organophosphates
    "CHLORPYRIFOS", "ACEPHATE", "PHORATE", "TERBUFOS", "DIMETHOATE",
    "DICROTOPHOS", "MALATHION", "PHOSMET", "DIAZINON", "METHYL PARATHION",
    "ETHOPROPHOS", "TEBUPIRIMPHOS", "CHLORETHOXYFOS", "NALED",
    # carbamates
    "CARBARYL", "METHOMYL", "OXAMYL", "ALDICARB",
    # pyrethroids / pyrethrins
    "BIFENTHRIN", "CYHALOTHRIN-LAMBDA", "CYHALOTHRIN-GAMMA", "PERMETHRIN",
    "CYFLUTHRIN", "ZETA-CYPERMETHRIN", "ALPHA CYPERMETHRIN", "CYPERMETHRIN",
    "ESFENVALERATE", "DELTAMETHRIN", "FENPROPATHRIN", "TEFLUTHRIN",
    "PYRETHRINS",
    # neonicotinoids, sulfoximine, butenolide
    "IMIDACLOPRID", "THIAMETHOXAM", "CLOTHIANIDIN", "ACETAMIPRID",
    "DINOTEFURAN", "THIACLOPRID", "SULFOXAFLOR", "FLUPYRADIFURONE",
    # diamides
    "CHLORANTRANILIPROLE", "CYANTRANILIPROLE", "FLUBENDIAMIDE",
    "CYCLANILIPROLE",
    # spinosyns / avermectins
    "SPINOSYN", "SPINETORAM", "ABAMECTIN", "EMAMECTIN",
    # growth regulators / moulting disruptors
    "DIFLUBENZURON", "NOVALURON", "METHOXYFENOZIDE", "PYRIPROXYFEN",
    "BUPROFEZIN", "CYROMAZINE",
    # other insecticides
    "INDOXACARB", "FIPRONIL", "FLONICAMID", "PYMETROZINE", "TOLFENPYRAD",
    "SPIROTETRAMAT",
    # acaricides
    "PROPARGITE", "HEXYTHIAZOX", "SPIRODICLOFEN", "SPIROMESIFEN", "PYRIDABEN",
    "FENPYROXIMATE", "FENBUTATIN OXIDE", "BIFENAZATE", "ETOXAZOLE",
    "CYFLUMETOFEN", "ACEQUINOCYL",
}

NEONICS = {"IMIDACLOPRID", "THIAMETHOXAM", "CLOTHIANIDIN", "ACETAMIPRID",
           "DINOTEFURAN", "THIACLOPRID"}

# ----------------------------------------------------------------------------


def parse_value(s):
    """NASS VALUE is a string: thousands separators plus suppression codes."""
    if s is None:
        return np.nan
    s = s.strip()
    if not s or s.startswith("("):      # (D) withheld, (Z) <half unit, (NA), (H), (L)
        return np.nan
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return np.nan


def read_census_county_acres(path, year):
    """Stream the gzipped Quick Stats file, keeping county ACRES rows only."""
    cols = None
    keep = []
    with gzip.open(path, "rt", encoding="latin-1", newline="") as fh:
        for i, line in enumerate(fh):
            parts = line.rstrip("\n").split("\t")
            if i == 0:
                cols = [c.strip() for c in parts]
                idx = {c: j for j, c in enumerate(cols)}
                continue
            if len(parts) != len(cols):
                continue
            if (parts[idx["AGG_LEVEL_DESC"]] != "COUNTY"
                    or parts[idx["UNIT_DESC"]] != "ACRES"
                    or parts[idx["DOMAIN_DESC"]] != "TOTAL"
                    or parts[idx["YEAR"]] != str(year)):
                continue
            keep.append([parts[idx[c]] for c in (
                "COMMODITY_DESC", "CLASS_DESC", "PRODN_PRACTICE_DESC",
                "UTIL_PRACTICE_DESC", "STATISTICCAT_DESC", "SHORT_DESC",
                "STATE_FIPS_CODE", "COUNTY_CODE", "VALUE")])
    d = pd.DataFrame(keep, columns=[
        "commodity", "cls", "prodn", "util", "stat", "short_desc",
        "state_fips", "county_fips", "value_raw"])
    d["state_fips"] = pd.to_numeric(d.state_fips, errors="coerce")
    d["county_fips"] = pd.to_numeric(d.county_fips, errors="coerce")
    d = d.dropna(subset=["state_fips", "county_fips"])
    d["state_fips"] = d.state_fips.astype(int)
    d["county_fips"] = d.county_fips.astype(int)
    d["acres"] = d.value_raw.map(parse_value)
    d["suppressed"] = d.value_raw.str.strip().str.startswith("(")
    return d


def build_crop_matrix(cen):
    """county x crop-group harvested acres."""
    fc = cen[(cen.stat == AH) & (cen.prodn == ALLP)]
    rows = []
    for label, triples in CROP_GROUPS.items():
        want = set(triples)
        sel = fc[[(c, k, u) in want
                  for c, k, u in zip(fc.commodity, fc.cls, fc.util)]]
        if sel.empty:
            continue
        g = (sel.groupby(["state_fips", "county_fips"])
                .agg(acres=("acres", "sum"),
                     n_suppressed=("suppressed", "sum"))
                .reset_index())
        g["crop_group"] = label
        rows.append(g)
    for label, sd in HORT_GROUPS.items():
        sel = cen[cen.short_desc == sd]
        if sel.empty:
            continue
        g = (sel.groupby(["state_fips", "county_fips"])
                .agg(acres=("acres", "sum"),
                     n_suppressed=("suppressed", "sum"))
                .reset_index())
        g["crop_group"] = label
        rows.append(g)
    m = pd.concat(rows, ignore_index=True)
    m["acres"] = m.acres.fillna(0.0)
    return m


def diversity_table(cen):
    m = build_crop_matrix(cen)
    pos = m[m.acres > 0].copy()

    def per_county(g):
        a = g.acres.to_numpy(dtype=float)
        tot = a.sum()
        p = a / tot
        H = float(-(p * np.log(p)).sum())
        order = np.argsort(-a)
        return pd.Series({
            "group_acres": tot,
            "n_crop_groups": int(len(a)),
            "shannon_H": H,
            "effective_n_crops": math.exp(H),
            "top1_share": float(p[order[0]]),
            "top3_share": float(p[order[:3]].sum()),
            "dominant_crop": g.crop_group.to_numpy()[order[0]],
        })

    div = (pos.groupby(["state_fips", "county_fips"], group_keys=False)
              .apply(per_county, include_groups=False)
              .reset_index())

    hc = cen[cen.short_desc == HARVESTED_CROPLAND][
        ["state_fips", "county_fips", "acres"]].rename(
        columns={"acres": "harvested_cropland_acres"})
    hc = hc.groupby(["state_fips", "county_fips"], as_index=False).max()

    sup = (m.groupby(["state_fips", "county_fips"], as_index=False)
             .n_suppressed.sum()
             .rename(columns={"n_suppressed": "n_suppressed_crop_records"}))

    div = div.merge(hc, on=["state_fips", "county_fips"], how="left")
    div = div.merge(sup, on=["state_fips", "county_fips"], how="left")
    div["coverage"] = div.group_acres / div.harvested_cropland_acres
    return div


def pnsp_county(year):
    d = pd.read_parquet(DERIVED / "pnsp_county_panel_corrected.parquet")
    d = d[d.year == year]
    out = {}
    for tag, col in (("low", "low_kg"), ("high", "high_kg")):
        tot = (d.groupby(["state_fips", "county_fips"])[col].sum()
                .rename(f"total_kg_{tag}"))
        ins = (d[d.compound.isin(INSECTICIDES)]
                 .groupby(["state_fips", "county_fips"])[col].sum()
                 .rename(f"insecticide_kg_{tag}"))
        neo = (d[d.compound.isin(NEONICS)]
                 .groupby(["state_fips", "county_fips"])[col].sum()
                 .rename(f"neonic_kg_{tag}"))
        out[tag] = pd.concat([tot, ins, neo], axis=1)
    p = pd.concat(out.values(), axis=1).reset_index()
    for c in p.columns:
        if c.endswith(("_low", "_high")):
            p[c] = p[c].fillna(0.0)
    return p


def dominant_stratum(crop):
    if crop in ("Corn", "Soybeans"):
        return "Corn / soybean"
    if crop in ("Wheat", "Hay & haylage", "Barley", "Oats", "Rye", "Triticale",
                "Emmer & spelt", "Millet", "Buckwheat", "Grass & legume seed",
                "Popcorn", "Switchgrass", "Miscanthus"):
        return "Hay & small grains"
    if crop in ("Cotton", "Peanuts", "Rice", "Tobacco", "Sorghum", "Sugarcane"):
        return "Southern row crops"
    if crop in ("Vegetables", "Orchards (fruit & tree nuts)", "Berries",
                "Hops", "Mint", "Dry herbs", "Taro"):
        return "Specialty (veg / orchard / berry)"
    return "Other"


def spearman(df, x, y):
    s = df[[x, y]].dropna()
    if len(s) < 10:
        return np.nan, np.nan, len(s)
    rho, p = stats.spearmanr(s[x], s[y])
    return float(rho), float(p), len(s)


def assemble(census_year, pnsp_year):
    cen = read_census_county_acres(CENSUS_FILES[census_year], census_year)
    div = diversity_table(cen)
    pn = pnsp_county(pnsp_year)
    df = div.merge(pn, on=["state_fips", "county_fips"], how="inner")
    df = df[(df.harvested_cropland_acres >= MIN_HARVESTED_ACRES)
            & df.coverage.between(COVERAGE_LO, COVERAGE_HI)].copy()
    for tag in ("low", "high"):
        df[f"insecticide_g_per_acre_{tag}"] = (
            df[f"insecticide_kg_{tag}"] * 1000.0 / df.harvested_cropland_acres)
        df[f"total_g_per_acre_{tag}"] = (
            df[f"total_kg_{tag}"] * 1000.0 / df.harvested_cropland_acres)
    df["stratum"] = df.dominant_crop.map(dominant_stratum)
    df["census_year"] = census_year
    df["pnsp_year"] = pnsp_year
    return df


def report(df, label):
    print(f"\n===== {label}  (n={len(df)} counties) =====")
    print(f"harvested cropland covered: "
          f"{df.harvested_cropland_acres.sum()/1e6:,.1f} M acres")
    print(f"ENC  median {df.effective_n_crops.median():.2f}  "
          f"p10 {df.effective_n_crops.quantile(.1):.2f}  "
          f"p90 {df.effective_n_crops.quantile(.9):.2f}")
    for ycol in ("insecticide_g_per_acre_high", "insecticide_g_per_acre_low"):
        rho, p, n = spearman(df, "effective_n_crops", ycol)
        print(f"  ALL   ENC vs {ycol:34s} rho={rho:+.3f} p={p:.2e} n={n}")
    rho, p, n = spearman(df, "top1_share", "insecticide_g_per_acre_high")
    print(f"  ALL   top1_share vs insecticide (high)      rho={rho:+.3f} "
          f"p={p:.2e} n={n}")
    print("  --- within dominant-crop stratum (EPest-high) ---")
    for s, g in df.groupby("stratum"):
        rho, p, n = spearman(g, "effective_n_crops",
                             "insecticide_g_per_acre_high")
        med = g.insecticide_g_per_acre_high.median()
        print(f"  {s:34s} n={n:5d} median={med:7.1f} g/ac  rho={rho:+.3f} "
              f"p={p:.2e}")
    return df


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("Building primary: Census 2017 crop composition x PNSP 2018 use")
    main_df = assemble(2017, PNSP_PRIMARY)
    report(main_df, "Census 2017 / PNSP 2018")

    print("\nBuilding replication A: Census 2022 crop composition x PNSP 2018")
    alt_census = assemble(2022, PNSP_PRIMARY)
    report(alt_census, "Census 2022 / PNSP 2018")

    print("\nBuilding replication B: Census 2017 crop composition x PNSP 2017")
    alt_year = assemble(2017, PNSP_CHECK)
    report(alt_year, "Census 2017 / PNSP 2017")

    # stability of the diversity measure itself across census vintages
    j = main_df[["state_fips", "county_fips", "effective_n_crops"]].merge(
        alt_census[["state_fips", "county_fips", "effective_n_crops"]],
        on=["state_fips", "county_fips"], suffixes=("_2017", "_2022"))
    rho, p = stats.spearmanr(j.effective_n_crops_2017, j.effective_n_crops_2022)
    print(f"\nENC 2017 vs ENC 2022 across {len(j)} counties: "
          f"Spearman rho={rho:+.3f} p={p:.2e}")

    # insecticide roster coverage check
    d18 = pd.read_parquet(DERIVED / "pnsp_county_panel_corrected.parquet")
    d18 = d18[d18.year == PNSP_PRIMARY]
    tot = d18.high_kg.sum()
    ins = d18[d18.compound.isin(INSECTICIDES)].high_kg.sum()
    missing = sorted(INSECTICIDES - set(d18.compound.unique()))
    print(f"\n2018 EPest-high national (no CA): total {tot/1e6:,.2f} M kg; "
          f"roster insecticide+acaricide {ins/1e6:,.2f} M kg "
          f"({100*ins/tot:.2f}% of mass); "
          f"{len(INSECTICIDES)-len(missing)} of {len(INSECTICIDES)} roster "
          f"compounds present")
    if missing:
        print("  roster compounds absent from 2018:", ", ".join(missing))

    # neonicotinoid seed-treatment discontinuity (USGS stopped estimating seed
    # treatments beginning with the 2015 estimates) -- an in-data check
    dall = pd.read_parquet(DERIVED / "pnsp_county_panel_corrected.parquet")
    neo = (dall[dall.compound.isin(NEONICS)]
           .groupby("year").high_kg.sum() / 1e6)
    print("\nNeonicotinoid EPest-high national mass, M kg (CA excluded):")
    print(neo.loc[2010:2018].round(3).to_string())

    # ---------------- chart table ----------------
    # decile of effective number of crops, within stratum, median insecticide
    # intensity. The chart claim: the pooled gradient is crop identity.
    df = main_df.copy()
    df["enc_decile"] = pd.qcut(df.effective_n_crops, 10, labels=False) + 1
    dec_edges = pd.qcut(df.effective_n_crops, 10).cat.categories

    parts = []
    allrows = (df.groupby("enc_decile")
                 .agg(n_counties=("effective_n_crops", "size"),
                      enc_median=("effective_n_crops", "median"),
                      insecticide_g_per_acre_median=(
                          "insecticide_g_per_acre_high", "median"),
                      insecticide_g_per_acre_p25=(
                          "insecticide_g_per_acre_high",
                          lambda s: s.quantile(.25)),
                      insecticide_g_per_acre_p75=(
                          "insecticide_g_per_acre_high",
                          lambda s: s.quantile(.75)),
                      harvested_acres=("harvested_cropland_acres", "sum"))
                 .reset_index())
    allrows["series"] = "All counties"
    parts.append(allrows)

    for s, g in df.groupby("stratum"):
        if len(g) < 100:
            continue
        r = (g.groupby("enc_decile")
              .agg(n_counties=("effective_n_crops", "size"),
                   enc_median=("effective_n_crops", "median"),
                   insecticide_g_per_acre_median=(
                       "insecticide_g_per_acre_high", "median"),
                   insecticide_g_per_acre_p25=(
                       "insecticide_g_per_acre_high",
                       lambda x: x.quantile(.25)),
                   insecticide_g_per_acre_p75=(
                       "insecticide_g_per_acre_high",
                       lambda x: x.quantile(.75)),
                   harvested_acres=("harvested_cropland_acres", "sum"))
              .reset_index())
        r["series"] = s
        r = r[r.n_counties >= 15]
        parts.append(r)

    chart = pd.concat(parts, ignore_index=True)
    chart["enc_decile_lo"] = chart.enc_decile.map(
        lambda i: round(float(dec_edges[int(i) - 1].left), 3))
    chart["enc_decile_hi"] = chart.enc_decile.map(
        lambda i: round(float(dec_edges[int(i) - 1].right), 3))

    # attach the within-series Spearman so the chart can annotate it
    rho_map = {"All counties": spearman(df, "effective_n_crops",
                                        "insecticide_g_per_acre_high")}
    for s, g in df.groupby("stratum"):
        rho_map[s] = spearman(g, "effective_n_crops",
                              "insecticide_g_per_acre_high")
    chart["series_spearman_rho"] = chart.series.map(lambda s: round(rho_map[s][0], 3))
    chart["series_spearman_p"] = chart.series.map(lambda s: rho_map[s][1])
    chart["series_n_counties"] = chart.series.map(lambda s: rho_map[s][2])

    chart = chart[["series", "enc_decile", "enc_decile_lo", "enc_decile_hi",
                   "enc_median", "n_counties", "harvested_acres",
                   "insecticide_g_per_acre_p25",
                   "insecticide_g_per_acre_median",
                   "insecticide_g_per_acre_p75",
                   "series_spearman_rho", "series_spearman_p",
                   "series_n_counties"]].round(
        {"enc_median": 3, "insecticide_g_per_acre_p25": 2,
         "insecticide_g_per_acre_median": 2, "insecticide_g_per_acre_p75": 2})
    out_chart = DERIVED / "lens_kremen_cropdiversity_vs_insecticide.csv"
    chart.to_csv(out_chart, index=False)
    print(f"\nwrote {out_chart}  ({len(chart)} rows)")

    # county-level table, for audit
    cols = ["state_fips", "county_fips", "census_year", "pnsp_year",
            "harvested_cropland_acres", "group_acres", "coverage",
            "n_crop_groups", "n_suppressed_crop_records", "shannon_H",
            "effective_n_crops", "top1_share", "top3_share", "dominant_crop",
            "stratum", "total_kg_high", "insecticide_kg_high",
            "neonic_kg_high", "insecticide_kg_low",
            "insecticide_g_per_acre_high", "insecticide_g_per_acre_low",
            "total_g_per_acre_high"]
    out_cty = DERIVED / "lens_kremen_county_detail.csv"
    main_df[cols].round(6).to_csv(out_cty, index=False)
    print(f"wrote {out_cty}  ({len(main_df)} rows)")


if __name__ == "__main__":
    main()
