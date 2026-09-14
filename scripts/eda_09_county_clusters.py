"""National totals hide who is spraying what. Counties have fingerprints.

eda_03 showed the story is compositional at the national level: total mass is
flat, the mix moved. The same logic applies in space. A county's pesticide
*mix* encodes its cropping system -- corn/soy counties look nothing like
Delta rice counties or Pacific Northwest orchard counties -- and regulatory
exposure arguments live at that level, not at the national aggregate.

WHY COMPOSITIONAL, NOT RAW KG
Clustering raw kilograms would recover farm size and nothing else: Iowa's
biggest corn county and a small Indiana corn county have near-identical
chemistry but differ 50x in mass, so k-means on kg would split them and merge
Iowa with an unrelated big-acreage county. Shares remove scale. But shares
live on the simplex, where Euclidean distance is not meaningful (components
are forced to sum to 1, so they are negatively correlated by construction --
the classic spurious-correlation problem in closed data). The standard fix is
Aitchison's centered log-ratio: divide each part by the row's geometric mean
and take logs. CLR coordinates are real-valued, scale-invariant, and
sub-compositionally coherent, so ordinary k-means/PCA become legitimate.

ZERO HANDLING
Logs need strictly positive parts. Zeros here are mostly *rounded/absent*
values (a compound used on a crop that county does not grow, or use below the
survey's reporting resolution), not structural impossibilities, so they are
replaced rather than dropped. We use multiplicative replacement: every zero
share becomes delta = 0.65 * (smallest non-zero share observed anywhere in
the matrix), and the non-zero parts of that row are multiplied down by
(1 - n_zeros * delta) so the row still sums to 1. The 0.65 factor is the
Martin-Fernandez et al. recommendation for a detection-limit-style
replacement; multiplicative (rather than additive) replacement preserves the
ratios among the observed parts, which is the whole point of the CLR.

SCOPE
2018 (latest year in PNSP), EPest-high, top 40 compounds by national 2018
mass (91% of all applied mass) so the axes stay interpretable. Counties with
< 10,000 kg of top-40 use, or fewer than 5 of those compounds present, are
dropped: below that the composition is one or two reported numbers and the
CLR is dominated by the zero-replacement constant, not by real agronomy.
California is already absent from this file in every year (see eda_02/eda_04).

k IS CHOSEN BY SILHOUETTE over k = 3..10 on the CLR matrix; the printed table
is the justification, and the chosen k is the argmax rather than an elbow
eyeballed after the fact. Caveat worth stating in any write-up: the whole
curve sits in a narrow 0.20-0.24 band, so these are gradients in cropping
system, not disjoint populations -- k=3 wins (stably, across seeds 0/7/42/123)
but the margin over k=5 is small, and k=5 splits the same three groups into
recognisable sub-regions rather than finding anything new.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

ROOT = Path("/home/user/Anthropocene")
OUT = ROOT / "data" / "derived"

YEAR = 2018
N_COMPOUNDS = 40
MIN_KG = 10_000.0        # see docstring: below this the mix is noise, not agronomy
MIN_PRESENT = 5          # need enough observed parts for a log-ratio to mean anything
DELTA_FRAC = 0.65        # multiplicative zero-replacement factor
SEED = 42

STATE_NAME = {
    1: "AL", 4: "AZ", 5: "AR", 8: "CO", 9: "CT", 10: "DE", 12: "FL", 13: "GA",
    16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
    23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS", 29: "MO",
    30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY",
    37: "NC", 38: "ND", 39: "OH", 40: "OK", 41: "OR", 42: "PA", 44: "RI",
    45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT", 50: "VT", 51: "VA",
    53: "WA", 54: "WV", 55: "WI", 56: "WY",
}

# ---------------------------------------------------------------- load
p = pd.read_parquet(OUT / "pnsp_county_panel_corrected.parquet")
p = p[p.year == YEAR].copy()
assert (p.state_fips != 6).all(), "California should already be excluded"

# USGS leaves EPest-high null for ~26k low-volume rows that do carry an
# EPest-low value. Dropping them would silently delete a compound from a
# county's fingerprint; since high >= low by construction, falling back to the
# low estimate is the conservative floor. It is 0.34% of 2018 mass.
p["kg"] = p.high_kg.fillna(p.low_kg)
p = p[p.kg.notna()]

p["fips"] = (p.state_fips.astype(str).str.zfill(2)
             + p.county_fips.astype(str).str.zfill(3))

national = p.groupby("compound").kg.sum().sort_values(ascending=False)
top = list(national.head(N_COMPOUNDS).index)
print(f"=== {YEAR}: top {N_COMPOUNDS} compounds = "
      f"{100*national.head(N_COMPOUNDS).sum()/national.sum():.1f}% of national mass ===")

m = (p[p.compound.isin(top)]
     .pivot_table(index="fips", columns="compound", values="kg",
                  aggfunc="sum", fill_value=0.0)
     .reindex(columns=top, fill_value=0.0))

# ------------------------------------------------------- filter thin counties
total_kg = m.sum(axis=1)
n_present = (m > 0).sum(axis=1)
keep = (total_kg >= MIN_KG) & (n_present >= MIN_PRESENT)
print(f"counties: {len(m)} -> {keep.sum()} after >= {MIN_KG:,.0f} kg and "
      f">= {MIN_PRESENT} compounds "
      f"({100*total_kg[keep].sum()/total_kg.sum():.2f}% of top-{N_COMPOUNDS} mass retained)")
m = m[keep]
total_kg = total_kg[keep]

# --------------------------------------------------------------- CLR
shares = m.div(m.sum(axis=1), axis=0)

S = shares.values
delta = DELTA_FRAC * S[S > 0].min()
zero = S == 0
# multiplicative replacement: zeros -> delta, observed parts scaled by
# (1 - n_zeros*delta) so the row still closes to 1. Scaling every observed part
# by the same factor leaves all of their mutual ratios untouched, which is the
# reason to prefer this over additive replacement.
scale = 1.0 - zero.sum(axis=1, keepdims=True) * delta
X = np.where(zero, delta, S * scale)
assert np.allclose(X.sum(axis=1), 1.0) and (X > 0).all()
print(f"zero replacement: delta = {delta:.3e} "
      f"({100*zero.mean():.1f}% of cells were zero)")

logX = np.log(X)
clr = logX - logX.mean(axis=1, keepdims=True)

# ----------------------------------------------------------- choose k
print(f"\n=== silhouette by k (CLR space, k-means, seed {SEED}) ===")
scores = {}
for k in range(3, 11):
    lab = KMeans(n_clusters=k, n_init=25, random_state=SEED).fit_predict(clr)
    scores[k] = silhouette_score(clr, lab)
    print(f"   k={k:<3} silhouette = {scores[k]:.4f}")
best_k = max(scores, key=scores.get)
print(f"   -> chose k = {best_k} (highest silhouette)")

km = KMeans(n_clusters=best_k, n_init=25, random_state=SEED).fit(clr)
labels = km.labels_

# ----------------------------------------------------------- PCA (plotting)
pca = PCA(n_components=2, random_state=SEED)
pcs = pca.fit_transform(clr)
ev = pca.explained_variance_ratio_
print(f"\nPCA on CLR: PC1 = {100*ev[0]:.1f}%, PC2 = {100*ev[1]:.1f}% "
      f"(cumulative {100*ev.sum():.1f}%)")

# ----------------------------------------------------------- profiles
top10 = list(national.loc[top].head(10).index)
res = pd.DataFrame({
    "fips": m.index,
    "state_fips": [f[:2] for f in m.index],
    "county_fips": [f[2:] for f in m.index],
    "cluster": labels,
    "total_kg": total_kg.values,
    "pc1": pcs[:, 0],
    "pc2": pcs[:, 1],
})
for c in top10:
    res[f"share_{c}"] = shares[c].values          # raw shares, not the imputed ones
res = res.sort_values("fips")
res.to_csv(OUT / "county_clusters_2018.csv", index=False)

res["_state"] = res.state_fips.astype(int).map(STATE_NAME)
mean_share = shares.groupby(labels).mean()

rows = []
print(f"\n=== cluster profiles ({YEAR}) ===")
for c in range(best_k):
    sub = res[res.cluster == c]
    ms = mean_share.loc[c].sort_values(ascending=False)
    st = sub._state.value_counts().head(6)
    comp_str = " | ".join(f"{n}:{v:.3f}" for n, v in ms.head(5).items())
    st_str = " | ".join(f"{n}:{v}" for n, v in st.items())
    rows.append({"cluster": c, "n_counties": len(sub),
                 "mean_total_kg": sub.total_kg.mean(),
                 "median_total_kg": sub.total_kg.median(),
                 "top_compounds": comp_str, "top_states": st_str})
    print(f"\ncluster {c}: n={len(sub)}  mean {sub.total_kg.mean():,.0f} kg/county  "
          f"median {sub.total_kg.median():,.0f} kg")
    print(f"   compounds: {comp_str}")
    print(f"   states:    {st_str}")

pd.DataFrame(rows).to_csv(OUT / "county_cluster_profiles.csv", index=False)
print(f"\nwrote {OUT/'county_clusters_2018.csv'}")
print(f"wrote {OUT/'county_cluster_profiles.csv'}")
