#!/bin/bash
# Re-acquire the full mirror in three lanes so a home connection is not
# saturated by ten simultaneous multi-GB transfers. Lanes are ordered so the
# largest download in each starts last, and every acquire_* script is
# idempotent -- already-present files are checksummed and skipped, so this is
# safe to re-run after an interruption.
cd "$(dirname "$0")/.."
lane() {
  for s in "$@"; do
    echo "=== $(date -u +%H:%M:%S) starting $s ==="
    python3 "scripts/$s" 2>&1
    echo "=== $(date -u +%H:%M:%S) finished $s ==="
  done
}
lane acquire_pnsp.py acquire_ecfr.py acquire_pdp.py acquire_nass_bulk.py   > logs/lane1.log 2>&1 &
lane acquire_ecotox.py acquire_historical_foods.py acquire_fdc.py acquire_cdpr_pur.py > logs/lane2.log 2>&1 &
lane acquire_raca.py acquire_nri.py acquire_nhanes.py acquire_water_wqp.py > logs/lane3.log 2>&1 &
wait
echo "ALL LANES COMPLETE"
