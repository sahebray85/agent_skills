#!/usr/bin/env bash
# REVIEW GATE. Names every branch on the delete list holding commits that exist on no
# origin ref. Does NOT abort — a name here can be a pruned remote-tracking ref for a
# branch whose content landed as a squash. Verify each with verify-presquash.sh.
# Usage: audit-unreachable.sh <delete-list-file> [remote]
set -euo pipefail
export MSYS_NO_PATHCONV=1

LIST="${1:?usage: audit-unreachable.sh <delete-list-file>}"
REMOTE="${2:-origin}"

echo "=== branches on the delete list with commits on no $REMOTE ref ==="
FOUND=0; TOTAL_COMMITS=0
while read -r b; do
  [ -z "$b" ] && continue
  n=$(git rev-list --count "$b" --not --remotes="$REMOTE" 2>/dev/null || echo 0)
  if [ "$n" -gt 0 ]; then
    FOUND=$((FOUND + 1)); TOTAL_COMMITS=$((TOTAL_COMMITS + n))
    echo "REVIEW: $b has $n commit(s) on no $REMOTE ref"
    git log --oneline -n "$n" "$b" --not --remotes="$REMOTE" | sed 's/^/         /'
  fi
done < "$LIST"

echo
echo "branches needing review: $FOUND   commits at stake: $TOTAL_COMMITS"
BASELINE=$(git rev-list --count --all --not --remotes="$REMOTE")
echo "baseline unreachable-from-$REMOTE commits (ALL refs): $BASELINE"
echo
echo "RECORD THESE. After deletion the baseline must drop by exactly $TOTAL_COMMITS."
echo "A larger drop means something outside the reviewed set was destroyed."
[ "$FOUND" -gt 0 ] && echo "Run verify-presquash.sh on each REVIEW branch before proceeding."
exit 0
