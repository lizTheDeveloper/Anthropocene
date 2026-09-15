"""How much soil-organism toxicity evidence exists per kilogram actually applied?

The acute-endpoint table returned only five compounds with three or more
comparable soil-fauna LC50/EC50 values, and glyphosate -- a quarter of all US
agricultural pesticide mass -- was not among them. Before treating that as a
finding rather than a filtering artifact, count the evidence at every level of
strictness: all soil-fauna records, all endpoint types, all units.
"""
import glob, zipfile
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"
Z = sorted(glob.glob(str(ROOT / "data/raw/epa/ecotox/**/ecotox_ascii_*.zip"), recursive=True))[0]
PRE = "ecotox_ascii_09_15_2026/"
CAS = {"GLYPHOSATE": 1071836, "ATRAZINE": 1912249, "CHLORPYRIFOS": 2921882,
       "METOLACHLOR": 51218452, "ACETOCHLOR": 34256821, "PENDIMETHALIN": 40487421,
       "TRIFLURALIN": 1582098, "SIMAZINE": 122349, "ALACHLOR": 15972608,
       "IMIDACLOPRID": 138261413, "CARBARYL": 63252, "DICAMBA": 1918009,
       "PARAQUAT": 4685147, "DIURON": 330541, "2,4-D": 94757,
       "CHLOROTHALONIL": 1897456, "METRIBUZIN": 21087649, "GLUFOSINATE": 51276474,
       "ACEPHATE": 30560191, "METAM": 137428, "CHLOROPICRIN": 76062}

def read(m, usecols=None):
    with zipfile.ZipFile(Z) as zf, zf.open(m) as fh:
        return pd.read_csv(fh, sep="|", usecols=usecols, low_memory=False,
                           encoding="latin-1", on_bad_lines="skip")

spec = read(PRE + "validation/species.txt")
soil_species = spec[spec.family.fillna("").str.contains(
    "Lumbricidae|Isotomidae|Onychiuridae|Enchytraeidae|Megascolecidae", case=False, na=False)]
tests = read(PRE + "tests.txt", usecols=["test_id", "test_cas", "species_number", "organism_habitat"])
soil_tests = tests[(tests.organism_habitat == "Soil")
                   & (tests.species_number.isin(soil_species.species_number))].copy()
soil_tests["cas"] = pd.to_numeric(soil_tests.test_cas, errors="coerce")
res = read(PRE + "results.txt", usecols=["test_id", "endpoint", "conc1_mean", "conc1_unit"])
d = res.merge(soil_tests, on="test_id", how="inner")
d["endpoint"] = d.endpoint.astype(str).str.strip().str.upper()
d["unit"] = d.conc1_unit.astype(str).str.strip().str.lower()

p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")
use = p[p.year == 2018].groupby("compound").high_kg.sum() / 1e6

rows = []
for name, cas in CAS.items():
    sub = d[d.cas == cas]
    acute = sub[sub.endpoint.isin(["LC50", "EC50", "LD50"])]
    comparable = acute[acute.unit.isin(["mg/kg", "mg/kg dw", "ppm", "mg/kg bdwt"])]
    u = float(use.get(name, float("nan")))
    rows.append({"compound": name, "use_2018_Mkg": u,
                 "soil_records_any": len(sub),
                 "acute_any_unit": len(acute),
                 "comparable_mg_kg": len(comparable),
                 "records_per_Mkg": len(sub) / u if u and u == u and u > 0 else float("nan")})

t = pd.DataFrame(rows).sort_values("use_2018_Mkg", ascending=False)
t.to_csv(OUT / "soil_evidence_gap.csv", index=False)

print("=== soil-fauna toxicity evidence in ECOTOX vs how much is applied ===\n")
print(f"{'compound':<16} {'2018 M kg':>10} {'soil recs':>10} {'acute':>7} {'comparable':>11} {'recs/Mkg':>9}")
print("-" * 70)
for _, r in t.iterrows():
    u = f"{r.use_2018_Mkg:,.1f}" if pd.notna(r.use_2018_Mkg) else "n/a"
    rp = f"{r.records_per_Mkg:,.1f}" if pd.notna(r.records_per_Mkg) else "n/a"
    print(f"{r.compound:<16} {u:>10} {r.soil_records_any:>10,} {r.acute_any_unit:>7,} "
          f"{r.comparable_mg_kg:>11,} {rp:>9}")

top5 = t.nlargest(5, "use_2018_Mkg")
print(f"\ntop 5 compounds by use = {top5.use_2018_Mkg.sum():,.0f} M kg/yr "
      f"({100*top5.use_2018_Mkg.sum()/t.use_2018_Mkg.sum():.0f}% of the mass in this table)")
print(f"   soil-fauna records for those 5 combined : {top5.soil_records_any.sum():,}")
print(f"   comparable acute endpoints for those 5  : {top5.comparable_mg_kg.sum():,}")
g = t[t.compound == "GLYPHOSATE"].iloc[0]
print(f"\nglyphosate: {g.use_2018_Mkg:,.1f} M kg/yr applied, {int(g.soil_records_any)} soil-fauna "
      f"records total, {int(g.comparable_mg_kg)} comparable acute endpoints.")
