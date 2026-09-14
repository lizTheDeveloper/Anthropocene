"""Parse 40 CFR Part 180 into a tidy pesticide-commodity tolerance table.

Part 180 is the operative list for a FFDCA 408(d) petition: a petition to revoke
tolerances has to name the tolerances it targets. The eCFR XML carries them as
HTML-ish tables (<DIV8> sections containing <TABLE>/<TR>/<TD>), one table per
section, with a commodity column and a parts-per-million column.

Output: data/derived/40cfr180_tolerances.csv
  section, section_heading, commodity, ppm, expiration_note
"""
import csv, re, html
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path("/home/user/Anthropocene")
src = sorted(ROOT.glob("data/raw/ecfr/40cfr180-tolerances/*/40CFR180_full_*.xml"))[-1]
out_dir = ROOT / "data" / "derived"; out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "40cfr180_tolerances.csv"

def text(el):
    return re.sub(r"\s+", " ", html.unescape("".join(el.itertext()))).strip()

tree = ET.parse(src)
root = tree.getroot()

rows = []
sections = 0
for div8 in root.iter("DIV8"):
    if div8.get("TYPE") != "SECTION":
        continue
    sections += 1
    sec = div8.get("N", "")
    head_el = div8.find("HEAD")
    heading = text(head_el) if head_el is not None else ""
    for table in div8.iter("TABLE"):
        # Identify the ppm column from the header row when labelled.
        header = []
        for tr in table.iter("TR"):
            ths = tr.findall("TH")
            if ths:
                header = [text(th).lower() for th in ths]
                break
        ppm_idx = next((i for i, h in enumerate(header) if "ppm" in h or "parts per million" in h), 1)
        for tr in table.iter("TR"):
            tds = tr.findall("TD")
            if len(tds) < 2:
                continue
            commodity = text(tds[0])
            if not commodity or commodity.lower().startswith("commodity"):
                continue
            idx = ppm_idx if ppm_idx < len(tds) else 1
            ppm = text(tds[idx])
            note = text(tds[-1]) if len(tds) > idx + 1 else ""
            if not ppm:
                continue
            # Not every table in Part 180 is a tolerance table. Sec. 180.1
            # carries commodity DEFINITIONS and Sec. 180.41 the crop GROUP
            # membership lists; both have the same two-column shape, and
            # counting them as tolerances inflates the total badly. Classify
            # rather than silently drop, so the distinction stays auditable.
            if sec in ("180.1", "180.410") or "crop group" in heading.lower() \
                    or "definitions" in heading.lower():
                row_type = "definition"
            elif re.match(r"^[\d.]+$", ppm.replace(",", "")):
                row_type = "tolerance"
            elif "exempt" in heading.lower() or "exempt" in ppm.lower():
                row_type = "exemption"
            else:
                row_type = "other"
            rows.append({
                "section": sec, "section_heading": heading,
                "commodity": commodity, "ppm": ppm,
                "expiration_note": note if note != ppm else "",
                "row_type": row_type,
            })

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["section", "section_heading", "commodity", "ppm", "expiration_note", "row_type"])
    w.writeheader(); w.writerows(rows)

print(f"source   : {src.name}")
print(f"sections : {sections}")
from collections import Counter
c = Counter(r["row_type"] for r in rows)
print(f"rows extracted: {len(rows):,}  " + "  ".join(f"{k}={v:,}" for k, v in c.most_common()))
print(f"written  : {out.relative_to(ROOT)}")
