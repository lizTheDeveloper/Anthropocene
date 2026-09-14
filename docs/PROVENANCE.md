# Provenance model

## The claim each row makes

Every row in `data/provenance.csv` asserts: *at `retrieved_at`, the URL `url`
served exactly these bytes, whose SHA-256 is `sha256`.* Nothing more. The file
on disk is unmodified — unzipping, parsing and cleaning all happen downstream in
`data/derived/`, so the checksum always refers to the artifact as served.

Failed acquisitions are recorded too. "We asked on this date and the agency
refused" is itself evidence, and a silent absence is not.

## Two kinds of row

**Direct retrieval.** The ordinary case. `http_status=200`, no `VIA_WAYBACK` tag.

**Archive retrieval.** `notes` begins `VIA_WAYBACK capture=<timestamp>
original_url=<url>`. These come from the Internet Archive's `id_` modifier,
which replays the original unmodified response body. Used where the agency's
edge refuses this network:

| Host | Behaviour | Path taken |
|------|-----------|------------|
| `www.fda.gov` | HTTP 401 on every `/media/…/download` and data page | Internet Archive |
| `www.nrcs.usda.gov` | TCP reset on `/resources/…` and `/sites/default/files/…` (root returns 200) | Internet Archive |
| `water.usgs.gov` | 403/000 on User-Agent alone | direct, with a complete browser header set |

The provenance implication should be stated plainly rather than glossed: an
archive row attests to a **third-party-archived copy captured at a known time**,
not to a live agency fetch by us. For a contested citation that is arguably the
stronger record — an independent custodian with its own timestamp — but it is a
different claim, and a reviewer is entitled to know which one is being made.

## Verification

```bash
python3 scripts/verify_mirror.py
```

Runs three checks:

1. **Inventory** from `provenance.csv` — files, bytes, failures, archive-sourced
   counts per dataset.
2. **Structural validation** — a sample per directory is actually opened. Zips
   must list and test clean, gzips must decompress, PDFs must start `%PDF-`,
   delimited files must not be a saved HTML error page. A truncated download and
   an agency error page both arrive as HTTP 200; only opening the file catches them.
3. **Checksum verification** against every `data/manifests/*.sha256`.

## Re-retrieval

Datasets that remain live have in some cases been altered rather than removed.
Re-run the relevant `acquire_*` script with `force=True`, then diff the new
checksum against the manifest. A changed checksum on an unchanged URL is exactly
the event this whole apparatus exists to catch.
