"""Which foods carry the same pesticide fingerprint?

Pesticide use data (PNSP, CDPR) says what growers bought. It does not say what
ends up on the plate. USDA AMS's Pesticide Data Program does: ~10k samples a
year, each screened against a few hundred analytes. This script asks whether
foods fall into natural groups by *which* residues they carry -- a produce-aisle
taxonomy built from residue chemistry rather than from botany or marketing.

Three properties of PDP force the design of everything below.

1. THE FILES HAVE NO HEADER ROW.
   `PDP<yy>Results.txt` and `PDP<yy>Samples.txt` are pipe-delimited with the
   first data record on line 1. Reading them with pandas' default header=0 eats
   one real sample and mislabels every column, silently. The column order is
   documented only in `PDP DataDictionary <year>.pdf` inside the same zip. The
   layouts below were read off the 2019 and 2024 dictionaries and then checked
   against the data: the 2024 dictionary claims 9,872 sample records and
   2,872,073 result records, and that is exactly what header=None yields.

2. RESIDUE RESULTS ARE LEFT-CENSORED.
   CONCEN is empty in the text file for a non-detect -- not zero, not a number.
   Treating blanks as 0 ppm would invent measurements below the limit of
   detection that nobody made, and would make the answer depend on each
   lab's LOD rather than on the food. So the cell value here is DETECTION
   FREQUENCY: of the samples of this commodity actually screened for this
   compound, what fraction came back positive. That is a quantity the data
   genuinely supports. Detect/non-detect comes from the MEAN column (O/R/A =
   detect, ND/NP = non-detect), which the code verifies agrees exactly with
   "CONCEN is blank" before relying on it.

3. THE COMMODITY LIST ROTATES EVERY YEAR.
   PDP samples a different basket each year in coordination with EPA. Over
   2019-2024 only 73 commodity codes appear at all and most appear in one or
   two years. Worse, the analyte panel is chosen per commodity: 2024 screened
   avocado against 547 compounds and almonds against 197. So a pooled
   commodity x pesticide matrix is riddled with cells that are not "zero
   detections" but "never looked". Two defences are used:
     (a) the denominator of every detection frequency is the number of samples
         of THAT commodity actually tested for THAT compound, taken from the
         result rows themselves -- never the commodity's total sample count;
     (b) the matrix is trimmed to a rectangle in which every retained
         commodity was screened for every retained compound (a "common panel"),
         so that a 0 always means "looked and found nothing".
   Within a commodity, years are pooled: a commodity's profile is its
   2019-2024 aggregate, and the years that went into it are carried through to
   the output so a reader can see that e.g. Grapes is 2022-2023 only.

Organic samples (CLAIM=PO, ~7% of records) are dropped: they are a different
production system and mixing them in would blur the conventional fingerprint
that the clustering is trying to find.
"""
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path("/home/user/Anthropocene")
RAW = ROOT / "data/raw/usda-ams/pdp/2026-09-14/annual"
OUT = ROOT / "data/derived"
YEARS = range(2019, 2025)          # recent enough to reflect today's chemistry,
                                   # wide enough that 73 commodities appear

# Column layouts from "PDP DataDictionary <year>.pdf"; identical 2019 and 2024.
SAMPLE_COLS = ["SAMPLE_PK", "STATE", "YEAR", "MONTH", "DAY", "SITE", "COMMOD",
               "SOURCE_ID", "VARIETY", "ORIGIN", "COUNTRY", "DISTTYPE", "COMMTYPE",
               "CLAIM", "QUANTITY", "GROWST", "PACKST", "DISTST"]
RESULT_COLS = ["SAMPLE_PK", "COMMOD", "COMMTYPE", "LAB", "PESTCODE", "TESTCLASS",
               "CONCEN", "LOD", "CONUNIT", "CONFMETHOD", "CONFMETHOD2", "ANNOTATE",
               "QUANTITATE", "MEAN", "EXTRACT", "DETERMIN"]
DETECT_CODES = {"O", "R", "A"}     # "Mean" reference sheet; ND/NP are non-detects

MIN_SAMPLES = 100                  # below this a detection frequency is mostly noise
MIN_COMMODITIES_PER_PEST = 3       # a compound seen in 1-2 foods is a label, not an axis
PANEL_COVERAGE = 0.50              # "screened" = tested in >=50% of that food's samples
PANEL_ROW_BIAS = 3.0               # see _common_panel(): we would rather lose a
                                   # compound than lose a food

# ---------------------------------------------------------------- loading

def _zip_for(year):
    # 2006/2015/2016/2017 ship as .ZIP; the recent years are .zip. Check both.
    for ext in (".zip", ".ZIP"):
        p = RAW / f"{year}PDPDatabase{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"no PDP archive for {year}")


def _member(year, kind):
    listing = subprocess.run(["unzip", "-Z1", str(_zip_for(year))],
                             capture_output=True, text=True, check=True).stdout.split()
    want = f"{str(year)[2:]}{kind}.txt".lower()
    return next(m for m in listing if m.lower().endswith(want))


def _read(year, kind, cols, usecols):
    """Stream one member out of the zip. header=None is the whole point."""
    proc = subprocess.Popen(["unzip", "-p", str(_zip_for(year)), _member(year, kind)],
                            stdout=subprocess.PIPE)
    df = pd.read_csv(proc.stdout, sep="|", header=None, names=cols, usecols=usecols,
                     dtype=str, na_filter=False)   # keep blanks as "" so a blank
    proc.wait()                                    # CONCEN stays distinguishable
    return df


def load(years):
    samples, results = [], []
    for y in years:
        s = _read(y, "Samples", SAMPLE_COLS, ["SAMPLE_PK", "COMMOD", "CLAIM"])
        r = _read(y, "Results", RESULT_COLS, ["SAMPLE_PK", "COMMOD", "PESTCODE", "CONCEN", "MEAN"])
        s["YR"] = y
        r["YR"] = y
        samples.append(s)
        results.append(r)
        print(f"   {y}: {len(s):>7,} samples  {len(r):>10,} results")
    return pd.concat(samples, ignore_index=True), pd.concat(results, ignore_index=True)


def reference_names():
    """Commodity and pesticide code -> name, most recent year wins.

    Codes get renamed across years (BB is "Blueberries, Cultivated" in 2020 and
    "Blueberries, Fresh" in 2023), so read every year and let later overwrite.
    """
    commod, pest = {}, {}
    tmp = Path(tempfile.mkdtemp(prefix="pdp_refs_"))
    for y in YEARS:
        subprocess.run(["unzip", "-o", "-j", str(_zip_for(y)),
                        f"PDP ReferenceTables {y}.xls*", "-d", str(tmp)],
                       capture_output=True, check=False)
        hit = list(tmp.glob(f"PDP ReferenceTables {y}.xls*"))
        if not hit:
            continue
        book = pd.ExcelFile(hit[0])
        for sheet, target in (("Commodity", commod), ("Pest Code", pest)):
            t = book.parse(sheet, header=None, skiprows=4).iloc[:, :2].dropna()
            t = t[~t[0].astype(str).str.contains("Code")]   # some years repeat the header
            target.update({str(a).strip(): str(b).strip() for a, b in zip(t[0], t[1])})
    return commod, pest


# ---------------------------------------------------------------- matrix

def _common_panel(present):
    """Trim a boolean commodity x compound "was screened" grid to a full rectangle.

    Greedily drop whichever row or column has the largest share of unscreened
    cells, but only drop a commodity when it is more than PANEL_ROW_BIAS times
    worse than the worst compound. Without that bias the search happily trades
    twenty foods for forty extra compounds; foods are the unit of analysis here
    and compounds are merely the coordinates, so foods are protected.
    """
    grid = present.loc[:, present.sum(axis=0) >= 40]   # bound the search
    while not grid.values.all():
        row_gap = (~grid).sum(axis=1) / grid.shape[1]
        col_gap = (~grid).sum(axis=0) / grid.shape[0]
        if row_gap.max() > PANEL_ROW_BIAS * col_gap.max():
            grid = grid.drop(index=row_gap.idxmax())
        else:
            grid = grid.drop(columns=col_gap.idxmax())
    return grid


def build_matrix(samples, results):
    samples = samples[samples.CLAIM != "PO"]                     # conventional only
    keep = set(zip(samples.YR, samples.SAMPLE_PK))
    results = results[[(y, k) in keep for y, k in zip(results.YR, results.SAMPLE_PK)]].copy()

    # Trust MEAN only after confirming it partitions exactly on "CONCEN is blank".
    results["DET"] = results.MEAN.isin(DETECT_CODES)
    assert (results.DET == results.CONCEN.ne("")).all(), \
        "MEAN detect codes disagree with CONCEN blankness -- re-read the data dictionary"

    n_samp = samples.groupby("COMMOD").size()
    pair = (results.groupby(["COMMOD", "PESTCODE"])
                   .agg(tested=("DET", "size"), detected=("DET", "sum")).reset_index())
    pair["n_samples"] = pair.COMMOD.map(n_samp)
    pair["screened_frac"] = pair.tested / pair.n_samples

    present = pd.crosstab(pair.loc[pair.screened_frac >= PANEL_COVERAGE, "COMMOD"],
                          pair.loc[pair.screened_frac >= PANEL_COVERAGE, "PESTCODE"]).astype(bool)
    panel = _common_panel(present)
    print(f"   common panel: {panel.shape[0]} commodities x {panel.shape[1]} compounds"
          f" (dropped commodities: {sorted(set(present.index) - set(panel.index))})")

    sub = pair[pair.COMMOD.isin(panel.index) & pair.PESTCODE.isin(panel.columns)].copy()
    sub["freq"] = sub.detected / sub.tested                      # the censoring-safe cell
    X = sub.pivot(index="COMMOD", columns="PESTCODE", values="freq")
    assert not X.isna().any().any(), "common panel left holes"

    X = X.loc[n_samp.reindex(X.index).ge(MIN_SAMPLES).values]
    X = X.loc[:, (X > 0).sum(axis=0) >= MIN_COMMODITIES_PER_PEST]
    return X, results, n_samp


# ---------------------------------------------------------------- clustering

def choose_k(X, kmax=10):
    """Report every candidate, then take the silhouette peak.

    Metric choice: all columns are the same thing measured the same way -- a
    probability in [0,1] -- so the usual reason to reach for cosine (columns on
    incommensurable scales, or document-length effects) does not apply, and
    plain Euclidean distance is meaningful. Cosine and correlation additionally
    throw away overall residue load, which is a real and interpretable axis of
    this data; empirically they also score worse and collapse more than half the
    commodities into one undifferentiated blob. Ward is preferred to k-means
    because it is deterministic and yields compact clusters at this n (~60).
    All four are scored below so the choice is auditable rather than asserted.
    """
    V = X.values
    euclid = squareform(pdist(V, "euclidean"))
    scores = {}

    def score(name, labels_by_k, D):
        scores[name] = {k: round(silhouette_score(D, lab, metric="precomputed"), 3)
                        for k, lab in labels_by_k.items() if len(set(lab)) > 1}

    Zw = linkage(pdist(V, "euclidean"), "ward")
    score("ward/euclidean", {k: fcluster(Zw, k, "maxclust") for k in range(2, kmax + 1)}, euclid)
    for metric in ("cosine", "correlation"):
        D = squareform(pdist(V, metric))
        Z = linkage(pdist(V, metric), "average")
        score(f"average/{metric}",
              {k: fcluster(Z, k, "maxclust") for k in range(2, kmax + 1)}, D)
    score("kmeans/euclidean",
          {k: KMeans(k, n_init=50, random_state=0).fit_predict(V) for k in range(2, kmax + 1)},
          euclid)

    print("\n=== silhouette by method and k ===")
    print(f"{'method':<20}" + "".join(f"{k:>7}" for k in range(2, kmax + 1)))
    for name, s in scores.items():
        print(f"{name:<20}" + "".join(f"{s.get(k, float('nan')):>7.3f}" for k in range(2, kmax + 1)))

    best_k = max(scores["ward/euclidean"], key=scores["ward/euclidean"].get)
    print(f"\n   chosen: ward/euclidean, k={best_k} "
          f"(silhouette {scores['ward/euclidean'][best_k]:.3f})")
    return fcluster(Zw, best_k, "maxclust"), best_k, scores


# ---------------------------------------------------------------- main

print("=== reading PDP 2019-2024 (header=None; see module docstring) ===")
samples, results = load(YEARS)
commod_name, pest_name = reference_names()

print("\n=== building commodity x pesticide detection-frequency matrix ===")
X, results, n_samp = build_matrix(samples, results)

# A commodity with no detections anywhere on the common panel has no fingerprint
# to cluster on (and no direction under cosine). Report it, do not cluster it.
blank = X.index[X.sum(axis=1) == 0].tolist()
if blank:
    print(f"   no detections on the common panel, held out: "
          f"{[commod_name.get(c, c) for c in blank]}")
X = X.loc[X.sum(axis=1) > 0]
print(f"   clustering matrix: {X.shape[0]} commodities x {X.shape[1]} compounds")

labels, k, _ = choose_k(X)

# Per-sample residue load, restricted to the same common panel so that the
# number is comparable across commodities screened on different full panels.
panel_res = results[results.COMMOD.isin(X.index) & results.PESTCODE.isin(X.columns)]
per_sample = panel_res.groupby(["YR", "SAMPLE_PK", "COMMOD"]).DET.sum().reset_index()
load = per_sample.groupby("COMMOD").DET.agg(
    mean_residues_per_sample="mean", pct_samples_with_any_detection=lambda v: 100 * (v > 0).mean())
years = samples[samples.CLAIM != "PO"].groupby("COMMOD").YR.agg(
    lambda v: "|".join(str(y) for y in sorted(set(v))))

clusters = pd.DataFrame({
    "commodity": [commod_name.get(c, c) for c in X.index],
    "commod_code": X.index,
    "cluster": labels,
    "n_samples": n_samp.reindex(X.index).values,
    "years_sampled": years.reindex(X.index).values,
    "mean_residues_per_sample": load.mean_residues_per_sample.reindex(X.index).round(3).values,
    "pct_samples_with_any_detection": load.pct_samples_with_any_detection.reindex(X.index).round(1).values,
}).sort_values(["cluster", "mean_residues_per_sample"], ascending=[True, False])

rows = []
for c in sorted(set(labels)):
    members = clusters[clusters.cluster == c]
    top = X.loc[members.commod_code].mean(axis=0).sort_values(ascending=False).head(5)
    rows.append({
        "cluster": c,
        "n_commodities": len(members),
        "commodities": "|".join(members.commodity),
        "top_pesticides": "|".join(pest_name.get(p, p) for p in top.index),
        "top_pesticide_detection_freq": "|".join(f"{v:.3f}" for v in top.values),
        "mean_residues_per_sample": round(members.mean_residues_per_sample.mean(), 3),
        "pct_samples_with_any_detection": round(members.pct_samples_with_any_detection.mean(), 1),
    })
profiles = pd.DataFrame(rows)

print(f"\n=== {k} clusters ===")
for _, r in profiles.iterrows():
    print(f"\ncluster {r.cluster}  n={r.n_commodities}  "
          f"{r.mean_residues_per_sample:.2f} residues/sample  "
          f"{r.pct_samples_with_any_detection:.0f}% of samples with a detection")
    print(f"   {r.commodities.replace('|', ', ')}")
    for p, v in zip(r.top_pesticides.split("|"), r.top_pesticide_detection_freq.split("|")):
        print(f"      {p:<28} {float(v):>6.1%}")

extremes = clusters.sort_values("mean_residues_per_sample")
print("\n=== residue load extremes (common panel) ===")
for label, row in (("least", extremes.iloc[0]), ("most", extremes.iloc[-1])):
    print(f"   {label:<6} {row.commodity:<24} {row.mean_residues_per_sample:>5.2f} residues/sample, "
          f"{row.pct_samples_with_any_detection:>5.1f}% with any detection (n={row.n_samples})")

OUT.mkdir(parents=True, exist_ok=True)
clusters.to_csv(OUT / "commodity_residue_clusters.csv", index=False)
profiles.to_csv(OUT / "commodity_cluster_profiles.csv", index=False)
Xn = X.rename(columns=lambda p: pest_name.get(p, p), index=lambda c: commod_name.get(c, c))
Xn.round(4).to_csv(OUT / "commodity_pesticide_matrix.csv")
for f in ("commodity_residue_clusters.csv", "commodity_cluster_profiles.csv",
          "commodity_pesticide_matrix.csv"):
    print(f"wrote {OUT / f}")
