# Step 09 — Regulatory corpus (for drafting the petition itself)

- [x] **eCFR 40 CFR Part 180** — full XML at issue date 2026-09-09, Title 40
      structure, and the complete amendment history for every section of Part 180
- [x] **Parsed tolerance table** → `data/derived/40cfr180_tolerances.csv`
      (15,416 tolerance rows, 409 sections, 2,474 commodities; plus 1,480
      exemption rows and 1,300 definitional rows, classified not dropped)
- [ ] regulations.gov — dockets, documents, and the full public comment corpus
      from prior pesticide dockets (**needs a free API key**; unauthenticated
      requests return 403)
- [ ] Federal Register API — full text back to 1994
- [ ] EPA Pesticide Chemical Search — registration status, review schedule,
      dockets per active ingredient

## Note on eCFR dates

The versioner API only serves issue dates it has actually published. Today's
date is ahead of it; read `latest_issue_date` from `ecfr_titles.json` first
(Title 40 was at 2026-09-09 when this was retrieved) or the request 404s.

## Why pull the prior comment corpora

Reading what the agency has already accepted and rejected in earlier pesticide
dockets is the cheapest available guide to which arguments survive. It also
shows what the opposing comments looked like.
