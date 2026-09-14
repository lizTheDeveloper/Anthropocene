"""Build the compound crosswalk that makes cross-pillar joins possible.

Nothing in this project shares a compound identifier. PNSP uses uppercase common
names, CA PUR uses a numeric chem_code with its own chemical table, 40 CFR 180
identifies chemicals by section heading, and the residue programmes use their own
code tables. Any "use up, residues up, tolerances high" claim needs these
reconciled first, and reconciling them by eye is how silent mismatches get in.

The approach is deliberately conservative: normalise aggressively, match exactly
on the normalised form, and leave everything else unmatched and visible.
A fuzzy match that quietly pairs "METOLACHLOR" with "METOLACHLOR-S" -- different
compounds, different tolerances -- is worse than no match at all.

Output: data/derived/compound_crosswalk.csv
"""
import csv, glob, io, re, zipfile
from pathlib import Path
import pandas as pd

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"; OUT.mkdir(parents=True, exist_ok=True)

def norm(s: str) -> str:
    """Normalise a chemical name for exact matching.

    Strips salt/ester/isomer qualifiers that appear inconsistently across
    sources, plus punctuation and spacing. Kept narrow on purpose -- each
    removal below is a form actually observed in these files.
    """
    s = str(s).upper().strip()
    s = re.sub(r"\(.*?\)", " ", s)                       # parentheticals
    s = re.sub(r",\s*(TOTAL|ALL ISOMERS|AND ISOMERS)\b", " ", s)
    s = re.sub(r"\b(SODIUM|POTASSIUM|AMMONIUM|CALCIUM|LITHIUM|ZINC|COPPER)\s+SALT\b", " ", s)
    s = re.sub(r"\b(ACID|SALT|ESTER|ESTERS|SALTS)\b", " ", s)
    s = re.sub(r"[^A-Z0-9]+", "", s)                     # punctuation and spaces
    return s

rows = {}
def add(key, source, value):
    r = rows.setdefault(key, {"normalized": key})
    r.setdefault(source, set()).add(str(value))

# --- PNSP compound names ---------------------------------------------------
p = sorted(glob.glob(str(ROOT / "data/raw/usgs/pnsp/**/EPest.county.estimates.2012.txt"), recursive=True))
pnsp_names = set()
if p:
    d = pd.read_csv(p[0], sep="\t", usecols=["COMPOUND"])
    pnsp_names = set(d["COMPOUND"].dropna().unique())
    for n in pnsp_names:
        add(norm(n), "pnsp_compound", n)

# --- CA PUR chemical table -------------------------------------------------
pur_n = 0
z = sorted(glob.glob(str(ROOT / "data/raw/ca-dpr/pur/**/pur2018.zip"), recursive=True))
if z:
    with zipfile.ZipFile(z[0]) as zf:
        name = next((n for n in zf.namelist() if n.lower().endswith("chemical.txt")), None)
        if name:
            with zf.open(name) as fh:
                d = pd.read_csv(io.StringIO(fh.read().decode("latin-1")), on_bad_lines="skip")
            col = next((c for c in d.columns if "chemname" in c.lower()), d.columns[-1])
            code = next((c for c in d.columns if "chem_code" in c.lower()), d.columns[0])
            for _, r in d.iterrows():
                add(norm(r[col]), "pur_chemname", r[col])
                add(norm(r[col]), "pur_chem_code", r[code])
                pur_n += 1

# --- 40 CFR 180 section headings -------------------------------------------
tol_n = 0
tol = OUT / "40cfr180_tolerances.csv"
if tol.exists():
    d = pd.read_csv(tol)
    for sec, head in d[["section", "section_heading"]].drop_duplicates().itertuples(index=False):
        # "§ 180.364 Glyphosate; tolerances for residues." -> "Glyphosate"
        m = re.sub(r"^§?\s*[\d.]+\s*", "", str(head))
        chem = m.split(";")[0].strip()
        if not chem or len(chem) > 80:
            continue
        add(norm(chem), "cfr180_chemical", chem)
        add(norm(chem), "cfr180_section", sec)
        tol_n += 1

# --- assemble --------------------------------------------------------------
fields = ["normalized", "pnsp_compound", "pur_chemname", "pur_chem_code",
          "cfr180_chemical", "cfr180_section", "n_sources"]
out_rows = []
for k, r in sorted(rows.items()):
    if not k:
        continue
    rec = {"normalized": k}
    present = 0
    for f in ["pnsp_compound", "pur_chemname", "pur_chem_code", "cfr180_chemical", "cfr180_section"]:
        vals = sorted(r.get(f, []))
        rec[f] = "|".join(vals[:4])
        if vals and f in ("pnsp_compound", "pur_chemname", "cfr180_chemical"):
            present += 1
    rec["n_sources"] = present
    out_rows.append(rec)

path = OUT / "compound_crosswalk.csv"
with open(path, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out_rows)

# --- report ----------------------------------------------------------------
df = pd.DataFrame(out_rows)
print(f"inputs: {len(pnsp_names)} PNSP compounds, {pur_n} PUR chemical records, {tol_n} CFR 180 sections")
print(f"crosswalk rows: {len(df):,}   written to {path.relative_to(ROOT)}")
print(f"\nmatched in all three sources : {(df.n_sources==3).sum():,}")
print(f"matched in exactly two       : {(df.n_sources==2).sum():,}")
print(f"single-source only           : {(df.n_sources==1).sum():,}")

pnsp_rows = df[df.pnsp_compound != ""]
print(f"\nPNSP compounds: {len(pnsp_rows)}")
print(f"  also in CA PUR      : {(pnsp_rows.pur_chemname!='').sum()}")
print(f"  also in 40 CFR 180  : {(pnsp_rows.cfr180_chemical!='').sum()}")
unmatched = pnsp_rows[(pnsp_rows.pur_chemname == "") & (pnsp_rows.cfr180_chemical == "")]
print(f"  matched to neither  : {len(unmatched)}")
print("\n  sample of PNSP compounds matching neither (need manual review):")
for n in sorted(unmatched.pnsp_compound)[:15]:
    print(f"     {n}")
print("\n  sample fully-matched rows:")
print(df[df.n_sources == 3][["pnsp_compound", "pur_chem_code", "cfr180_section"]].head(10).to_string(index=False))
