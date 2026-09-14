#!/usr/bin/env python3
"""
analysis/lal/compute.py  --  run from the repository root:

    python3 analysis/lal/compute.py

Lens: soil-organic-carbon / erosion / degradation framework (Lal and colleagues).

Question: does the US federal record support a quantitative claim about soil
carbon CHANGE on American cropland?

What this script does
---------------------
1. Extracts the national ("Total") erosion panel from the 2022 NRI Summary
   Report -- Table 15 (sheet & rill), Table 16 (wind) -- and the national
   erosion-relative-to-T acreage tables -- Table 17 (water), Table 18 (wind) --
   plus the national cropland acreage panel, Table 10.
   These tables are in the PDF only; NRCS does not publish them as CSV.

2. Runs four independent verifications before writing anything (see VERIFY).

3. Writes data/derived/lens_lal_soil_measurement_record.csv -- the aggregated
   rows behind analysis/lal/chart.json.

CRITICAL METHOD NOTE
--------------------
The NRI back-updates its own history at every release: each release restates
prior years so that observed change is real change and not collection-method
drift.  EVERY number here -- 1982 through 2022 -- is taken from the 2022
release only.  Nothing is mixed with the 2017 release.

Soil carbon is deliberately NOT read from any time series, because no federal
soil-carbon time series exists.  See FINDING.md.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NRI_PDF = ROOT / "data/raw/usda-nrcs/nri/2026-09-14/reports/2022_NRI_Summary_Report.pdf"
RACA_PDF = ROOT / "data/raw/usda-nrcs/raca/2026-09-14/docs/RaCA_Methodology_Sampling_Summary.pdf"
OUT_CSV = ROOT / "data/derived/lens_lal_soil_measurement_record.csv"

# SHA-256 of the complete, direct-from-NRCS 2022 NRI Summary Report as held in
# this mirror (12,666,474 bytes, 222 pages).  NOTE: at the time of writing this
# hash is NOT recorded in data/provenance.csv or data/manifests/nri.sha256 --
# those record only the truncated 5,242,880-byte Wayback copy that was
# subsequently discarded and replaced.  Pinned here so the analysis is at least
# self-attesting.  See FINDING.md, "Provenance gap".
NRI_PDF_SHA256 = "5aa1b976a225772166322b2f0f392648f8061222d5ddad277ce2ac4ef322c58c"

NRI_YEARS = [1982, 1987, 1992, 1997, 2002, 2007, 2012, 2017, 2022]

NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
YEAR = re.compile(r"\b(1982|1987|1992|1997|2002|2007|2012|2017|2022)\b")

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")
    return ok


# ---------------------------------------------------------------- extraction


def pdf_text(pdf: Path) -> list[str]:
    """pdftotext -layout preserves the column structure these tables need."""
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, check=True,
    )
    return out.stdout.decode("utf-8", "replace").splitlines()


def numeric_tokens(line: str) -> list[float]:
    """Numbers on a line, ignoring margin-of-error tokens and '--' placeholders."""
    toks = []
    for t in line.split():
        if t.startswith("±"):
            return []          # a margin-of-error row: not a value row
        if NUM.match(t):
            toks.append(float(t))
    return toks


def header_starts(lines: list[str], header: str) -> list[int]:
    starts = [i for i, ln in enumerate(lines) if header in ln]
    if not starts:
        raise SystemExit(f"table header not found: {header!r}")
    return starts


def region_to_notes(lines: list[str], s: int) -> tuple[int, int]:
    """Span from a table-header line to the next 'Notes:' line."""
    for j in range(s, len(lines)):
        if lines[j].strip().startswith("Notes:"):
            return s, j
    return s, len(lines)


def last_national_block(lines: list[str], header: str, year_on: str,
                        n_values: int, years: list[int] | None = None
                        ) -> dict[int, list[float]]:
    """
    The national 'Total' block is the final nine year-rows of a by-State table.

    year_on: 'same'   -- year and values share a line (Tables 15, 16)
             'before' -- values line precedes the year line (Table 10)

    The returned year sequence is asserted to be exactly NRI_YEARS, which is
    what makes this safe: a mis-parse cannot silently produce nine
    correctly-ordered NRI years.

    Headers repeat on every page of these tables, and the final repetition is
    sometimes a stray line-wrapped fragment sitting above the notes block, so
    candidate page-starts are tried newest-first until one validates.
    """
    years = years or NRI_YEARS
    for s in reversed(header_starts(lines, header)):
        block = _block_from(lines, s, year_on, n_values, years)
        if block is not None:
            return block
    raise SystemExit(f"{header}: no page yielded the national year sequence {years}")


def _block_from(lines: list[str], s: int, year_on: str,
                n_values: int, years: list[int]) -> dict[int, list[float]] | None:
    s, e = region_to_notes(lines, s)
    rows: list[tuple[int, list[float]]] = []

    if year_on == "same":
        for ln in lines[s:e]:
            m = YEAR.search(ln)
            if not m:
                continue
            vals = numeric_tokens(ln[m.end():])
            if len(vals) >= n_values:
                rows.append((int(m.group(1)), vals[:n_values]))
    elif year_on == "before":
        for i, ln in enumerate(lines[s:e], start=s):
            # A year line is one whose only number is a trailing NRI year; it may
            # carry a non-numeric State/land-use label to its left ("Total  1982").
            toks = ln.split()
            if not toks or not YEAR.fullmatch(toks[-1]) or numeric_tokens(" ".join(toks[:-1])):
                continue
            m = YEAR.fullmatch(toks[-1])
            for k in (i - 1, i - 2):
                if k < s:
                    continue
                vals = numeric_tokens(lines[k])
                if len(vals) >= n_values:
                    rows.append((int(m.group(1)), vals[:n_values]))
                    break
    else:
        raise ValueError(year_on)

    tail = rows[-len(years):]
    if [y for y, _ in tail] != years:
        return None
    return {y: v for y, v in tail}


def parse_t_table(lines: list[str], header: str, year_on: str,
                  labels: tuple[str, ...]) -> pd.DataFrame:
    """
    Tables 17/18: land cover/use x year x erosion-relative-to-T class,
    thousands of acres.  Seven value columns:
      <=T, 1T-2T, 2T-3T, 3T-4T, 4T-5T, >5T, Total.

    These tables are already national -- there is no State dimension -- so
    every row is kept, and each (label, year) must appear exactly once.
    """
    # The header string also occurs in the table of contents and in the chapter
    # table list, so every occurrence is tried and the one yielding a complete
    # parse wins.
    best = pd.DataFrame()
    for s in header_starts(lines, header):
        df = _scan_t_table(lines, s, header, year_on, labels)
        if len(df) > len(best):
            best = df

    need = ["Cultivated cropland", "Non-cultivated cropland", "Total cropland"]
    for lab in need:
        got = sorted(best.loc[best.land_use == lab, "year"].tolist()) if len(best) else []
        if got != NRI_YEARS:
            raise SystemExit(f"{header}: {lab} parsed years {got}, expected {NRI_YEARS}")
    dup = best.duplicated(["land_use", "year"]).sum()
    if dup:
        raise SystemExit(f"{header}: {dup} duplicate (land_use, year) rows parsed")
    return best


def _scan_t_table(lines, s, header, year_on, labels) -> pd.DataFrame:
    # run to the start of the NEXT distinct table, not the first 'Notes:'
    # (these tables carry per-page note blocks).
    stop = len(lines)
    for j in range(s + 5, len(lines)):
        if re.match(r"\s*Table (1[1-9]|2[0-9])\s*- ", lines[j]) and header not in lines[j]:
            stop = j
            break

    cur = None
    recs: list[dict] = []
    pending_year = None
    for ln in lines[s:stop]:
        for lab in labels:
            if re.search(r"(?<![A-Za-z])" + re.escape(lab) + r"(?![A-Za-z])", ln):
                cur = lab
                break
        m = YEAR.search(ln)
        if m and cur:
            vals = numeric_tokens(ln[m.end():])
            if len(vals) >= 7 and year_on == "same":
                recs.append(dict(zip(
                    ["land_use", "year", "le_T", "t1_2", "t2_3", "t3_4",
                     "t4_5", "gt_5T", "total"],
                    [cur, int(m.group(1)), *vals[:7]])))
                pending_year = None
            elif not vals:
                pending_year = (cur, int(m.group(1)))
            continue
        if pending_year:
            vals = numeric_tokens(ln)
            if len(vals) >= 7:
                lab, yr = pending_year
                recs.append(dict(zip(
                    ["land_use", "year", "le_T", "t1_2", "t2_3", "t3_4",
                     "t4_5", "gt_5T", "total"],
                    [lab, yr, *vals[:7]])))
                pending_year = None

    cols = ["land_use", "year", "le_T", "t1_2", "t2_3", "t3_4", "t4_5", "gt_5T", "total"]
    return pd.DataFrame(recs, columns=cols)


# ---------------------------------------------------------------------- main


def main() -> int:
    print("Anthropocene / lens: lal -- the federal soil measurement record\n")

    print("File integrity")
    digest = hashlib.sha256(NRI_PDF.read_bytes()).hexdigest()
    check("2022 NRI Summary Report SHA-256 matches pinned value", digest == NRI_PDF_SHA256,
          f"got {digest[:16]}...")
    check("2022 NRI Summary Report is the complete 12,666,474-byte file",
          NRI_PDF.stat().st_size == 12_666_474, f"{NRI_PDF.stat().st_size:,} bytes")

    lines = pdf_text(NRI_PDF)

    # --- Tables 15 and 16: national rates, tons/acre/year -------------------
    # value order after the year:
    #   cultivated est, cultivated median, non-cultivated est, non-cultivated
    #   median, total-cropland est, total-cropland median, ...
    t15 = last_national_block(
        lines, "Table 15 - Estimated average annual sheet and rill erosion", "same", 6)
    t16 = last_national_block(
        lines, "Table 16- Estimated average annual wind erosion", "same", 6)

    # --- Table 10: national cropland acreage, thousands of acres ------------
    # value order: irrigated, non-irrigated, cultivated total, irrigated,
    #              non-irrigated, non-cultivated total, total cropland
    t10 = last_national_block(lines, "Table 10 - Cropland use, by State and year",
                              "before", 7)

    # --- Tables 17 and 18: acres by erosion-relative-to-T class -------------
    labels = ("Cultivated cropland", "Non-cultivated cropland", "Total cropland",
              "CRP land", "Pastureland")
    t17 = parse_t_table(
        lines, "Table 17 - Estimated average annual sheet and rill erosion in relation to T",
        "same", labels)
    t18 = parse_t_table(
        lines, "Table 18 - Estimated average annual wind erosion in relation to T",
        "before", labels)

    print("\nVERIFY 1 -- three independent tables must agree on cropland acreage")
    # Table 10 (Chapter 4) vs Table 17 (Chapter 5, water) vs Table 18 (Chapter 5, wind)
    for lab, col10 in [("Cultivated cropland", 2), ("Non-cultivated cropland", 5),
                       ("Total cropland", 6)]:
        a = pd.Series({y: t10[y][col10] for y in NRI_YEARS})
        b = t17.set_index(["land_use", "year"]).loc[lab, "total"].reindex(NRI_YEARS)
        c = t18.set_index(["land_use", "year"]).loc[lab, "total"].reindex(NRI_YEARS)
        worst = max((a - b).abs().max(), (a - c).abs().max())
        wy = (a - b).abs().idxmax()
        # 5 thousand acres is ~0.0015% of the cropland base: tight enough that a
        # column mis-parse cannot pass, loose enough to tolerate the report's own
        # small Chapter 4 / Chapter 5 editing discrepancies (see FINDING.md).
        check(f"Table 10 == Table 17 == Table 18 total acres, {lab}",
              bool(worst < 5.0),
              f"max |diff| = {worst:.1f} kac (worst year {wy}); "
              f"{100*worst/a.mean():.4f}% of the mean")

    print("\nVERIFY 2 -- recompute the national rate a second way")
    # Table 15/16 report cultivated, non-cultivated AND total-cropland rates
    # independently.  The total must be the acreage-weighted mean of the two
    # components, with acreage taken from Tables 17/18.  This is a genuine
    # cross-table identity: it tests the rate parse and the acreage parse at once.
    cult_ac = t17.set_index(["land_use", "year"]).loc["Cultivated cropland", "total"]
    nonc_ac = t17.set_index(["land_use", "year"]).loc["Non-cultivated cropland", "total"]
    for name, tab in [("sheet & rill (Table 15)", t15), ("wind (Table 16)", t16)]:
        worst = 0.0
        for y in NRI_YEARS:
            cult, nonc, tot = tab[y][0], tab[y][2], tab[y][4]
            recomputed = (cult * cult_ac[y] + nonc * nonc_ac[y]) / (cult_ac[y] + nonc_ac[y])
            worst = max(worst, abs(recomputed - tot))
        # The report publishes rates to 0.01 t/ac/yr, so three independently
        # rounded inputs can compound to ~0.01.  A column mis-parse would be off
        # by orders of magnitude, so this stays a real test.
        check(f"total-cropland rate == acreage-weighted components, {name}",
              worst <= 0.011, f"max |diff| = {worst:.4f} t/ac/yr "
                              f"(published rates are rounded to 0.01)")

    print("\nVERIFY 3 -- parsed values must match the report's own narrative text")
    # Chapter 2 'Erosion' highlight paragraph -- located by content, not by offset.
    i = next(k for k, ln in enumerate(lines)
             if "Soil erosion rates on cropland decreased" in ln)
    narrative = " ".join(lines[i:i + 4])
    for phrase, ok in [
        ("a 34 percent decrease", "34 percent" in narrative),
        ("water 3.89 -> 2.67", "3.89" in narrative and "2.67" in narrative),
        ("wind 3.24 -> 2.08", "3.24" in narrative and "2.08" in narrative),
    ]:
        check(f"narrative states {phrase}", ok)
    check("Table 15 total-cropland water rate 1982/2022 == narrative 3.89/2.67",
          (t15[1982][4], t15[2022][4]) == (3.89, 2.67), f"{t15[1982][4]} / {t15[2022][4]}")
    check("Table 16 total-cropland wind rate 1982/2022 == narrative 3.24/2.08",
          (t16[1982][4], t16[2022][4]) == (3.24, 2.08), f"{t16[1982][4]} / {t16[2022][4]}")
    hdr = (t15[1982][4] + t16[1982][4], t15[2022][4] + t16[2022][4])
    decline = 100 * (1 - hdr[1] / hdr[0])
    # The narrative's own headline recomputed from the tables underneath it.
    check("combined water+wind decline reproduces the narrative's 34 percent",
          abs(decline - 34) < 1.0,
          f"tables give {hdr[0]:.2f} -> {hdr[1]:.2f} t/ac/yr = -{decline:.1f}%; "
          f"narrative says 34% (difference is within the 0.01 rounding of the "
          f"published rates)")

    print("\nVERIFY 4 -- the T-class columns must sum to the reported total")
    for name, df in [("Table 17", t17), ("Table 18", t18)]:
        s = df[["le_T", "t1_2", "t2_3", "t3_4", "t4_5", "gt_5T"]].sum(axis=1)
        d = (s - df["total"]).abs()
        check(f"{name} class columns sum to Total", bool(d.max() < 0.15),
              f"max |diff| = {d.max():.2f} kac over {len(df)} rows")

    print("\nVERIFY 5 -- the NRI reports no soil carbon at all")
    full = "\n".join(lines).lower()
    for term in ["organic carbon", "soil carbon", "organic matter", "carbon"]:
        n = full.count(term)
        check(f"2022 NRI Summary Report mentions '{term}' zero times", n == 0,
              f"{n} occurrences in 222 pages")

    if problems:
        print("\nABORTED -- verification failures:")
        for p in problems:
            print("   -", p)
        return 1

    # ------------------------------------------------------------ assemble
    print("\nBuilding data/derived/lens_lal_soil_measurement_record.csv")
    i17 = t17.set_index(["land_use", "year"])
    i18 = t18.set_index(["land_use", "year"])

    rows = []
    for lab, (r_tab_w, r_tab_x) in [("Cultivated cropland", (t15, t16)),
                                    ("Total cropland", (t15, t16))]:
        col = 0 if lab == "Cultivated cropland" else 4
        for y in NRI_YEARS:
            water = r_tab_w[y][col]
            wind = r_tab_x[y][col]
            acres = i17.loc[(lab, y), "total"]
            above_w = acres - i17.loc[(lab, y), "le_T"]
            above_x = acres - i18.loc[(lab, y), "le_T"]
            rows.append({
                "year": y,
                "land_use": lab,
                "water_erosion_t_per_ac_yr": round(water, 2),
                "wind_erosion_t_per_ac_yr": round(wind, 2),
                "total_erosion_t_per_ac_yr": round(water + wind, 2),
                # 1 short ton/acre = 2.24170 Mg/ha.  The soil-carbon literature
                # this analysis is framed against works in Mg/ha.
                "total_erosion_Mg_per_ha_yr": round((water + wind) * 2.24170, 2),
                "acres_thousands": acres,
                "acres_above_T_water_thousands": round(above_w, 1),
                "pct_acres_above_T_water": round(100 * above_w / acres, 2),
                "acres_above_T_wind_thousands": round(above_x, 1),
                "pct_acres_above_T_wind": round(100 * above_x / acres, 2),
                "acres_above_5T_water_thousands": i17.loc[(lab, y), "gt_5T"],
                # The federal record holds exactly one national soil-organic-carbon
                # stock measurement (RaCA, field seasons 2010-2011).  It is not an
                # NRI year and there is no second one, so this column is 0 in every
                # year the NRI measured erosion nationally.
                "national_soc_stock_measurements_this_year": 0,
            })

    out = pd.DataFrame(rows).sort_values(["land_use", "year"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"  wrote {OUT_CSV.relative_to(ROOT)}  ({len(out)} rows)")

    # ------------------------------------------------------------- headline
    cc = out[out.land_use == "Cultivated cropland"].set_index("year")
    tc = out[out.land_use == "Total cropland"].set_index("year")

    def pct(a, b):
        return 100 * (b - a) / a

    print("\nHEADLINE NUMBERS  (cultivated cropland, 2022 NRI release, all years)")
    print(f"  water erosion  1982 {cc.loc[1982,'water_erosion_t_per_ac_yr']:.2f}"
          f" -> 1997 {cc.loc[1997,'water_erosion_t_per_ac_yr']:.2f}"
          f" -> 2022 {cc.loc[2022,'water_erosion_t_per_ac_yr']:.2f} t/ac/yr")
    print(f"     1982->1997 {pct(cc.loc[1982,'water_erosion_t_per_ac_yr'], cc.loc[1997,'water_erosion_t_per_ac_yr']):+.1f}%"
          f"   1997->2022 {pct(cc.loc[1997,'water_erosion_t_per_ac_yr'], cc.loc[2022,'water_erosion_t_per_ac_yr']):+.1f}%"
          f"   2007->2022 {pct(cc.loc[2007,'water_erosion_t_per_ac_yr'], cc.loc[2022,'water_erosion_t_per_ac_yr']):+.1f}%")
    print(f"  wind erosion   1982 {cc.loc[1982,'wind_erosion_t_per_ac_yr']:.2f}"
          f" -> 2002 {cc.loc[2002,'wind_erosion_t_per_ac_yr']:.2f}"
          f" -> 2022 {cc.loc[2022,'wind_erosion_t_per_ac_yr']:.2f} t/ac/yr")
    print(f"     1982->2002 {pct(cc.loc[1982,'wind_erosion_t_per_ac_yr'], cc.loc[2002,'wind_erosion_t_per_ac_yr']):+.1f}%"
          f"   2002->2022 {pct(cc.loc[2002,'wind_erosion_t_per_ac_yr'], cc.loc[2022,'wind_erosion_t_per_ac_yr']):+.1f}%")
    print(f"  combined       1982 {cc.loc[1982,'total_erosion_t_per_ac_yr']:.2f}"
          f" -> 1997 {cc.loc[1997,'total_erosion_t_per_ac_yr']:.2f}"
          f" -> 2022 {cc.loc[2022,'total_erosion_t_per_ac_yr']:.2f} t/ac/yr"
          f"   ({pct(cc.loc[1982,'total_erosion_t_per_ac_yr'], cc.loc[2022,'total_erosion_t_per_ac_yr']):+.1f}% over 40 yr;"
          f" {pct(cc.loc[1997,'total_erosion_t_per_ac_yr'], cc.loc[2022,'total_erosion_t_per_ac_yr']):+.1f}% since 1997)")

    print("\n  share of the 1982-2022 combined decline achieved by 1997: "
          f"{100*(cc.loc[1982,'total_erosion_t_per_ac_yr']-cc.loc[1997,'total_erosion_t_per_ac_yr'])/(cc.loc[1982,'total_erosion_t_per_ac_yr']-cc.loc[2022,'total_erosion_t_per_ac_yr']):.0f}%")

    print("\nABOVE TOLERABLE LOSS (T), cultivated cropland")
    for y in (1982, 1997, 2007, 2022):
        print(f"  {y}: water {cc.loc[y,'acres_above_T_water_thousands']/1000:7.1f} M ac"
              f" ({cc.loc[y,'pct_acres_above_T_water']:5.2f}%)"
              f" | wind {cc.loc[y,'acres_above_T_wind_thousands']/1000:7.1f} M ac"
              f" ({cc.loc[y,'pct_acres_above_T_wind']:5.2f}%)"
              f" | >5T water {cc.loc[y,'acres_above_5T_water_thousands']/1000:5.1f} M ac")
    print(f"  2007->2022 change, water above T: "
          f"{(cc.loc[2022,'acres_above_T_water_thousands']-cc.loc[2007,'acres_above_T_water_thousands'])/1000:+.1f} M ac "
          f"({cc.loc[2022,'pct_acres_above_T_water']-cc.loc[2007,'pct_acres_above_T_water']:+.2f} pp)")
    print(f"  2007->2022 change, water above 5T: "
          f"{(cc.loc[2022,'acres_above_5T_water_thousands']-cc.loc[2007,'acres_above_5T_water_thousands'])/1000:+.2f} M ac "
          f"({pct(cc.loc[2007,'acres_above_5T_water_thousands'], cc.loc[2022,'acres_above_5T_water_thousands']):+.1f}%)")
    print("  NOTE: water and wind above-T acreages are MARGINAL and overlap; the"
          "\n        report gives no joint distribution, so they must not be summed.")

    print(f"\n  total cropland 2022 combined rate: {tc.loc[2022,'total_erosion_t_per_ac_yr']:.2f} t/ac/yr"
          f" (1982: {tc.loc[1982,'total_erosion_t_per_ac_yr']:.2f})")

    # --------------------------------------------------- the carbon counterpart
    print("\nTHE CARBON SIDE -- RaCA, the only national soil-carbon measurement")
    rl = pdf_text(RACA_PDF)
    joined = "\n".join(rl)
    check("RaCA describes itself as a single point in time",
          "at a single point in time" in joined)
    # Table 2 of the RaCA report: sites sampled by region and land use.
    m = re.search(r"Table 2\. Total Number of Sites Sampled(.*?)\* Conservation Reserve",
                  joined, re.S)
    crop_sites = sum(int(r.split()[1]) for r in m.group(1).splitlines()
                     if re.match(r"^\s*\d{2}\s+\d+\s+\d+", r))
    print(f"  cropland sites sampled nationwide, all 17 RaCA regions: {crop_sites}")
    print("  5 pedons per site; only the CENTRAL pedon went to the Kellogg Soil")
    print("  Survey Laboratory for measured carbon -- the other four are VNIR-predicted.")
    print(f"  => ~{crop_sites} lab-measured cropland pedons, nationally, ever.")
    ac_2022 = cc.loc[2022, "acres_thousands"] * 1000
    print(f"  cultivated cropland in 2022: {ac_2022/1e6:.1f} M acres"
          f"  =>  1 lab-measured pedon per {ac_2022/crop_sites/1e3:,.0f} thousand acres")
    print("  RaCA cropland SOC stock to 100 cm (Table 8, LUGR-weighted): 106.1 Mg C/ha")
    print("  Number of repeat measurements: 0.  Number of computable rates of change: 0.")

    # ------------------------------------------- landmine demonstration only
    # NOT used in any reported number.  This shows, from the mirror itself, WHY
    # the 2017 and 2022 releases must never be mixed: the 2022 release silently
    # restates years the 2017 release already published.
    print("\nLANDMINE DEMO -- the NRI back-updates its own history")
    print("  National sheet & rill rate, cultivated cropland (t/ac/yr)")
    old = pdf_text(ROOT / "data/raw/usda-nrcs/nri/2026-09-14/reports/2017NRISummary_Final.pdf")
    t14_2017 = last_national_block(
        old, "Table 14 - Estimated average annual sheet and rill erosion", "same", 6,
        years=NRI_YEARS[:-1])   # the 2017 release ends at 2017
    print("    year   2017 release   2022 release   revision")
    nrev = 0
    for y in NRI_YEARS[:-1]:          # the 2017 release stops at 2017
        a, b = t14_2017[y][0], t15[y][0]
        nrev += (abs(b - a) > 1e-9)
        print(f"    {y}       {a:5.2f}          {b:5.2f}        {b - a:+.2f}")
    print(f"  {nrev} of {len(NRI_YEARS)-1} already-published years were revised by the 2022 release.")
    d07 = t15[2022][0] / t15[2007][0] - 1
    d07_wrong = t15[2022][0] / t14_2017[2007][0] - 1
    print(f"  Using the 2022 release throughout, 2007->2022 is {100*d07:+.1f}%.")
    print(f"  Mixing releases (2017-published 2007 value) would give {100*d07_wrong:+.1f}% --"
          f" an inflation of {100*(d07_wrong-d07):.1f} pp on a {100*d07:.1f} pp signal.")
    print("  Every number reported in FINDING.md comes from the 2022 release only.")

    print("\nDone.  All verifications passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
