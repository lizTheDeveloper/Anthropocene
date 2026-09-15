# Step 01 — Acquisition infrastructure & provenance

Goal: nothing enters the analysis without a URL, a retrieval timestamp, and a
checksum. If an agency later alters or withdraws a file, our copy is the record.

- [x] Directory layout (`data/raw`, `data/manifests`, `data/codebooks`, `plans`, `scripts`)
- [x] `scripts/fetchlib.py` — streaming fetcher, SHA-256, retry with exponential backoff
- [x] `data/provenance.csv` ledger (url, retrieved_at, sha256, bytes, agency, dataset, license, notes)
- [x] Per-dataset `sha256sum -c`-compatible manifests
- [x] Failed acquisitions recorded too — "the agency refused" is itself evidence
- [x] Browser header set (agency WAFs reject UA-only requests; USGS needed the full set)
- [x] Internet Archive `id_` fallback for hosts that block this network (FDA)
- [x] `.gitignore` excludes raw bytes, tracks manifests and provenance
- [ ] `scripts/verify_mirror.py` — re-verify every manifest, report drift
- [ ] Re-retrieval cron: re-fetch headline files quarterly, diff checksums, flag silent edits

## Notes

- Raw bytes are never transformed on the way in. Unzip/parse/clean all happen
  downstream so the checksum always refers to the file as served.
- `bundleCoversEveryHost: true` on the agent proxy — 401/403 responses seen here
  are agency-side WAF decisions, not egress policy denials.
