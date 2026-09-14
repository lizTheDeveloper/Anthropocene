"""Total mass is flat and composition has shifted (eda_03/eda_04) -- but "composition
changed" is 500 separate compound stories. This reduces them to a handful of SHAPES.

The question a petition has to answer is not "did use go up" but "what kinds of
trajectories exist, and which compounds are still on the rising one in 2018".
So: cluster each compound's 1992-2018 national series by its SHAPE.

Normalization: each compound is divided by its own peak year, giving a curve in
[0, 1] whose maximum is 1. Two consequences, both wanted:
  * Magnitude is removed. A compound that went 1 -> 100 kg and one that went
    10 -> 1000 kg have identical normalized curves and must cluster together;
    otherwise the clustering just rediscovers the (already known) mass ranking,
    with glyphosate alone in a cluster of one.
  * The scale stays interpretable. A centroid value of 0.40 in 2018 reads
    directly as "this family of compounds ended at 40% of its own peak".
  z-scoring each series was the alternative and gives the same broad structure
  (best silhouette also at a small k), but its centroids are in units of
  each-compound standard deviations, which is not a quantity anyone reading a
  regulatory filing can check against the raw series. Peak-scaling is preferred
  for that reason, not for any statistical one.

Clustering: Ward linkage on Euclidean distance between the 27-dim normalized
curves. Ward over k-means because these are nested shape families rather than
isotropic blobs (a "decline" family splits into steep and shallow declines, not
into two separate clouds), and because it is deterministic -- no random restarts
to report for a filing. k-means silhouettes are printed alongside as a
robustness check; they pick the same k.

k = 4 by silhouette over k=3..8. The scores are modest in absolute terms (~0.24),
which is expected and should be stated plainly: trajectory space is a continuum,
not well-separated islands, so the clusters are a summary of that continuum, not
proof of four discrete regimes.

Panel is the corrected one (California dropped from every year, aggregate
double-count rows removed) -- do not re-apply those corrections here.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"

YEARS = list(range(1992, 2019))
MIN_YEARS = 20        # present in 20 of 27 years: tolerates late registrations and
                      # gap years, excludes one-off appearances that have no shape
MIN_PEAK_KG = 1e5     # 100 tonnes/yr at national peak. Below that, a compound's
                      # county-level EPest estimates are a handful of surveyed
                      # counties and the year-to-year curve is survey noise.

p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")

# 2018 is preliminary and ~26k county rows carry a low estimate with no high
# estimate. Summing with NaN dropped (pandas default, and what eda_03/eda_04 did)
# understates 2018 by the low-estimate mass on those rows: 1.5M kg of 448M kg,
# 0.34%. Too small to move any normalized curve, so it is left as-is rather than
# mixing low- and high-basis numbers in one series.
by = (p.groupby(["year", "compound"]).high_kg.sum()
      .unstack(fill_value=0).reindex(YEARS).fillna(0))

n_years_used = (by > 0).sum()
peak_kg = by.max()
keep = by.columns[(n_years_used >= MIN_YEARS) & (peak_kg >= MIN_PEAK_KG)]
X = by[keep].T                                  # rows = compounds, cols = years

print("=== compound screen ===")
print(f"   compounds in corrected panel            : {by.shape[1]}")
print(f"   present in >= {MIN_YEARS} of {len(YEARS)} years            : {(n_years_used >= MIN_YEARS).sum()}")
print(f"   ... and peak annual use >= {MIN_PEAK_KG/1e3:,.0f} tonnes   : {len(keep)}")
print(f"   share of 2018 national mass retained    : "
      f"{100*X[2018].sum()/by.loc[2018].sum():.1f}%")

N = X.div(X.max(axis=1), axis=0)                # shape only: each curve peaks at 1.0
A = N.values

Z = linkage(A, method="ward")
print("\n=== choosing k: silhouette on the normalized curves ===")
print(f"{'k':<4} {'Ward':>8} {'k-means':>9}   cluster sizes (Ward)")
scores = {}
for k in range(3, 9):
    ward = fcluster(Z, k, criterion="maxclust")
    km = KMeans(n_clusters=k, n_init=25, random_state=0).fit(A)
    scores[k] = silhouette_score(A, ward)
    print(f"{k:<4} {scores[k]:>8.4f} {silhouette_score(A, km.labels_):>9.4f}   "
          f"{np.bincount(ward)[1:]}")

K = max(scores, key=scores.get)
print(f"\n   k = {K} (Ward silhouette {scores[K]:.4f}). Separation is weak in absolute")
print("   terms; these are summaries of a continuum, not discrete regimes.")

raw_lab = pd.Series(fcluster(Z, K, criterion="maxclust"), index=X.index)

# Ward's label numbers are arbitrary, which makes diffs between runs unreadable.
# Renumber by the year the cluster centroid peaks, so cluster 1 is always the
# earliest-peaking (most declined) family and cluster K the latest-peaking.
order = (N.groupby(raw_lab).mean().idxmax(axis=1).sort_values().index)
remap = {old: new for new, old in enumerate(order, start=1)}
lab = raw_lab.map(remap).rename("cluster")

centroids = N.groupby(lab).mean()
sizes = lab.value_counts().sort_index()

print("\n=== clusters ===")
for c in centroids.index:
    mem = lab[lab == c].index
    cen = centroids.loc[c]
    print(f"\n cluster {c}: n = {len(mem)}   2018 mass = {X.loc[mem, 2018].sum()/1e6:,.1f} M kg "
          f"({100*X.loc[mem, 2018].sum()/X[2018].sum():.1f}% of screened mass)")
    print(f"   centroid peaks {cen.idxmax()}, ends {cen.loc[2018]:.2f} of peak; "
          f"member peak years {N.loc[mem].idxmax(axis=1).quantile(.25):.0f}-"
          f"{N.loc[mem].idxmax(axis=1).quantile(.75):.0f} (IQR)")
    print("   mean normalized trajectory:")
    for i in range(0, len(YEARS), 9):
        chunk = YEARS[i:i+9]
        print("      " + "  ".join(f"{y}" for y in chunk))
        print("      " + "  ".join(f"{cen.loc[y]:>4.2f}" for y in chunk))
    top = X.loc[mem, 2018].sort_values(ascending=False).head(15)
    print("   top members by 2018 mass (M kg):")
    for cmpd, v in top.items():
        print(f"      {cmpd:<28} {v/1e6:>8.2f}   "
              f"1992 {X.loc[cmpd, 1992]/1e6:>7.2f}  peak {X.loc[cmpd].max()/1e6:>7.2f} "
              f"({X.loc[cmpd].idxmax()})")

print("\n=== where the compounds of interest landed ===")
for cmpd in ["GLYPHOSATE", "ATRAZINE", "ALACHLOR", "CHLORPYRIFOS", "METHYL BROMIDE"]:
    if cmpd not in lab.index:
        print(f"   {cmpd:<16} screened out")
        continue
    s = X.loc[cmpd]
    print(f"   {cmpd:<16} cluster {lab[cmpd]}   "
          f"1992 {s.loc[1992]/1e6:>7.2f} -> 2018 {s.loc[2018]/1e6:>7.2f} M kg   "
          f"peak {s.max()/1e6:>7.2f} ({s.idxmax()})")

per_compound = pd.DataFrame({
    "compound": X.index,
    "cluster": lab.values,
    "use_1992_Mkg": X[1992].values / 1e6,
    "use_2018_Mkg": X[2018].values / 1e6,
    "peak_Mkg": X.max(axis=1).values / 1e6,
    "peak_year": X.idxmax(axis=1).values,
}).sort_values(["cluster", "use_2018_Mkg"], ascending=[True, False])
per_compound.to_csv(OUT / "compound_trajectory_clusters.csv", index=False)

cent_long = (centroids.stack().rename("mean_normalized_value").reset_index()
             .rename(columns={"level_1": "year"}))
cent_long["n_compounds"] = cent_long.cluster.map(sizes)
cent_long = cent_long[["cluster", "year", "mean_normalized_value", "n_compounds"]]
cent_long.to_csv(OUT / "compound_cluster_centroids.csv", index=False)

print(f"\nwrote {OUT/'compound_trajectory_clusters.csv'} ({len(per_compound)} compounds)")
print(f"wrote {OUT/'compound_cluster_centroids.csv'} ({len(cent_long)} rows)")
