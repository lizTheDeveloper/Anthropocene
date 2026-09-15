"""Prove each mirrored dataset actually loads and contains what it claims.

A file that downloads cleanly and checksums correctly can still be the wrong
thing. This opens one representative artifact per dataset, parses it, and
prints shape, columns, and a sample so the schema is confirmed before any
analysis is built on top of it.
"""
import glob, gzip, io, zipfile
from pathlib import Path
import pandas as pd

pd.set_option("display.width", 200, "display.max_columns", 30)
ROOT = Path("/home/user/Anthropocene")

def head(title): print(f"\n{'='*78}\n{title}\n{'='*78}")
def one(pat):
    m = sorted(glob.glob(str(ROOT / pat), recursive=True))
    return m[0] if m else None

# --- USGS PNSP -------------------------------------------------------------
head("USGS PNSP — county-level pesticide use, 2012 (final)")
p = one("data/raw/usgs/pnsp/**/EPest.county.estimates.2012.txt")
df = pd.read_csv(p, sep="\t")
print(f"file: {Path(p).name}   rows={len(df):,}  cols={list(df.columns)}")
print(df.head(3).to_string(index=False))
print(f"compounds={df['COMPOUND'].nunique()}  states={df['STATE_FIPS_CODE'].nunique()}  "
      f"counties={df.groupby(['STATE_FIPS_CODE','COUNTY_FIPS_CODE']).ngroups:,}")
print(f"EPest_low total kg = {df['EPEST_LOW_KG'].sum():,.0f} | high = {df['EPEST_HIGH_KG'].sum():,.0f}")
print("top 5 compounds by high estimate:")
print(df.groupby("COMPOUND")["EPEST_HIGH_KG"].sum().nlargest(5).to_string())

# --- USDA PDP --------------------------------------------------------------
head("USDA AMS PDP — 2023 annual database")
z = one("data/raw/usda-ams/pdp/**/2023PDPDatabase.zip")
with zipfile.ZipFile(z) as zf:
    names = zf.namelist()
    print(f"archive: {Path(z).name}  members={len(names)}")
    for n in names[:12]: print("   ", n)
    tx = [n for n in names if n.lower().endswith((".txt", ".csv"))]
    if tx:
        with zf.open(tx[0]) as fh:
            raw = fh.read(400_000).decode("latin-1")
        d = pd.read_csv(io.StringIO(raw), sep=None, engine="python", on_bad_lines="skip")
        print(f"\nfirst table {tx[0]}: cols={len(d.columns)}")
        print("   ", list(d.columns)[:22])
        print(d.head(3).to_string(index=False)[:900])

# --- NASS chemical use -----------------------------------------------------
head("USDA NASS — Quick Stats 'environmental' (Agricultural Chemical Use)")
g = one("data/raw/usda-nass/quickstats-bulk/**/qs.environmental_*.txt.gz")
rows = []
with gzip.open(g, "rt", encoding="latin-1") as fh:
    hdr = fh.readline().rstrip("\n").split("\t")
    for i, line in enumerate(fh):
        if i >= 200_000: break
        rows.append(line.rstrip("\n").split("\t"))
d = pd.DataFrame(rows, columns=hdr)
print(f"file: {Path(g).name}  (first {len(d):,} rows of a larger file)")
print("columns:", list(d.columns))
print("\nsample chemical-use records:")
cols = [c for c in ["YEAR","STATE_NAME","COMMODITY_DESC","STATISTICCAT_DESC","DOMAIN_DESC","DOMAINCAT_DESC","VALUE"] if c in d.columns]
print(d[cols].head(5).to_string(index=False)[:1400])
print("\nyears present in sample:", sorted(d["YEAR"].unique())[:14])
print("statistic categories:", d["STATISTICCAT_DESC"].value_counts().head(6).to_dict())

# --- California PUR --------------------------------------------------------
head("California DPR PUR — 2018 application records")
z = one("data/raw/ca-dpr/pur/**/pur2018.zip")
with zipfile.ZipFile(z) as zf:
    names = zf.namelist()
    print(f"archive: {Path(z).name}  members={len(names)}")
    udc = [n for n in names if "udc" in n.lower()][:3]
    for n in names[:8]: print("   ", n)
    if udc:
        with zf.open(udc[0]) as fh:
            raw = fh.read(600_000).decode("latin-1")
        d = pd.read_csv(io.StringIO(raw), on_bad_lines="skip", low_memory=False)
        print(f"\n{udc[0]}: cols={len(d.columns)}")
        print("   ", list(d.columns)[:24])
        keep = [c for c in ["applic_dt","county_cd","chem_code","lbs_chm_used","acre_treated","site_code"] if c in d.columns]
        print(d[keep].head(4).to_string(index=False))

# --- FDA residue -----------------------------------------------------------
head("FDA — pesticide residue monitoring, FY2022 SampleData")
z = one("data/raw/fda/pesticide-residue-monitoring/**/FY2022/SampleData2022.zip")
with zipfile.ZipFile(z) as zf:
    names = zf.namelist(); print(f"archive: {Path(z).name}  members={names}")
    with zf.open(names[0]) as fh:
        raw = fh.read(400_000).decode("latin-1")
    lines = raw.splitlines()
    print(f"first line: {lines[0][:200]}")
    print(f"sample row : {lines[1][:200]}")
    print(f"delimiter looks like: {'TAB' if chr(9) in lines[0] else ('PIPE' if '|' in lines[0] else 'COMMA/FIXED')}")

# --- FoodData Central ------------------------------------------------------
head("USDA FoodData Central — SR Legacy (frozen 2018-04)")
z = one("data/raw/usda-ars-fdc/fooddata-central/**/FoodData_Central_sr_legacy_food_csv_2018-04.zip")
with zipfile.ZipFile(z) as zf:
    names = zf.namelist(); print(f"archive: {Path(z).name}")
    for n in names: print("   ", n)
    fn = [n for n in names if n.endswith("food_nutrient.csv")]
    if fn:
        with zf.open(fn[0]) as fh:
            d = pd.read_csv(fh, nrows=5)
        print(f"\nfood_nutrient.csv columns: {list(d.columns)}")
        print(d.head(3).to_string(index=False))

# --- ECOTOX ----------------------------------------------------------------
head("EPA ECOTOX — full ASCII release")
z = one("data/raw/epa/ecotox/**/ecotox_ascii_*.zip")
with zipfile.ZipFile(z) as zf:
    names = zf.namelist()
    print(f"archive: {Path(z).name}  members={len(names)}")
    for n in names[:14]: print("   ", n)
    t = [n for n in names if n.endswith("tests.txt")]
    if t:
        with zf.open(t[0]) as fh:
            raw = fh.read(120_000).decode("latin-1")
        print(f"\n{t[0]} header: {raw.splitlines()[0][:220]}")

# --- 40 CFR 180 ------------------------------------------------------------
head("eCFR — 40 CFR Part 180 tolerance table")
x = one("data/raw/ecfr/40cfr180-tolerances/**/40CFR180_full_*.xml")
txt = Path(x).read_text(errors="replace")
import re
secs = re.findall(r'<SECTNO>&#xA7;\s*([\d.\-]+)</SECTNO>', txt) or re.findall(r'<SECTNO>[^<]*?([\d]+\.[\d]+)</SECTNO>', txt)
print(f"file: {Path(x).name}  {len(txt):,} chars   sections found: {len(secs)}")
print("  first 12 section numbers:", secs[:12])
print("  commodity/tolerance table rows (approx):", txt.count("<ROW>"))
