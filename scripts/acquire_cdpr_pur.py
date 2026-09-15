"""California DPR Pesticide Use Reporting -- full-census application records.

PUR is not a survey. Since 1974 every agricultural pesticide application in
California has been reported by law: product, active ingredient, pounds, acres
treated, crop, date, and location to the square-mile (1 mi^2) PLSS section.
That is application-level resolution nothing else in the US offers, which is
why USGS substitutes PUR for California in its own PNSP estimates.

The 1970-1973 microfiche PDF archive (~5.4 GB of scanned images, not records)
is skipped -- it is not machine-readable and adds nothing a soil or residue
analysis can use.
"""
import re, sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session, fetch

ROOT = "https://files.cdpr.ca.gov/pub/outgoing/pur_archives/"
AGENCY, DATASET = "ca-dpr", "pur"

s = session()
listing = s.get(ROOT, timeout=180).text
# IIS directory listing; hrefs are uppercase-tagged.
hrefs = re.findall(r'A HREF="([^"]+)"', listing, re.I)
zips = sorted({h for h in hrefs if re.search(r"/pur\d{4}\.zip$", h, re.I)})
docs = sorted({h for h in hrefs if h.lower().endswith(".txt")})

print(f"Found {len(zips)} annual PUR archives, {len(docs)} readme files")
items = [f"https://files.cdpr.ca.gov{h}" for h in zips]
doc_items = [f"https://files.cdpr.ca.gov{h}" for h in docs]

fetch_all(doc_items, AGENCY, DATASET, subdir="codebooks", sess=s,
          notes="PUR archive readme", license="California public record")
fetch_all(items, AGENCY, DATASET, subdir="annual", sess=s, timeout=2400, pause=1.0,
          notes="full-census application records, section-level (1 sq mi) geography",
          license="California public record")

# The data structure definitions directory holds the field/code lookups without
# which the numeric product and site codes are meaningless.
defs = s.get(ROOT + "Information_Data_Structure_Definitions/", timeout=180).text
dhrefs = sorted({h for h in re.findall(r'A HREF="([^"]+)"', defs, re.I)
                 if re.search(r"\.(zip|txt|pdf|csv)$", h, re.I)})
print(f"Found {len(dhrefs)} codebook files")
fetch_all([f"https://files.cdpr.ca.gov{h}" for h in dhrefs], AGENCY, DATASET,
          subdir="codebooks", sess=s, timeout=900,
          notes="PUR data structure definitions / code lookups",
          license="California public record")
