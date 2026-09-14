"""Is US cropland soil being lost faster than it forms? NRI 2022, Tables 17 and 18.

This is the direct test of the "soil is being strip-mined" hypothesis, and it is
the only federal dataset that can run it. RaCA is a single timepoint. SSURGO is
modelled representative values, not repeat measurement. Only NRI tracks the same
statistical sample of land from 1982 to 2022 and reports erosion against T --
the tolerable soil loss rate, the rate below which soil formation is presumed to
keep pace.

Acres eroding above T are acres losing soil faster than it is made. That is the
operational definition of mining a soil, and NRI counts them directly.

One methodological rule governs everything here: NRI BACK-UPDATES prior years at
each release so that observed change is real change rather than method drift.
Every figure below therefore comes from the 2022 release alone. Mixing it with
numbers printed in the 2017 report would manufacture a trend.

Values are transcribed from the PDF tables; margins of error are in the report
and are small relative to the differences discussed.
"""
from pathlib import Path
import pandas as pd

# Table 17 - sheet and rill erosion vs T, CULTIVATED CROPLAND, thousands of acres.
# Columns: <=T, 1-2T, 2-3T, 3-4T, 4-5T, >5T, total
SHEET_RILL = {
    1982: [280215.8, 51115.8, 17463.9, 8930.0, 5504.4, 12491.8, 375721.7],
    1987: [277865.0, 46032.7, 15816.4, 7871.2, 4702.1,  9983.7, 362271.1],
    1992: [267292.3, 39686.7, 13075.2, 5981.6, 3231.6,  6199.9, 335467.3],
    1997: [266351.7, 37183.1, 11317.0, 4821.6, 2440.1,  4161.8, 326275.3],
    2002: [256075.0, 34990.9, 11067.8, 5080.3, 2488.3,  4447.9, 314150.2],
    2007: [251980.7, 31817.6, 10125.2, 4611.3, 2343.4,  4003.0, 304881.2],
    2012: [254549.7, 32479.0, 10880.2, 4835.9, 2476.2,  4275.7, 309496.7],
    2017: [257916.5, 33414.7, 11345.8, 4926.8, 2613.4,  4558.7, 314775.9],
    2022: [256662.2, 33097.3, 11254.9, 4940.9, 2609.3,  4609.6, 313174.2],
}
# Table 18 - wind erosion vs T, CULTIVATED CROPLAND.
WIND = {
    1982: [295293.0, 36737.5, 17743.3, 8864.3, 4956.4, 12127.2, 375721.7],
    1987: [282869.1, 36907.1, 16992.9, 9200.4, 5116.0, 11185.6, 362271.1],
    1992: [272968.9, 30008.8, 13573.6, 7167.9, 3753.3,  7994.8, 335467.3],
    1997: [273820.8, 24860.7, 11472.1, 6120.1, 3278.0,  6723.6, 326275.3],
    2002: [265836.2, 23145.9, 10824.7, 5809.9, 3290.3,  5243.2, 314150.2],
    2007: [258564.8, 22765.0, 10222.3, 5579.3, 2915.7,  4834.1, 304881.2],
    2012: [265111.9, 21425.1,  9906.9, 5462.6, 2774.8,  4815.4, 309496.7],
    2017: [269024.1, 21806.1, 10147.3, 5886.2, 2857.9,  5054.3, 314775.9],
    2022: [267526.8, 21695.5,  9920.1, 5979.8, 2965.0,  5087.0, 313174.2],
}
# Table 17/18 - Conservation Reserve Program land totals (acres retired from production).
CRP_TOTAL = {1982: 0.0, 1987: 13810.9, 1992: 33342.7, 1997: 32694.7, 2002: 31687.8,
             2007: 32833.9, 2012: 23515.0, 2017: 15827.0, 2022: 10152.7}

def frame(d, label):
    rows = []
    for y, v in sorted(d.items()):
        above = sum(v[1:6])
        rows.append({"year": y, "acres_at_or_below_T": v[0], "acres_above_T": above,
                     "acres_above_5T": v[5], "total": v[6],
                     "pct_above_T": 100 * above / v[6],
                     "pct_above_5T": 100 * v[5] / v[6]})
    t = pd.DataFrame(rows); t["measure"] = label
    return t

sr, wd = frame(SHEET_RILL, "sheet_and_rill"), frame(WIND, "wind")
out = pd.concat([sr, wd], ignore_index=True)
out.to_csv(Path("data/derived/nri_cropland_erosion.csv"), index=False)

for t, name in [(sr, "SHEET AND RILL (water) EROSION"), (wd, "WIND EROSION")]:
    print(f"\n{'='*82}\n{name} on CULTIVATED CROPLAND, vs T (tolerable soil loss)\n{'='*82}")
    print(f"{'year':<6} {'acres > T (000)':>16} {'% of cropland > T':>19} {'acres > 5T (000)':>17}")
    for _, r in t.iterrows():
        print(f"{int(r.year):<6} {r.acres_above_T:>16,.0f} {r.pct_above_T:>18.1f}% {r.acres_above_5T:>17,.0f}")
    a, b = t.iloc[0], t.iloc[-1]
    lo = t.loc[t.pct_above_T.idxmin()]
    print(f"\n   1982 -> 2022: {a.pct_above_T:.1f}% -> {b.pct_above_T:.1f}%  "
          f"({b.pct_above_T - a.pct_above_T:+.1f} points, {100*(b.acres_above_T-a.acres_above_T)/a.acres_above_T:+.0f}% fewer acres)")
    print(f"   best year was {int(lo.year)} at {lo.pct_above_T:.1f}%; since then {b.pct_above_T - lo.pct_above_T:+.1f} points")

print(f"\n{'='*82}\nLAND RETIRED FROM PRODUCTION (Conservation Reserve Program)\n{'='*82}")
print(f"{'year':<6} {'CRP acres (000)':>18}")
for y, v in sorted(CRP_TOTAL.items()):
    print(f"{y:<6} {v:>18,.0f}")
peak = max(CRP_TOTAL.items(), key=lambda kv: kv[1])
print(f"\n   peak {peak[0]}: {peak[1]:,.0f}k acres  ->  2022: {CRP_TOTAL[2022]:,.0f}k acres "
      f"({100*(CRP_TOTAL[2022]-peak[1])/peak[1]:+.0f}%)")

print(f"\n{'='*82}\nVERDICT ON THE HYPOTHESIS\n{'='*82}")
sr22, wd22 = sr.iloc[-1], wd.iloc[-1]
print(f"   Cropland eroding above the tolerable rate in 2022:")
print(f"      by water: {sr22.acres_above_T:,.0f}k acres ({sr22.pct_above_T:.1f}% of cultivated cropland)")
print(f"      by wind : {wd22.acres_above_T:,.0f}k acres ({wd22.pct_above_T:.1f}%)")
print(f"   Direction of travel since 1982: IMPROVING on both measures.")
print(f"   Direction of travel since 2007: flat to slightly worse on water erosion.")
