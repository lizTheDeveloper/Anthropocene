"""Independent check of the PNSP aggregate double-counting correction.

The corrected national series in eda_04 drops two compound rows as aggregates:
"METOLACHLOR & METOLACHLOR-S" and "DIMETHENAMID & DIMETHENAMID-P". That
correction moves the headline 2016->2018 number from a fall to flat, so it
should not be taken on trust from a single script; this re-derives it straight
from the raw distributed files, without the intermediate parquet panel.

Note on how NOT to test this: searching for compound names that are a prefix of
other names finds nothing. The aggregates are explicit combined-name rows
containing " & ", not parents of a name hierarchy, so a prefix test returns a
clean bill of health on files that are in fact double-counted.
"""
import glob, io, sys, zipfile
import pandas as pd

def load(pattern):
    f = sorted(glob.glob(pattern, recursive=True))
    if not f:
        return None
    if f[0].endswith(".zip"):
        with zipfile.ZipFile(f[0]) as z:
            name = [m for m in z.namelist() if m.lower().endswith((".txt", ".csv"))][0]
            with z.open(name) as fh:
                return pd.read_csv(io.StringIO(fh.read().decode("latin-1")),
                                   sep=None, engine="python")
    return pd.read_csv(f[0], sep="\t")

YEARS = [
    ("2012", "data/raw/usgs/pnsp/**/EPest.county.estimates.2012.txt"),
    ("2016", "data/raw/usgs/pnsp/**/2016PreliminaryEstimates.zip"),
    ("2018", "data/raw/usgs/pnsp/**/2018PreliminaryEstimatesNoCA.zip"),
]

failures = []
for label, pattern in YEARS:
    d = load(pattern)
    if d is None:
        print(f"{label}: file not present, skipped"); continue
    cc = [c for c in d.columns if "COMPOUND" in c.upper()][0]
    hi = [c for c in d.columns if "HIGH" in c.upper()][0]
    total = d[hi].sum()
    combos = sorted(n for n in set(d[cc].dropna()) if " & " in str(n))
    print(f"\n{label}: total={total:,.0f} kg | combined-name rows: {len(combos)}")
    inflated = 0.0
    for n in combos:
        parts = [x.strip() for x in n.split("&")]
        agg = d.loc[d[cc] == n, hi].sum()
        comp = d.loc[d[cc].isin(parts), hi].sum()
        ratio = agg / comp if comp else float("nan")
        inflated += agg
        print(f"   {n:<32} aggregate={agg:>13,.0f} components={comp:>13,.0f} ratio={ratio:.4f}")
        if comp and abs(ratio - 1.0) > 1e-6:
            failures.append(f"{label}/{n}: ratio {ratio:.6f} != 1.0")
    if combos:
        print(f"   --> double-counted = {inflated:,.0f} kg = {100*inflated/total:.1f}% of the naive total")

print("\nRESULT:", "aggregate==component-sum confirmed" if not failures else f"UNEXPECTED: {failures}")
sys.exit(1 if failures else 0)
