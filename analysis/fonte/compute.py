#!/usr/bin/env python3
"""
Lens: Fonte (participatory, whole-bundle agroecosystem assessment).

Question: the federal data system measures the outcomes in the Fonte-lab bundle
-- yield, profitability, erosion control, nutrient cycling, carbon sequestration,
pest regulation, water capture -- in radically unequal depth. Quantify that
asymmetry, and quantify how much of the bundle can be observed *in the same
place at the same time*.

Run from repo root:
    python3 analysis/fonte/compute.py

Writes:
    data/derived/lens_fonte_bundle_coverage.csv   (chart rows: outcome x year grid)
    analysis/fonte/_summary.json                  (headline numbers, for the writeup)

Runtime ~15 min: it streams the full NASS crops file (1.1 GB gz), five Census
files, the NASS environmental file, and the ECOTOX tests table. Nothing is
hard-coded that can be read from the mirror; the two exceptions (RaCA site
totals from the published methodology PDF, RaCA campaign years) are parsed from
the mirrored PDF text and flagged below.

Requires: pdftotext on PATH (poppler) for the NRI and RaCA PDFs.
"""

import collections
import csv
import gzip
import io
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
DERIVED = os.path.join(ROOT, "data", "derived")
OUT_CSV = os.path.join(DERIVED, "lens_fonte_bundle_coverage.csv")
OUT_JSON = os.path.join(ROOT, "analysis", "fonte", "_summary.json")

NASS = os.path.join(RAW, "usda-nass", "quickstats-bulk", "2026-09-14")
CENSUS_YEARS = [2002, 2007, 2012, 2017, 2022]   # census files present in the mirror

# Analysis window = the span of the longest bundle series in the federal record
# (NRI erosion, 1982-2022).
Y0, Y1 = 1982, 2022
YEARS = list(range(Y0, Y1 + 1))


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 1. YIELD  -- NASS QuickStats survey, county x year
# ---------------------------------------------------------------------------
def scan_yield():
    """County-level published crop yields, by year.

    Columns in qs.*.txt (1-indexed, tab-delimited, latin-1):
      4 COMMODITY_DESC  5 CLASS_DESC  7 UTIL_PRACTICE_DESC  8 STATISTICCAT_DESC
      9 UNIT_DESC 11 DOMAIN_DESC 13 AGG_LEVEL_DESC 15 STATE_FIPS 21 COUNTY_CODE
      31 YEAR 38 VALUE
    VALUE is a STRING; suppressed cells are '(D)', '(Z)', etc. -> reject '^('.
    """
    path = os.path.join(NASS, "qs.crops_20260912.txt.gz")
    log("scanning", os.path.basename(path), "(this is the slow one, ~3 min)")
    any_crop = collections.defaultdict(set)   # year -> {fips}
    corn = collections.defaultdict(set)       # year -> {fips}
    with gzip.open(path, "rt", encoding="latin-1", errors="replace") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 38:
                continue
            if p[12] != "COUNTY" or p[7] != "YIELD":
                continue
            if p[5] != "ALL PRODUCTION PRACTICES" or p[10] != "TOTAL":
                continue
            v = p[37]
            if not v or v.startswith("("):
                continue
            try:
                yr = int(p[30])
            except ValueError:
                continue
            if not (Y0 <= yr <= Y1):
                continue
            fips = p[14] + p[20]
            any_crop[yr].add(fips)
            if p[3] == "CORN" and p[6] == "GRAIN" and p[8] == "BU / ACRE":
                corn[yr].add(fips)
    return ({y: len(s) for y, s in any_crop.items()},
            {y: len(s) for y, s in corn.items()})


# ---------------------------------------------------------------------------
# 2. PROFITABILITY + practices + input proxies -- NASS Census of Agriculture
# ---------------------------------------------------------------------------
CENSUS_TARGETS = {
    "profitability": "INCOME, NET CASH FARM, OF OPERATIONS - NET INCOME, MEASURED IN $",
    "cover_crop":    "PRACTICES, LAND USE, CROPLAND, COVER CROP PLANTED, (EXCL CRP) - ACRES",
    "no_till":       "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, NO-TILL - ACRES",
    "fert_expense":  "FERTILIZER TOTALS, INCL LIME & SOIL CONDITIONERS - EXPENSE, MEASURED IN $",
    "chem_expense":  "CHEMICAL TOTALS - EXPENSE, MEASURED IN $",
    "irrigated":     "AG LAND, CROPLAND, HARVESTED, IRRIGATED - ACRES",
    "corn_acres":    "CORN, GRAIN - ACRES HARVESTED",
}


def scan_census():
    out = collections.defaultdict(lambda: collections.defaultdict(set))  # key -> year -> fips
    want = {v: k for k, v in CENSUS_TARGETS.items()}
    for y in CENSUS_YEARS:
        path = os.path.join(NASS, "qs.census%d.txt.gz" % y)
        log("scanning", os.path.basename(path))
        with gzip.open(path, "rt", encoding="latin-1", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) < 38 or p[12] != "COUNTY":
                    continue
                key = want.get(p[9])
                if key is None:
                    continue
                # DOMAIN_DESC must be TOTAL: 2012/2017 repeat income by producer
                # demographic domains, which would triple-count counties.
                if p[10] != "TOTAL":
                    continue
                v = p[37]
                if not v or v.startswith("("):
                    continue
                out[key][int(p[30])].add(p[14] + p[20])
    return {k: {y: len(s) for y, s in d.items()} for k, d in out.items()}


def scan_environmental():
    """County-level treated-acreage (Census-derived) in the environmental file:
    the closest thing to a county nutrient / pest-pressure series."""
    path = os.path.join(NASS, "qs.environmental_20260912.txt.gz")
    log("scanning", os.path.basename(path))
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    with gzip.open(path, "rt", encoding="latin-1", errors="replace") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 38 or p[12] != "COUNTY":
                continue
            if p[9] != "AG LAND - TREATED, MEASURED IN ACRES":
                continue
            dom = p[10]
            if dom == "FERTILIZER":
                key = "fert_treated"
            elif dom.startswith("CHEMICAL, INSECTICIDE"):
                key = "insecticide_treated"
            else:
                continue
            v = p[37]
            if not v or v.startswith("("):
                continue
            yr = int(p[30])
            if Y0 <= yr <= Y1:
                out[key][yr].add(p[14] + p[20])
    return {k: {y: len(s) for y, s in d.items()} for k, d in out.items()}


# ---------------------------------------------------------------------------
# 3. EROSION -- NRI 2022 Summary Report, Table 15 (sheet & rill) / 16 (wind)
# ---------------------------------------------------------------------------
def scan_nri():
    pdf = os.path.join(RAW, "usda-nrcs", "nri", "2026-09-14", "reports",
                       "2022_NRI_Summary_Report.pdf")
    log("extracting", os.path.basename(pdf))
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    lines = txt.split("\n")
    hdr15 = [i for i, l in enumerate(lines)
             if l.strip().startswith("Table 15 - Estimated average annual sheet and rill")]
    hdr16 = [i for i, l in enumerate(lines)
             if l.strip().startswith("Table 16 -") or l.strip().startswith("Table 16-")]
    # hdr15[0]/[1] are table-of-contents and list-of-tables entries; the body
    # starts at the third occurrence (first real page header).
    lo = hdr15[2]
    hi = min(j for j in hdr16 if j > hdr15[-1])
    body = lines[lo:hi]
    rows = [l for l in body if re.match(r"^\s*\S{0,26}\s+(19|20)\d\d\s+\S", l)]
    years = sorted({int(re.search(r"(19|20)\d\d", l).group(0)) for l in rows})
    n_blocks = len(rows) // len(years)
    # Verification: the final block is the national "Total"; its total-cropland
    # sheet-and-rill estimate must match the narrative claim on p.2-9
    # (3.89 t/ac/yr in 1982 -> 2.67 in 2022).
    tail = rows[-len(years):]
    def col(l, k):
        return re.findall(r"-?\d+\.?\d*|--", l.strip())[k]
    nat_1982 = float(col(tail[0], 5))    # 0=year,1=cult est,2=cult med,3=noncult est,4=med,5=total cropland est
    nat_2022 = float(col(tail[-1], 5))
    return {"n_units": n_blocks - 1,      # blocks minus the national Total
            "years": years,
            "n_rows": len(rows),
            "national_1982_t_ac_yr": nat_1982,
            "national_2022_t_ac_yr": nat_2022}


# ---------------------------------------------------------------------------
# 4. SOIL CARBON -- RaCA methodology PDF, Table 2
# ---------------------------------------------------------------------------
def scan_raca():
    pdf = os.path.join(RAW, "usda-nrcs", "raca", "2026-09-14", "docs",
                       "RaCA_Methodology_Sampling_Summary.pdf")
    log("extracting", os.path.basename(pdf))
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    lines = txt.split("\n")
    i = next(i for i, l in enumerate(lines) if "Total Number of Sites Sampled" in l)
    regions, total_sites = [], 0
    for l in lines[i:i + 30]:
        m = re.match(r"^\s{2,}(\d{2})\s+((?:\s*(?:\d+|—|-)){3,})\s*$", l)
        if m:
            regions.append(m.group(1))
            total_sites += sum(int(x) for x in re.findall(r"\d+", m.group(2)))
    single_point = "at a single point in time" in txt
    return {"n_regions": len(regions),
            "sites_in_table2": total_sites,
            "n_lulc_classes": 6,
            "single_point_in_time": single_point,
            "campaign_years": [2010, 2011]}   # NRCS RaCA field campaign


# ---------------------------------------------------------------------------
# 5. SOIL MACROFAUNA / PEST REGULATION -- ECOTOX
# ---------------------------------------------------------------------------
EW_FAMILIES = {"lumbricidae", "megascolecidae", "glossoscolecidae", "eudrilidae",
               "acanthodrilidae", "ocnerodrilidae", "octochaetidae",
               "moniligastridae", "almidae", "sparganophilidae"}
TERMITE_FAMILIES = {"termitidae", "rhinotermitidae", "kalotermitidae",
                    "hodotermitidae", "mastotermitidae", "serritermitidae",
                    "archotermopsidae", "stylotermitidae"}


def scan_ecotox():
    zpath = os.path.join(RAW, "epa", "ecotox", "2026-09-14",
                         "ecotox_ascii_09_15_2026.zip")
    log("scanning", os.path.basename(zpath))
    z = zipfile.ZipFile(zpath)
    base = "ecotox_ascii_09_15_2026/"

    macro = {}
    with z.open(base + "validation/species.txt") as fh:
        rd = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        hdr = rd.readline().rstrip("\n").split("|")
        ix = {h: i for i, h in enumerate(hdr)}
        for line in rd:
            p = line.rstrip("\n").split("|")
            if len(p) < len(hdr):
                continue
            fam = p[ix["family"]].strip().lower()
            order = p[ix["tax_order"]].strip().lower()
            g = None
            if fam in EW_FAMILIES or order in ("haplotaxida", "opisthopora"):
                g = "earthworm"
            elif fam == "formicidae":
                g = "ant"
            elif order == "isoptera" or fam in TERMITE_FAMILIES:
                g = "termite"
            if g:
                macro[p[ix["species_number"]].strip()] = g

    tot = n_field = n_lat = n_us = 0
    all_tests = all_lat = 0
    by_group = collections.Counter()
    with z.open(base + "tests.txt") as fh:
        rd = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        hdr = rd.readline().rstrip("\n").split("|")
        ix = {h: i for i, h in enumerate(hdr)}
        for line in rd:
            p = line.rstrip("\n").split("|")
            if len(p) < len(hdr):
                continue
            all_tests += 1
            lat = p[ix["latitude"]].strip()
            has_lat = lat not in ("", "NR", "NC")
            if has_lat:
                all_lat += 1
            g = macro.get(p[ix["species_number"]].strip())
            if not g:
                continue
            tot += 1
            by_group[g] += 1
            if p[ix["test_location"]].strip().startswith("FIELD"):
                n_field += 1
            if has_lat:
                n_lat += 1
            if p[ix["geographic_code"]].strip().upper().startswith("US"):
                n_us += 1
    return {"all_tests": all_tests, "all_with_latitude": all_lat,
            "macrofauna_species": len(macro), "macrofauna_tests": tot,
            "macrofauna_by_group": dict(by_group),
            "macrofauna_field_tests": n_field,
            "macrofauna_with_latitude": n_lat,
            "macrofauna_us_geocoded": n_us}


# ---------------------------------------------------------------------------
# 6. PESTICIDE PRESSURE -- PNSP corrected county panel (pressure proxy only)
# ---------------------------------------------------------------------------
def scan_pnsp():
    import pyarrow.parquet as pq
    path = os.path.join(DERIVED, "pnsp_county_panel_corrected.parquet")
    log("reading", os.path.basename(path))
    t = pq.read_table(path, columns=["year", "state_fips", "county_fips"])
    d = t.to_pydict()
    per_year = collections.defaultdict(set)
    for y, s, c in zip(d["year"], d["state_fips"], d["county_fips"]):
        per_year[int(y)].add((int(s), int(c)))
    return {y: len(v) for y, v in per_year.items()}


# ---------------------------------------------------------------------------
# Assemble the coverage grid
# ---------------------------------------------------------------------------
def main():
    yield_any, yield_corn = scan_yield()
    census = scan_census()
    env = scan_environmental()
    nri = scan_nri()
    raca = scan_raca()
    eco = scan_ecotox()
    pnsp = scan_pnsp()

    log("NRI check: national total-cropland sheet+rill %.2f (1982) -> %.2f (2022)"
        % (nri["national_1982_t_ac_yr"], nri["national_2022_t_ac_yr"]))

    nri_years = set(nri["years"])
    raca_years = set(raca["campaign_years"])

    # outcome -> (order, direct series spec, proxy series spec)
    # A "direct" series measures the outcome itself, in a place, at a time.
    # A "proxy" series measures an input, a pressure, or a hazard instead.
    rows = []

    def add(outcome, order, year, direct, support, units, basis, source,
            proxy=0, proxy_support="", proxy_units=0, proxy_source="",
            proxy_basis=""):
        rows.append(dict(
            outcome=outcome, outcome_order=order, year=year,
            direct_available=direct, spatial_support=support,
            n_spatial_units=units, measurement_basis=basis, source=source,
            proxy_available=proxy, proxy_spatial_support=proxy_support,
            proxy_n_spatial_units=proxy_units, proxy_source=proxy_source,
            proxy_measurement_basis=proxy_basis))

    for y in YEARS:
        # --- 1. Yield -------------------------------------------------------
        n = yield_any.get(y, 0)
        add("Yield", 1, y, 1 if n else 0, "county" if n else "", n,
            "survey enumeration (published county estimate)",
            "NASS QuickStats, county crop yield")

        # --- 2. Profitability ----------------------------------------------
        n = census["profitability"].get(y, 0)
        add("Profitability", 2, y, 1 if n else 0, "county" if n else "", n,
            "census enumeration (net cash farm income)",
            "NASS Census of Agriculture")

        # --- 3. Erosion control --------------------------------------------
        d = 1 if y in nri_years else 0
        add("Erosion control", 3, y, d, "state" if d else "",
            nri["n_units"] if d else 0,
            "model output (RUSLE2 / WEQ on panel points)",
            "NRCS NRI 2022 Summary Report, Tables 15-16")

        # --- 4. Nutrient cycling & provision --------------------------------
        pn = env["fert_treated"].get(y, 0)
        add("Nutrient cycling", 4, y, 0, "", 0, "no federal series", "",
            proxy=1 if pn else 0, proxy_support="county" if pn else "",
            proxy_units=pn,
            proxy_source="NASS Census: cropland acres receiving fertilizer",
            proxy_basis="input applied, not a cycling rate")

        # --- 5. Carbon sequestration ----------------------------------------
        d = 1 if y in raca_years else 0
        add("Carbon sequestration", 5, y, d, "RaCA region" if d else "",
            raca["n_regions"] if d else 0,
            "one-time field campaign; most SOC values predicted from VNIR spectra",
            "NRCS Rapid Carbon Assessment (RaCA)")

        # --- 6. Pest regulation ---------------------------------------------
        pn = pnsp.get(y, 0)
        add("Pest regulation", 6, y, 0, "", 0, "no federal series", "",
            proxy=1 if pn else 0, proxy_support="county" if pn else "",
            proxy_units=pn,
            proxy_source="USGS PNSP county pesticide use (corrected panel)",
            proxy_basis="modelled chemical pressure, not the regulating service")

        # --- 7. Water capture & storage -------------------------------------
        pn = census["irrigated"].get(y, 0)
        add("Water capture", 7, y, 0, "", 0, "no federal series", "",
            proxy=1 if pn else 0, proxy_support="county" if pn else "",
            proxy_units=pn,
            proxy_source="NASS Census: irrigated harvested cropland",
            proxy_basis="water applied, not infiltration or storage")

        # --- 8. Soil macrofauna (functional indicator) -----------------------
        add("Soil macrofauna", 8, y, 0, "", 0, "no federal series", "",
            proxy=0, proxy_support="", proxy_units=0,
            proxy_source="ECOTOX: lab bioassays only",
            proxy_basis="hazard endpoints with no place and no repeat")

    os.makedirs(DERIVED, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log("wrote", OUT_CSV, len(rows), "rows")

    # ---- headline numbers ------------------------------------------------
    n_out = 8
    bundle7 = ["Yield", "Profitability", "Erosion control", "Nutrient cycling",
               "Carbon sequestration", "Pest regulation", "Water capture"]
    direct_by_outcome = collections.Counter()
    for r in rows:
        if r["direct_available"]:
            direct_by_outcome[r["outcome"]] += 1
    outcome_years_possible = len(bundle7) * len(YEARS)
    outcome_years_filled = sum(direct_by_outcome[o] for o in bundle7)

    # observation cells = spatial units x years with a direct observation
    cells = collections.Counter()
    for r in rows:
        if r["direct_available"]:
            cells[r["outcome"]] += r["n_spatial_units"]

    # joint observability: for each pair of the 7, is there any common spatial
    # support and any common year?
    support_years = {
        "Yield":               ("county", set(y for y in YEARS if yield_any.get(y))),
        "Profitability":       ("county", set(census["profitability"])),
        "Erosion control":     ("state", nri_years & set(YEARS)),
        "Nutrient cycling":    (None, set()),
        "Carbon sequestration": ("RaCA region", raca_years & set(YEARS)),
        "Pest regulation":     (None, set()),
        "Water capture":       (None, set()),
    }
    # county nests in state; RaCA regions (MLRA soil survey regions) do not nest
    # in states or counties, so a RaCA-region series joins only to series that
    # can be aggregated up from counties.
    def joinable(a, b):
        sa, ya = support_years[a]
        sb, yb = support_years[b]
        if sa is None or sb is None:
            return False, set()
        common = ya & yb
        if not common:
            return False, set()
        if "RaCA region" in (sa, sb):
            other = sb if sa == "RaCA region" else sa
            if other != "county":       # state-level series cannot be cut to RaCA regions
                return False, set()
        return True, common

    pairs = []
    for i, a in enumerate(bundle7):
        for b in bundle7[i + 1:]:
            ok, common = joinable(a, b)
            pairs.append({"a": a, "b": b, "joinable": ok,
                          "n_common_years": len(common),
                          "common_years": sorted(common)})
    n_pairs_ok = sum(1 for p in pairs if p["joinable"])

    # max simultaneously observable, by year, at a common spatial support
    max_simul = {}
    for y in YEARS:
        # county support: outcomes published at county level
        cnty = [o for o in bundle7 if support_years[o][0] == "county" and y in support_years[o][1]]
        # state support: county series can roll up to state; state series stay
        st = [o for o in bundle7 if support_years[o][0] in ("county", "state") and y in support_years[o][1]]
        max_simul[y] = {"county": len(cnty), "state": len(st),
                        "county_outcomes": cnty, "state_outcomes": st}
    best_state = max(v["state"] for v in max_simul.values())
    best_county = max(v["county"] for v in max_simul.values())
    n_years_at_best_state = sum(1 for v in max_simul.values() if v["state"] == best_state)
    n_years_at_best_county = sum(1 for v in max_simul.values() if v["county"] == best_county)

    summary = {
        "window": [Y0, Y1],
        "n_years": len(YEARS),
        "timepoints_per_outcome": {o: direct_by_outcome[o] for o in bundle7 + ["Soil macrofauna"]},
        "observation_cells_per_outcome": {o: cells[o] for o in bundle7 + ["Soil macrofauna"]},
        "outcome_years_possible": outcome_years_possible,
        "outcome_years_filled": outcome_years_filled,
        "outcome_years_pct": round(100.0 * outcome_years_filled / outcome_years_possible, 1),
        "share_of_filled_that_is_yield": round(
            100.0 * direct_by_outcome["Yield"] / outcome_years_filled, 1),
        "pairs_total": len(pairs),
        "pairs_jointly_observable": n_pairs_ok,
        "pairs": pairs,
        "max_simultaneous_state": best_state,
        "years_at_max_state": n_years_at_best_state,
        "max_simultaneous_county": best_county,
        "years_at_max_county": n_years_at_best_county,
        "nri": nri,
        "raca": raca,
        "ecotox": eco,
        "yield_any_crop_counties_2022": yield_any.get(2022, 0),
        "yield_corn_counties_2022": yield_corn.get(2022, 0),
        "census_corn_acres_counties_2022": census["corn_acres"].get(2022, 0),
        "census_practice_years": sorted(census["cover_crop"]),
        "census_profitability_years": sorted(census["profitability"]),
        "pnsp_years": [min(pnsp), max(pnsp)],
        "pnsp_counties_median": sorted(pnsp.values())[len(pnsp) // 2],
    }
    with open(OUT_JSON, "w") as fh:
        json.dump(summary, fh, indent=2)
    log("wrote", OUT_JSON)

    log("\n--- headline ---")
    log("direct timepoints per outcome:", summary["timepoints_per_outcome"])
    log("observation cells per outcome:", summary["observation_cells_per_outcome"])
    log("outcome-years filled: %d / %d (%.1f%%), %.1f%% of them yield"
        % (outcome_years_filled, outcome_years_possible,
           summary["outcome_years_pct"], summary["share_of_filled_that_is_yield"]))
    log("jointly observable pairs: %d / %d" % (n_pairs_ok, len(pairs)))
    log("max simultaneous outcomes: %d (state, in %d of %d years); %d (county, in %d years)"
        % (best_state, n_years_at_best_state, len(YEARS), best_county, n_years_at_best_county))


if __name__ == "__main__":
    main()
