"""Soil-organism toxicity of the compounds actually applied, from EPA ECOTOX.

The soil pillar is the weakest in this project: the federal soil data is either
single-timepoint (RaCA), modelled (SSURGO, CEAP), or back-updated each release
(NRI). ECOTOX is different -- it is MEASURED toxicity to non-target soil
organisms, the effect residue monitoring does not attempt to capture at all.

Two joins here are easy to get wrong and silently return nothing:
  * ECOTOX `chemicals.txt` carries SYSTEMATIC names, not common ones -- glyphosate
    appears as "N-(Phosphonomethyl)glycine". Join on CAS, never on name.
  * `ecotox_group == "Worms"` includes marine polychaetes (Nereis, Glycera).
    Filtering on that alone puts saltwater ragworms in a soil analysis. Use
    `organism_habitat == "Soil"` together with the standard soil-test families.

Caveats kept in the output rather than buried:
  * ECOTOX is a literature compilation. Endpoint counts track RESEARCH effort,
    not use or risk; a well-studied compound looks worse by being well studied.
  * Endpoints span orders of magnitude across duration, media and lifestage;
    the median of log10 is reported with its spread.
  * Toxicity per kg is not risk. Risk needs exposure, persistence and binding.
"""
import glob, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
Z = sorted(glob.glob(str(ROOT / "data/raw/epa/ecotox/**/ecotox_ascii_*.zip"), recursive=True))[0]
PRE = "ecotox_ascii_09_15_2026/"

# CAS numbers as integers, matching ECOTOX's cas_number encoding.
CAS = {
    "GLYPHOSATE": 1071836, "ATRAZINE": 1912249, "CHLORPYRIFOS": 2921882,
    "METOLACHLOR": 51218452, "ACETOCHLOR": 34256821, "PENDIMETHALIN": 40487421,
    "TRIFLURALIN": 1582098, "SIMAZINE": 122349, "ALACHLOR": 15972608,
    "IMIDACLOPRID": 138261413, "CARBARYL": 63252, "DICAMBA": 1918009,
    "PARAQUAT": 4685147, "DIURON": 330541, "2,4-D": 94757, "MALATHION": 121755,
    "CHLOROTHALONIL": 1897456, "METRIBUZIN": 21087649, "CARBOFURAN": 1563662,
    "GLUFOSINATE": 51276474, "ACEPHATE": 30560191, "CYPERMETHRIN": 52315078,
}

def read(member, usecols=None):
    with zipfile.ZipFile(Z) as zf, zf.open(member) as fh:
        return pd.read_csv(fh, sep="|", usecols=usecols, low_memory=False,
                           encoding="latin-1", on_bad_lines="skip")

spec = read(PRE + "validation/species.txt")
SOIL_FAMILIES = "Lumbricidae|Isotomidae|Onychiuridae|Enchytraeidae|Megascolecidae"
soil_species = spec[spec.family.fillna("").str.contains(SOIL_FAMILIES, case=False, na=False)]
print(f"soil-fauna species (earthworms, springtails, potworms): {len(soil_species):,}")
print("  e.g.", ", ".join(soil_species.latin_name.dropna().unique()[:5]))

tests = read(PRE + "tests.txt", usecols=["test_id", "test_cas", "species_number", "organism_habitat"])
soil_tests = tests[(tests.organism_habitat == "Soil")
                   & (tests.species_number.isin(soil_species.species_number))]
print(f"tests: {len(tests):,}   -> soil-habitat tests on soil fauna: {len(soil_tests):,}")

res = read(PRE + "results.txt", usecols=["test_id", "endpoint", "conc1_mean", "conc1_unit"])
d = res.merge(soil_tests, on="test_id", how="inner")

d["endpoint"] = d.endpoint.astype(str).str.strip().str.upper()
d = d[d.endpoint.isin(["LC50", "EC50", "LD50"])]
d["unit"] = d.conc1_unit.astype(str).str.strip().str.lower()
d = d[d.unit.isin(["mg/kg", "mg/kg dw", "ppm", "mg/kg bdwt"])]
d["val"] = pd.to_numeric(d.conc1_mean.astype(str).str.replace(r"[^0-9.eE+-]", "", regex=True),
                         errors="coerce")
d = d[(d.val > 0) & d.val.notna()]
d["cas"] = pd.to_numeric(d.test_cas, errors="coerce")
print(f"usable acute soil endpoints (LC50/EC50/LD50 in mg/kg): {len(d):,}")

p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")
use = p[p.year == 2018].groupby("compound").high_kg.sum() / 1e6

rows = []
for name, cas in CAS.items():
    sub = d[d.cas == cas]
    if len(sub) < 3:
        continue
    lg = np.log10(sub.val)
    rows.append({"compound": name, "n_endpoints": len(sub),
                 "median_LC50_mg_kg": float(10 ** lg.median()),
                 "min_mg_kg": float(sub.val.min()),
                 "log10_spread": float(lg.std()),
                 "use_2018_Mkg": float(use.get(name, np.nan))})

t = pd.DataFrame(rows).sort_values("median_LC50_mg_kg")
t["toxicity_weighted_use"] = t.use_2018_Mkg / t.median_LC50_mg_kg
t.to_csv(OUT / "soil_toxicity_vs_use.csv", index=False)

print("\n=== acute toxicity to soil fauna (LOWER mg/kg = MORE toxic) vs 2018 use ===")
print(f"{'compound':<16} {'median LC50':>12} {'min':>9} {'spread':>7} {'n':>4} {'2018 M kg':>10} {'tox-wtd':>9}")
print("-" * 76)
for _, r in t.iterrows():
    u = f"{r.use_2018_Mkg:,.1f}" if pd.notna(r.use_2018_Mkg) else "n/a"
    tw = f"{r.toxicity_weighted_use:,.2f}" if pd.notna(r.toxicity_weighted_use) else "n/a"
    print(f"{r.compound:<16} {r.median_LC50_mg_kg:>12,.1f} {r.min_mg_kg:>9,.2f} "
          f"{r.log10_spread:>7.2f} {int(r.n_endpoints):>4} {u:>10} {tw:>9}")

print("\n'tox-wtd' = M kg applied / median LC50: a crude hazard-per-area proxy.")
print("It is NOT risk -- no exposure, persistence, or soil-binding term.")
print("n is literature volume, i.e. research effort, not risk.")
