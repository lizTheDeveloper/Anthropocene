"""EPA ECOTOX Knowledgebase -- full ASCII database release.

Curated aquatic and terrestrial toxicity literature. This is the federal source
for non-target and soil-organism effects (earthworms, collembola, soil microbial
endpoints) -- the effects residue testing does not measure at all, and therefore
the pillar that carries a soil-degradation argument where PDP cannot.
"""
import sys; sys.path.insert(0, 'scripts')
from fetchlib import fetch_all, session

AGENCY, DATASET = "epa", "ecotox"
items = [
    ("https://gaftp.epa.gov/ecotox/ecotox_ascii_09_15_2026.zip", None),
    ("https://gaftp.epa.gov/ecotox/ecotox-terms-appendix.xlsx", None),
]
fetch_all(items, AGENCY, DATASET, sess=session(), timeout=2400,
          notes="full ECOTOX ASCII release + controlled-terms appendix (codebook)")
