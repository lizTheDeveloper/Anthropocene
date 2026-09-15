#!/usr/bin/env bash
# Push the current branch with bounded retries on NETWORK failure only.
#
# The obvious one-liner is wrong in a way that hides real failures:
#     if git push ... 2>&1 | tail -1; then echo OK; fi
# A pipeline's exit status is the LAST command's, so that tests `tail`, which
# succeeds whatever git did -- reporting success for a rejected push. Capture
# the output, then test git's own status via PIPESTATUS.
#
# A non-fast-forward rejection is NOT retried: retrying cannot fix it, and the
# fix (fetch and merge, never force on a shared branch) needs a human decision.
set -uo pipefail
branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
for attempt in 1 2 3 4; do
  out="$(git push -u origin "$branch" 2>&1)"; rc=$?
  printf '%s\n' "$out"
  if [ "$rc" -eq 0 ]; then echo "push: ok"; exit 0; fi
  if printf '%s' "$out" | grep -qiE 'non-fast-forward|fetch first|rejected'; then
    echo "push: REJECTED (remote has commits you do not have)." >&2
    echo "      Fetch and merge -- never force-push a shared branch." >&2
    exit 1
  fi
  delay=$((2 ** attempt))
  echo "push: attempt $attempt failed (network), retrying in ${delay}s" >&2
  sleep "$delay"
done
echo "push: FAILED after 4 attempts" >&2
exit 1
