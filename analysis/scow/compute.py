#!/usr/bin/env python3
"""Evidence-hierarchy audit of the federal soil-biology record.

Question
--------
For the pesticide mass actually applied to US cropland, what *tier* of
soil-biological evidence exists in the federal record, and how deep is it?

The framing is that of long-term replicated agroecosystem experiments
(Russell Ranch / LTRAS; Rothamsted; the Morrow Plots): a claim about how a
management input changes soil biology is only as good as the design that
produced it. A 48-hour filter-paper contact assay on one earthworm species
is not the same kind of object as a randomised, replicated, multi-year field
trial, and stacking them into one "the science shows" pile is precisely the
error this audit exists to expose.

So: for each compound in the corrected PNSP county panel, and for each of
four NON-TARGET soil functional groups, find the highest design tier at which
the ECOTOX full release holds at least k independent published studies; then
weight compounds by 2018 applied mass.

Design tiers
------------
0  No record             no soil-habitat test on that group, at any design
1  Lab, not in soil      exposure on filter paper / agar / culture / water
2  Lab, in soil, acute   soil matrix, <= 14 d              (OECD 207-style)
3  Lab, in soil, chronic soil matrix, > 14 d or CHRONIC    (OECD 222/232-style)
4  Field, < 1 year       test_location FIELDN/FIELDA/FIELDU
5  Field, >= 1 year      field, study duration >= 365 d

Depth: a tier counts as attained only if at least `k` DISTINCT ECOTOX
reference_numbers (published studies) sit at that tier or above. k=2 is the
headline (one unreplicated test row is not an established result); k=1 is
carried alongside as the most generous possible reading of the record.

Functional groups
-----------------
Only non-target soil biota. Plant-pathogenic fungi and soil-dwelling
arthropod/nematode crop pests are excluded on purpose: a trial asking whether
a fungicide suppressed Rhizoctonia, or whether a nematicide killed cyst
nematodes, is an efficacy trial against a target organism and says nothing
about non-target soil function. The script prints how much of the record that
exclusion removes.

Joins
-----
PNSP compound -> DTXSID (data/derived/compound_crosswalk_full.csv)
             -> ECOTOX validation/chemicals.txt cas_number
CAS sets are then expanded by systematic-name containment so that salts and
tank mixes of the same parent count as evidence (a deliberately generous
direction: it can only make the record look better than it is). Never joined
on common name -- glyphosate is filed as N-(Phosphonomethyl)glycine.

Run from anywhere:  python3 analysis/scow/compute.py
"""
import glob
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
OUT_LADDER = DERIVED / "lens_scow_soil_evidence_ladder.csv"
OUT_COMPOUND = DERIVED / "lens_scow_compound_tiers.csv"

ZIPS = sorted(glob.glob(str(ROOT / "data/raw/epa/ecotox/**/ecotox_ascii_*.zip"), recursive=True))
if not ZIPS:
    sys.exit("no ECOTOX release found under data/raw/epa/ecotox/")
Z = ZIPS[0]
PRE = Path(Z).name.replace(".zip", "") + "/"

K_HEADLINE = 2   # independent studies required to credit a tier
K_GENEROUS = 1


def read(member, usecols=None):
    with zipfile.ZipFile(Z) as zf, zf.open(PRE + member) as fh:
        return pd.read_csv(fh, sep="|", usecols=usecols, low_memory=False,
                           encoding="latin-1", on_bad_lines="skip")


# ------------------------------------------------------ compound -> CAS set

# DTXSID missing or left ambiguous in the crosswalk, but large enough by mass
# to matter. CAS written as integers, matching ECOTOX's cas_number encoding.
MANUAL_CAS = {
    "METOLACHLOR-S": 87392129,   # S-metolachlor,        87392-12-9
    "2,4-D": 94757,              # crosswalk unresolved across salts/esters
    "DICHLOROPROPENE": 542756,   # 1,3-dichloropropene,  542-75-6
    "CHLOROPICRIN": 76062,       # 76-06-2
    "MCPA": 94746,               # 94-74-6
    "COPPER HYDROXIDE": 20427592,
    "METAM": 137428,             # metam-sodium, 137-42-8 (PNSP METAM is the Na salt;
                                 # the crosswalk DTXSID resolves to the free acid)
    "METAM POTASSIUM": 137417,
}


def build_cas_sets(chem, crosswalk, compounds):
    """{compound: set(cas ints)} plus a short note on how each was resolved."""
    chem_d = chem.dropna(subset=["dtxsid"]).drop_duplicates("dtxsid").set_index("dtxsid")
    dtx = crosswalk.dropna(subset=["dtxsid"]).drop_duplicates("pnsp_compound") \
                   .set_index("pnsp_compound").dtxsid
    names = chem.chemical_name.fillna("")
    cas_all = pd.to_numeric(chem.cas_number, errors="coerce")

    out, notes = {}, {}
    for c in compounds:
        seed, how = set(), []
        d = dtx.get(c)
        if isinstance(d, str) and d in chem_d.index:
            v = chem_d.cas_number.get(d)
            if pd.notna(v):
                seed.add(int(v))
                how.append("dtxsid")
        if c in MANUAL_CAS:
            seed.add(MANUAL_CAS[c])
            how.append("manual")
        if not seed:
            out[c], notes[c] = set(), "unresolved"
            continue
        expanded = set(seed)
        for cas in seed:
            hit = chem[cas_all == cas]
            if hit.empty:
                continue
            parent = str(hit.chemical_name.iloc[0])
            if len(parent) >= 10:   # guard against generic short names
                fam = cas_all[names.str.contains(parent, case=False, regex=False, na=False)]
                expanded |= {int(x) for x in fam.dropna()}
        out[c] = expanded
        notes[c] = "+".join(how) + (f"+name_family({len(expanded) - len(seed)})"
                                    if len(expanded) > len(seed) else "")
    return out, notes


# ------------------------------------------------------------ tier machinery

SOIL_MEDIA = {"NAT", "MIN", "ART", "UKS", "HUM", "LIT"}
CHRONIC_TYPES = {"CHRONIC", "SBCHRON", "GEN", "FLC", "PLC"}
DAY = {"h": 1 / 24.0, "d": 1.0, "wk": 7.0, "mo": 30.44, "yr": 365.25, "mi": 1 / 1440.0}

GROUPS = {
    # detritivores / bioturbators -- OECD 207 & 222 test taxa
    "Earthworms & potworms":
        lambda s: s.phylum_division.eq("Annelida"),
    # mesofauna -- OECD 232 (Collembola) & 226 (predatory mites)
    "Springtails & soil mites":
        lambda s: s["class"].isin(["Entognatha", "Arachnida"]),
    # the plant-symbiont fungi the soil-health literature is actually about
    "Mycorrhizal fungi":
        lambda s: s.phylum_division.eq("Glomeromycota"),
    # the nutrient cyclers -- OECD 216/217 subject matter
    "Soil bacteria & protozoa":
        lambda s: s.kingdom.isin(["Monera", "Protista"]) | s.phylum_division.eq("Cyanophycota"),
}
TIER_LABEL = {
    0: "No record",
    1: "Lab, not in soil",
    2: "Lab, in soil, acute (<=14 d)",
    3: "Lab, in soil, chronic (>14 d)",
    4: "Field, single season (<1 yr)",
    5: "Field, >=1 year",
}
TIERS = [0, 1, 2, 3, 4, 5]


def assign_tier(df):
    loc = df.test_location.astype(str).str.rstrip("/")
    med = df.media_type.astype(str).str.rstrip("/")
    ttype = df.test_type.astype(str).str.rstrip("/")
    dur = df.duration_d
    field = loc.str.startswith("FIELD")
    in_soil = med.isin(SOIL_MEDIA)
    chronic = ttype.isin(CHRONIC_TYPES) | (dur > 14)
    t = pd.Series(1, index=df.index, dtype=int)
    t = t.mask(in_soil, 2)
    t = t.mask(in_soil & chronic, 3)
    t = t.mask(field, 4)
    t = t.mask(field & (dur >= 365), 5)
    return t


def highest_tier(ref_tiers, k):
    """Highest T with >= k distinct studies at tier >= T. ref_tiers: Series of
    tier per distinct reference_number. Returns 0 if nothing qualifies."""
    if len(ref_tiers) == 0:
        return 0
    for T in (5, 4, 3, 2, 1):
        if (ref_tiers >= T).sum() >= k:
            return T
    return 0


def main():
    chem = read("validation/chemicals.txt")
    species = read("validation/species.txt")
    tests = read("tests.txt", usecols=[
        "test_id", "reference_number", "test_cas", "species_number",
        "organism_habitat", "study_duration_mean", "study_duration_unit",
        "test_type", "test_location", "media_type"])
    results = read("results.txt", usecols=["test_id", "endpoint"])

    # a test is evidence only if it reported at least one endpoint
    ep = results.endpoint.astype(str).str.strip()
    scored = set(results.loc[results.endpoint.notna() & ~ep.isin(["", "NR", "NC", "--"]),
                             "test_id"])

    soil_all = tests[tests.organism_habitat.eq("Soil")].merge(
        species[["species_number", "kingdom", "phylum_division", "class",
                 "tax_order", "family", "latin_name"]],
        on="species_number", how="left")
    soil = soil_all[soil_all.test_id.isin(scored)].copy()
    soil["cas"] = pd.to_numeric(soil.test_cas, errors="coerce")
    soil["duration_d"] = (pd.to_numeric(soil.study_duration_mean, errors="coerce")
                          * soil.study_duration_unit.astype(str).str.rstrip("/").map(DAY))
    soil["tier"] = assign_tier(soil)

    # ---- 1. what the soil-habitat record is made of -----------------------
    print(f"ECOTOX release : {Path(Z).name}")
    print(f"soil-habitat tests: {len(soil_all):,} from {soil_all.reference_number.nunique():,} "
          f"published studies ({len(soil):,} tests report an endpoint)\n")
    print(f"{'':<32}{'tests':>9}{'studies':>9}{'field tests':>13}{'field studies':>15}")
    def line(name, sub):
        f = sub[sub.tier >= 4]
        print(f"  {name:<30}{len(sub):>9,}{sub.reference_number.nunique():>9,}"
              f"{len(f):>13,}{f.reference_number.nunique():>15,}")
    for g, sel in GROUPS.items():
        line(g, soil[sel(soil)])
    line("[excluded] other fungi",
         soil[soil.kingdom.eq("Fungi") & ~soil.phylum_division.eq("Glomeromycota")])
    line("[excluded] nematodes",  soil[soil.phylum_division.eq("Nematoda")])
    line("[excluded] insects",    soil[soil["class"].eq("Insecta")])
    line("[excluded] plants",     soil[soil.kingdom.eq("Plantae")])

    bact = soil_all[soil_all.kingdom.isin(["Monera", "Protista"])
                    | soil_all.phylum_division.eq("Cyanophycota")]
    print(f"\n  the entire soil bacteria/protozoa record: {len(bact)} tests, "
          f"{bact.reference_number.nunique()} studies, "
          f"{pd.to_numeric(bact.test_cas, errors='coerce').nunique()} chemicals, "
          f"{(bact.test_location.astype(str).str.startswith('FIELD')).sum()} field test(s)")
    print("  its five commonest taxa: " +
          ", ".join(bact.latin_name.value_counts().head(5).index))

    # ---- 2. applied mass --------------------------------------------------
    panel = pd.read_parquet(DERIVED / "pnsp_county_panel_corrected.parquet")
    p18 = panel[panel.year == 2018]
    use_hi = p18.groupby("compound").high_kg.sum() / 1e6
    use_lo = p18.groupby("compound").low_kg.sum() / 1e6
    use_hi = use_hi[use_hi > 0].sort_values(ascending=False)
    total_hi = use_hi.sum()
    total_lo = use_lo.reindex(use_hi.index).sum()
    print(f"\n2018 applied mass (corrected panel, California excluded): "
          f"{total_hi:,.1f} M kg over {len(use_hi)} compounds")

    crosswalk = pd.read_csv(DERIVED / "compound_crosswalk_full.csv")
    cas_sets, notes = build_cas_sets(chem, crosswalk, list(use_hi.index))
    resolved = {c for c, s in cas_sets.items() if s}
    m_res = use_hi[use_hi.index.isin(resolved)].sum()
    print(f"CAS resolved for {len(resolved)}/{len(use_hi)} compounds "
          f"= {m_res:,.1f} M kg ({100 * m_res / total_hi:.1f}% of mass)")
    unres = use_hi[~use_hi.index.isin(resolved)]
    print("  largest unresolved: " +
          ", ".join(f"{c} ({v:,.1f} M kg)" for c, v in unres.head(4).items()))

    # ---- 3. per-compound highest tier ------------------------------------
    # collapse each group to one tier per (cas, reference): a study is one vote
    per_ref = {g: soil[sel(soil)].groupby(["cas", "reference_number"]).tier.max()
               for g, sel in GROUPS.items()}

    rows = []
    for c in use_hi.index:
        cs = sorted(cas_sets[c])
        for g in GROUPS:
            if not cs:
                rows.append({"compound": c, "biota_group": g,
                             "use_2018_Mkg_high": float(use_hi[c]),
                             "use_2018_Mkg_low": float(use_lo.get(c, np.nan)),
                             "n_studies": np.nan, "n_tests": np.nan,
                             "tier": np.nan, "tier_generous": np.nan,
                             "tier_label": "CAS unresolved",
                             "cas_resolution": notes[c], "n_cas_matched": 0})
                continue
            s = per_ref[g]
            rt = s[s.index.get_level_values("cas").isin(cs)]
            t = highest_tier(rt, K_HEADLINE)
            tg = highest_tier(rt, K_GENEROUS)
            sub = soil[GROUPS[g](soil) & soil.cas.isin(cs)]
            rows.append({"compound": c, "biota_group": g,
                         "use_2018_Mkg_high": float(use_hi[c]),
                         "use_2018_Mkg_low": float(use_lo.get(c, np.nan)),
                         "n_studies": int(rt.index.get_level_values(1).nunique()),
                         "n_tests": int(len(sub)),
                         "tier": t, "tier_generous": tg,
                         "tier_label": TIER_LABEL[t],
                         "cas_resolution": notes[c], "n_cas_matched": len(cs)})
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT_COMPOUND, index=False)

    # ---- 4. aggregate to the ladder --------------------------------------
    agg = []
    for g in GROUPS:
        sub = comp[comp.biota_group == g]
        for t in TIERS:
            s = sub[sub.tier == t]
            sg = sub[sub.tier_generous == t]
            agg.append({
                "biota_group": g, "tier": t, "tier_label": TIER_LABEL[t],
                "n_compounds": len(s),
                "mass_2018_Mkg": round(float(s.use_2018_Mkg_high.sum()), 4),
                "mass_share_pct": round(100 * float(s.use_2018_Mkg_high.sum()) / total_hi, 3),
                "mass_share_pct_low_basis":
                    round(100 * float(s.use_2018_Mkg_low.sum()) / total_lo, 3),
                "mass_share_pct_generous_1study":
                    round(100 * float(sg.use_2018_Mkg_high.sum()) / total_hi, 3)})
        s = sub[sub.tier.isna()]
        agg.append({
            "biota_group": g, "tier": -1, "tier_label": "CAS unresolved",
            "n_compounds": len(s),
            "mass_2018_Mkg": round(float(s.use_2018_Mkg_high.sum()), 4),
            "mass_share_pct": round(100 * float(s.use_2018_Mkg_high.sum()) / total_hi, 3),
            "mass_share_pct_low_basis":
                round(100 * float(s.use_2018_Mkg_low.sum()) / total_lo, 3),
            "mass_share_pct_generous_1study":
                round(100 * float(s.use_2018_Mkg_high.sum()) / total_hi, 3)})
    ladder = pd.DataFrame(agg)
    ladder.to_csv(OUT_LADDER, index=False)

    print("\n=== share of 2018 applied mass by highest evidence tier "
          f"(>= {K_HEADLINE} independent studies) ===")
    for g in GROUPS:
        sub = ladder[ladder.biota_group == g]
        print(f"\n{g}")
        for _, r in sub.iterrows():
            print(f"   t{int(r.tier):>2}  {r.tier_label:<30}{r.mass_share_pct:>7.2f}%"
                  f"   ({r.mass_2018_Mkg:>7,.1f} M kg, {r.n_compounds:>3} cmpd)"
                  f"   [1-study basis {r.mass_share_pct_generous_1study:>6.2f}%]")
        nf = sub[sub.tier.isin([0, 1, 2, 3])].mass_share_pct.sum()
        nf1 = sub[sub.tier.isin([0, 1, 2, 3])].mass_share_pct_generous_1study.sum()
        print(f"   -> no field evidence at all: {nf:.2f}% of applied mass "
              f"({nf1:.2f}% on the 1-study basis)")

    # ---- 5. verification --------------------------------------------------
    print("\n=== verification ===")
    d = (ladder.mass_share_pct - ladder.mass_share_pct_low_basis).abs().max()
    print(f"(a) recomputed on PNSP low_kg instead of high_kg: max shift in any "
          f"share = {d:.2f} pp")

    nat = pd.read_csv(DERIVED / "pnsp_national_corrected.csv")
    n18 = float(nat.loc[nat.year == 2018, "total_high_Mkg"].iloc[0])
    print(f"(b) 2018 total from the panel {total_hi:,.3f} M kg vs published "
          f"pnsp_national_corrected {n18:,.3f} M kg (diff {abs(total_hi - n18):.4f})")

    fam5 = soil.family.fillna("").str.contains(
        "Lumbricidae|Isotomidae|Onychiuridae|Enchytraeidae|Megascolecidae",
        case=False, na=False)
    strict = soil[fam5 & soil.cas.eq(1071836)]
    fam = soil[fam5 & soil.cas.isin(cas_sets.get("GLYPHOSATE", set()))]
    print(f"(c) glyphosate, the repo's five-family soil-fauna filter: "
          f"{len(strict)} endpoint-bearing tests on the parent CAS alone, "
          f"{len(fam)} across the {len(cas_sets['GLYPHOSATE'])}-member CAS family "
          f"(repo EDA reports 106 records before the endpoint filter)")

    print("(d) every tier-5 (>=1 yr field) credit, and the studies behind it:")
    any5 = comp[comp.tier == 5]
    if len(any5) == 0:
        print("      none -- no compound x group reaches >=1 yr field evidence "
              f"with >= {K_HEADLINE} independent studies")
    for _, r in any5.sort_values("use_2018_Mkg_high", ascending=False).head(15).iterrows():
        print(f"      {r.compound:<18} {r.biota_group:<26} "
              f"{r.n_studies:>3.0f} studies, {r.n_tests:>4.0f} tests")
    g5 = comp[comp.tier_generous == 5]
    print(f"    on the 1-study basis, {len(g5)} compound x group cells reach tier 5")

    print("(e) top-10 compounds by mass, tier per group "
          f"(>= {K_HEADLINE} studies / 1 study):")
    top10 = list(use_hi.head(10).index)
    piv = comp[comp.compound.isin(top10)].pivot(
        index="compound", columns="biota_group", values="tier").reindex(top10)
    pig = comp[comp.compound.isin(top10)].pivot(
        index="compound", columns="biota_group", values="tier_generous").reindex(top10)
    hdr = ["Earthworms & potworms", "Springtails & soil mites",
           "Mycorrhizal fungi", "Soil bacteria & protozoa"]
    print(f"      {'compound':<18}{'Mkg':>7}  " + "  ".join(f"{h[:14]:>14}" for h in hdr))
    for c in top10:
        cells = "  ".join(f"{str(piv.loc[c, h]):>6}/{str(pig.loc[c, h]):<7}" for h in hdr)
        print(f"      {c:<18}{use_hi[c]:>7,.1f}  {cells}")

    print(f"\nwrote {OUT_LADDER.relative_to(ROOT)}")
    print(f"wrote {OUT_COMPOUND.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
