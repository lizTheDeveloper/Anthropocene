"""Historical food composition -- the baseline for any micronutrient-decline claim.

The 20th-century values needed for a decline argument exist only as scanned
print. This script puts the source scans into custody; OCR and per-value
verification are a separate, much larger job (see plans/step-05-nutrition.md).

Two landmines govern how these can be used:
  * Analytical method drift. A 1896 Kjeldahl nitrogen figure and a 2018 value
    are not the same measurement. Restrict comparisons to nutrients where the
    method is comparable or the bias is characterisable, and read the methods
    sections -- which is why the full scans are captured, not just the tables.
  * The dilution effect. Declining mineral concentration is conventionally
    attributed to cultivar selection for yield, not soil depletion. Same-cultivar
    comparison or archived-sample reanalysis is the only clean way past it.

Every extracted value will need a page citation. Budget accordingly.
"""
import sys, time; sys.path.insert(0, 'scripts')
from fetchlib import fetch, fetch_all, session

AGENCY, DATASET = "usda-historical", "food-composition"
s = session()

print("== govinfo: Composition of Foods (Agriculture Handbook No. 8) ==")
fetch("https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo17007/pdf/GOVPUB-A-PURL-gpo17007.pdf",
      AGENCY, DATASET, filename="AH8_GOVPUB-A-PURL-gpo17007.pdf", subdir="handbook-8", sess=s,
      timeout=900, notes="Agriculture Handbook No. 8, Composition of Foods (govinfo scan)")

# Atwater & Woods, USDA Bulletin No. 28 -- the origin point of US food composition data.
print("\n== Internet Archive: Atwater & Woods, USDA Bulletin No. 28 ==")
atwater = ["chemicalcomposit28atwa", "chemicalcomposit28atwa_0"]
for ident in atwater:
    for ext, sub in [("pdf", "bulletin-28"), ("djvu.txt", "bulletin-28-ocr")]:
        r = fetch(f"https://archive.org/download/{ident}/{ident}.{ext}",
                  AGENCY, DATASET, filename=f"{ident}.{ext}", subdir=sub, sess=s, timeout=900,
                  notes="Atwater & Woods, The Chemical Composition of American Food Materials, USDA Bull. 28")
        print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>12,}  {ident}.{ext}")
        time.sleep(2)

# Agriculture Handbook No. 8 sectional revisions (AH-8-1 .. AH-8-21), as available.
print("\n== Internet Archive: AH-8 sectional revisions ==")
sectionals = ["compositionoffoo816matt", "CAT87882023", "micro_IA41152616_0421",
              "proceduresforcal6213merr", "CAT10696850", "CAT78693574"]
for ident in sectionals:
    r = fetch(f"https://archive.org/download/{ident}/{ident}.pdf",
              AGENCY, DATASET, filename=f"{ident}.pdf", subdir="handbook-8-sectionals",
              sess=s, timeout=900, notes="AH-8 sectional revision / related USDA composition publication")
    print(f"  [{'ok ' if r['ok'] else 'FAIL'}] {r.get('bytes',0):>12,}  {ident}.pdf")
    time.sleep(2)
