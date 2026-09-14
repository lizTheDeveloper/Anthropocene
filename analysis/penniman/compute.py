#!/usr/bin/env python3
"""
Lens: Penniman / Soul Fire Farm -- who holds the land the rest of this project measures?

Reads the USDA Census of Agriculture bulk QuickStats mirror (2002, 2007, 2012,
2017, 2022) and produces national land-access tables by producer race/ethnicity:
operations, producers, acres operated, tenure class, and sales class.

Run from repo root:
    python3 analysis/penniman/compute.py

Outputs:
    data/derived/lens_penniman_land_access_by_race.csv   (chart data)
    data/derived/lens_penniman_tenure_scale_2022.csv     (supporting)
    data/derived/lens_penniman_salesclass_2022.csv       (supporting)

Notes on the source format:
  * Files are tab-delimited, latin-1, gzipped, with a header row.
  * VALUE is a STRING: thousands separators, and NASS suppression codes
    "(D)" (withheld, individual operation disclosure), "(Z)" (<half unit),
    "(NA)", "(X)", "(L)". Anything starting with "(" is not a number.
  * The race series are "at least one <race> producer/operator on the
    operation" concepts. They OVERLAP: an operation with one Black and one
    White producer is counted in both. They therefore do not sum to the
    national total and must never be stacked.
  * DEFINITIONAL BREAK AT 2017. 2002-2012 report "OPERATORS" (principal +
    up to two additional operators, max 3). 2017-2022 report "PRODUCERS"
    (up to four per operation, all counted equally, with an explicit push to
    enumerate spouses and other decision-makers). The closest bridge is
    "any operator of race X" -> "any producer of race X", used here, but the
    2017 redesign mechanically raised producer counts. Operations and acres
    are far less sensitive to the redesign than producer counts are, which is
    why the headline metric here is acres and operations, not head-counts.
"""

import csv
import gzip
import os
import sys
from collections import defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(REPO, "data", "raw", "usda-nass", "quickstats-bulk")
OUT = os.path.join(REPO, "data", "derived")

YEARS = [2002, 2007, 2012, 2017, 2022]

# canonical group label -> NASS race/ethnicity token inside SHORT_DESC
GROUPS = {
    "White": "WHITE",
    "Black or African American": "BLACK OR AFRICAN AMERICAN",
    "American Indian or Alaska Native": "AMERICAN INDIAN OR ALASKA NATIVE",
    "Asian": "ASIAN",
    "Native Hawaiian or Other Pacific Islander": "NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER",
    "Multi-race": "MULTI-RACE",
    "Hispanic (any race)": "HISPANIC",
}

MEASURES = {
    "ACRES OPERATED": "acres_operated",
    "NUMBER OF OPERATIONS": "operations",
    "NUMBER OF OPERATORS": "people",   # 2002-2012
    "NUMBER OF PRODUCERS": "people",   # 2017-2022
}


def find_census_file(year):
    """Locate qs.census<year>.txt.gz under the dated mirror directory."""
    for d in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, d, f"qs.census{year}.txt.gz")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"qs.census{year}.txt.gz not found under {RAW}")


def parse_value(s):
    """NASS VALUE -> float or None. Suppression codes start with '('."""
    s = (s or "").strip()
    if not s or s.startswith("("):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def split_short_desc(sd):
    """'PRODUCERS, WHITE - ACRES OPERATED' -> ('PRODUCERS, WHITE', 'ACRES OPERATED')"""
    if " - " not in sd:
        return sd, None
    subject, _, measure = sd.rpartition(" - ")
    return subject, measure


def classify_subject(subject, year):
    """
    Return the canonical group label for a race/ethnicity 'any operator/producer'
    subject, or None if this row is not one of the series we want.

    Accepted exactly (no age/sex/tenure/decision-making sub-cuts, no
    PRINCIPAL/SECOND/THIRD operator cuts, no 'ALONE OR COMBINED WITH OTHER
    RACES' variant -- that variant exists only from 2007 and is a different,
    broader concept):
        2002-2012: 'OPERATORS, <TOKEN>'
        2017-2022: 'PRODUCERS, <TOKEN>'
    """
    prefix = "OPERATORS, " if year < 2017 else "PRODUCERS, "
    if not subject.startswith(prefix):
        return None
    tail = subject[len(prefix):]
    for label, token in GROUPS.items():
        if tail == token:
            return label
    return None


def scan(year, want):
    """
    One streaming pass over a census file.

    `want` is a callable(row_dict) -> None or a key tuple. Rows for which it
    returns a key are accumulated into a dict key -> float value.
    Returns (data, suppressed_keys) where suppressed_keys counts rows that
    matched but carried a suppression code.
    """
    path = find_census_file(year)
    data = {}
    suppressed = defaultdict(int)
    with gzip.open(path, "rt", encoding="latin-1", newline="") as fh:
        rdr = csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in rdr:
            key = want(row)
            if key is None:
                continue
            v = parse_value(row["VALUE"])
            if v is None:
                suppressed[key] += 1
                continue
            data[key] = v
    return data, suppressed


# ---------------------------------------------------------------- pass builders

def national_race_want(year):
    def want(row):
        if row["AGG_LEVEL_DESC"] != "NATIONAL" or row["DOMAIN_DESC"] != "TOTAL":
            return None
        subject, measure = split_short_desc(row["SHORT_DESC"])
        if measure not in MEASURES:
            return None
        if subject == "FARM OPERATIONS":
            return ("__ALL__", MEASURES[measure])
        g = classify_subject(subject, year)
        if g is None:
            return None
        return (g, MEASURES[measure])
    return want


def state_race_want(year):
    """State-level Black + total acreage/operations, for the independent check
    and for the geography of the finding."""
    def want(row):
        if row["AGG_LEVEL_DESC"] != "STATE" or row["DOMAIN_DESC"] != "TOTAL":
            return None
        subject, measure = split_short_desc(row["SHORT_DESC"])
        if measure not in ("ACRES OPERATED", "NUMBER OF OPERATIONS"):
            return None
        if subject == "FARM OPERATIONS":
            g = "__ALL__"
        else:
            g = classify_subject(subject, year)
            if g is None:
                return None
        return (row["STATE_ALPHA"], g, MEASURES[measure])
    return want


def area_class_want(year):
    """AREA OPERATED cross-tab, used as the independent re-derivation of the
    national operations count."""
    def want(row):
        if row["AGG_LEVEL_DESC"] != "NATIONAL" or row["DOMAIN_DESC"] != "AREA OPERATED":
            return None
        subject, measure = split_short_desc(row["SHORT_DESC"])
        if measure != "NUMBER OF OPERATIONS":
            return None
        if subject == "FARM OPERATIONS":
            g = "__ALL__"
        else:
            g = classify_subject(subject, year)
            if g is None:
                return None
        return (g, row["DOMAINCAT_DESC"])
    return want


def tenure_want(year):
    def want(row):
        if row["AGG_LEVEL_DESC"] != "NATIONAL" or row["DOMAIN_DESC"] != "TENURE":
            return None
        subject, measure = split_short_desc(row["SHORT_DESC"])
        if measure not in ("ACRES OPERATED", "NUMBER OF OPERATIONS"):
            return None
        if subject == "FARM OPERATIONS":
            g = "__ALL__"
        else:
            g = classify_subject(subject, year)
            if g is None:
                return None
        return (g, row["DOMAINCAT_DESC"], MEASURES[measure])
    return want


def sales_want(year):
    """FARM SALES cross-tab: people (producers/operators) by sales class."""
    def want(row):
        if row["AGG_LEVEL_DESC"] != "NATIONAL" or row["DOMAIN_DESC"] != "FARM SALES":
            return None
        subject, measure = split_short_desc(row["SHORT_DESC"])
        if measure not in ("NUMBER OF PRODUCERS", "NUMBER OF OPERATORS"):
            return None
        if subject in ("PRODUCERS", "OPERATORS"):
            g = "__ALL__"
        else:
            g = classify_subject(subject, year)
            if g is None:
                return None
        return (g, row["DOMAINCAT_DESC"])
    return want


def combined_want(year):
    """Run every filter in a single pass over the (large) file."""
    fns = [
        ("nat", national_race_want(year)),
        ("state", state_race_want(year)),
        ("area", area_class_want(year)),
        ("tenure", tenure_want(year)),
        ("sales", sales_want(year)),
    ]

    def want(row):
        for name, fn in fns:
            k = fn(row)
            if k is not None:
                return (name,) + (k if isinstance(k, tuple) else (k,))
        return None
    return want


# ---------------------------------------------------------------------- driver

def main():
    os.makedirs(OUT, exist_ok=True)
    all_rows = []
    tenure_rows = []
    sales_rows = []
    checks = []

    for year in YEARS:
        sys.stderr.write(f"scanning census{year} ...\n")
        data, suppressed = scan(year, combined_want(year))

        nat = {k[1:]: v for k, v in data.items() if k[0] == "nat"}
        state = {k[1:]: v for k, v in data.items() if k[0] == "state"}
        area = {k[1:]: v for k, v in data.items() if k[0] == "area"}
        tenure = {k[1:]: v for k, v in data.items() if k[0] == "tenure"}
        sales = {k[1:]: v for k, v in data.items() if k[0] == "sales"}

        us_ops = nat[("__ALL__", "operations")]
        us_acres = nat[("__ALL__", "acres_operated")]
        era = "operator (<=3 per farm)" if year < 2017 else "producer (<=4 per farm)"

        for label in GROUPS:
            ops = nat.get((label, "operations"))
            acres = nat.get((label, "acres_operated"))
            people = nat.get((label, "people"))
            if ops is None or acres is None:
                continue
            all_rows.append({
                "year": year,
                "producer_group": label,
                "concept_era": era,
                "operations": int(ops),
                "people": int(people) if people is not None else "",
                "acres_operated": int(acres),
                "us_total_operations": int(us_ops),
                "us_total_acres": int(us_acres),
                "share_of_operations_pct": round(100 * ops / us_ops, 4),
                "share_of_acres_pct": round(100 * acres / us_acres, 4),
                "acres_per_operation": round(acres / ops, 1),
                "us_acres_per_operation": round(us_acres / us_ops, 1),
                "scale_vs_us_avg": round((acres / ops) / (us_acres / us_ops), 3),
                "acres_share_over_ops_share": round((acres / us_acres) / (ops / us_ops), 3),
            })

        # ---- independent check A: sum of state values vs published national
        for label in ("Black or African American", "White", "__ALL__"):
            s_ops = sum(v for (st, g, m), v in state.items()
                        if g == label and m == "operations")
            s_ac = sum(v for (st, g, m), v in state.items()
                       if g == label and m == "acres_operated")
            n_ops = nat.get((label, "operations"))
            n_ac = nat.get((label, "acres_operated"))
            if n_ops:
                checks.append((year, "state-sum vs national", label, "operations",
                               s_ops, n_ops, round(100 * (s_ops - n_ops) / n_ops, 3)))
                checks.append((year, "state-sum vs national", label, "acres",
                               s_ac, n_ac, round(100 * (s_ac - n_ac) / n_ac, 3)))

        # ---- independent check B: AREA OPERATED classes vs TOTAL operations
        # Use the coarse, mutually exclusive partition NASS publishes
        # (1.0-9.9 / 10.0-49.9 / 50-179 / 180-499 / 500+ acres).
        coarse = ["AREA OPERATED: (1.0 TO 9.9 ACRES)",
                  "AREA OPERATED: (10.0 TO 49.9 ACRES)",
                  "AREA OPERATED: (50 TO 179 ACRES)",
                  "AREA OPERATED: (180 TO 499 ACRES)",
                  "AREA OPERATED: (500 OR MORE ACRES)"]
        for label in ("Black or African American", "White", "__ALL__"):
            tot = 0.0
            missing = 0
            for c in coarse:
                v = area.get((label, c))
                if v is None:
                    missing += 1
                else:
                    tot += v
            n_ops = nat.get((label, "operations"))
            if n_ops and missing == 0:
                checks.append((year, "area-class sum vs total", label, "operations",
                               tot, n_ops, round(100 * (tot - n_ops) / n_ops, 3)))

        # ---- tenure (cross-section; concept differs pre/post 2017, see notes)
        for (g, cat, m), v in tenure.items():
            tenure_rows.append({"year": year, "producer_group": g,
                                "tenure": cat.replace("TENURE: ", "").strip("()"),
                                "measure": m, "value": int(v)})

        # ---- sales class
        for (g, cat, ), v in ((k, v) for k, v in sales.items()):
            sales_rows.append({"year": year, "producer_group": g,
                               "sales_class": cat.replace("FARM SALES: ", "").strip("()"),
                               "people": int(v)})

    # ------------------------------------------------------------------ write
    main_csv = os.path.join(OUT, "lens_penniman_land_access_by_race.csv")
    with open(main_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(all_rows, key=lambda r: (r["year"], -r["acres_operated"])))

    ten_csv = os.path.join(OUT, "lens_penniman_tenure_scale_2022.csv")
    ten = [r for r in tenure_rows if r["year"] in (2017, 2022)]
    with open(ten_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ten[0].keys()))
        w.writeheader()
        w.writerows(sorted(ten, key=lambda r: (r["year"], r["producer_group"],
                                               r["tenure"], r["measure"])))

    sal_csv = os.path.join(OUT, "lens_penniman_salesclass_2022.csv")
    sal = [r for r in sales_rows if r["year"] == 2022]
    with open(sal_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sal[0].keys()))
        w.writeheader()
        w.writerows(sorted(sal, key=lambda r: (r["producer_group"], r["sales_class"])))

    # ------------------------------------------------------------- report out
    print("\n=== national land access by producer group ===")
    hdr = f"{'yr':>5} {'group':<42} {'ops':>10} {'acres':>14} {'%ops':>7} {'%acres':>7} {'ac/op':>8} {'gap':>6}"
    print(hdr)
    for r in sorted(all_rows, key=lambda r: (r["producer_group"], r["year"])):
        print(f"{r['year']:>5} {r['producer_group']:<42} {r['operations']:>10,} "
              f"{r['acres_operated']:>14,} {r['share_of_operations_pct']:>7.3f} "
              f"{r['share_of_acres_pct']:>7.3f} {r['acres_per_operation']:>8.1f} "
              f"{r['acres_share_over_ops_share']:>6.2f}")

    print("\n=== verification checks (independent re-derivations) ===")
    print(f"{'yr':>5} {'check':<28} {'group':<28} {'measure':>10} "
          f"{'derived':>16} {'published':>16} {'diff %':>8}")
    for c in checks:
        print(f"{c[0]:>5} {c[1]:<28} {c[2]:<28} {c[3]:>10} "
              f"{c[4]:>16,.0f} {c[5]:>16,.0f} {c[6]:>8.3f}")

    print("\nwrote:")
    for p in (main_csv, ten_csv, sal_csv):
        print("  " + os.path.relpath(p, REPO))


if __name__ == "__main__":
    main()
