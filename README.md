# Anthropocene

Federal data acquisition and exploratory analysis for soil health, pesticide use
and residues, micronutrient decline, and toxicology in the United States.

Start with **[PLAN.md](PLAN.md)**; per-step detail lives in [`plans/`](plans/).

## Layout

```
data/
  raw/<agency>/<dataset>/<retrieval-date>/   mirrored bytes, never transformed
  manifests/<dataset>.sha256                 sha256sum -c compatible
  derived/                                   parsed outputs
  provenance.csv                             url, retrieved_at, sha256, bytes, …
scripts/
  fetchlib.py            provenance-recording fetcher (+ Internet Archive fallback)
  acquire_*.py           one per dataset
  verify_mirror.py       checksums + structural validation + inventory
  smoke_test.py          opens every dataset, confirms schema
  parse_40cfr180.py      tolerance table extraction
plans/                   step-by-step plan with checkboxes
logs/                    acquisition logs
```

## Why every file is checksummed

Federal environmental and agricultural datasets have been removed, altered, or
silently re-scoped repeatedly since January 2025. Anything cited in a petition
needs to exist in our own custody with a retrieval timestamp and a SHA-256. If
the agency later changes the file, our record is the one that survives — and
`verify_mirror.py` makes the comparison mechanical.

Codebooks are captured alongside the data, always. PDP, the FDA residue files,
NCSS lab data and NRI all ship separate reference/definition files; the data
without the manual is uninterpretable in eighteen months.

## Usage

```bash
pip install pandas requests
python3 scripts/acquire_pnsp.py     # or any other acquire_* script
python3 scripts/verify_mirror.py    # inventory + checksum + structure check
python3 scripts/smoke_test.py       # confirm every dataset loads
```

Raw bytes are gitignored. Manifests, provenance, scripts and plans are tracked.

## Current state

363 files / 8.6 GB mirrored across 13 datasets, all checksums verified and no
corrupt archives. See [`docs/ACQUISITION_REPORT.md`](docs/ACQUISITION_REPORT.md)
for what landed, what did not, and why.
