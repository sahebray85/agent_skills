#!/usr/bin/env bash
# Post-cleanup assertions.
# Usage: verify.sh <backup-refs-file> "<protected branches>" [expected-drop] [remote]
set -euo pipefail
export MSYS_NO_PATHCONV=1

BACKUP="${1:?usage: verify.sh <backup-refs-file> \"<protected>\" [expected-drop] [remote]}"
PROTECTED="${2:?protected branch list required}"
DROP="${3:-}"
REMOTE="${4:-origin}"
FAIL=0

echo "=== protected branches must be identical to the backup ==="
for p in $PROTECTED; do
  want=$(awk -v b="$p" '$1==b{print $2}' "$BACKUP")
  got=$(git rev-parse --verify -q "$p" 2>/dev/null || echo MISSING)
  if [ "$want" = "$got" ]; then
    echo "OK    $p $got"
  else
    echo "FAIL  $p was=$want now=$got"; FAIL=1
  fi
done

echo
echo "=== no deleted branch may have carried commits that exist on no $REMOTE ref ==="
LOST=0
while read -r b sha; do
  [ -z "${b:-}" ] && continue
  git rev-parse --verify -q "$b" >/dev/null 2>&1 && continue   # still present, fine
  n=$(git rev-list --count "$sha" --not --remotes="$REMOTE" 2>/dev/null || echo 0)
  if [ "$n" -gt 0 ]; then
    echo "GONE  $b ($sha) held $n commit(s) on no $REMOTE ref"
    echo "      restore with: git branch $b $sha"
    LOST=$((LOST + 1))
  fi
done < "$BACKUP"
if [ "$LOST" -eq 0 ]; then
  echo "OK    nothing carrying origin-only work was deleted"
else
  echo "NOTE  the $LOST GONE entries are expected ONLY if you consented to each at the review pause."
  echo "      Cross-check against the audit-unreachable.sh output. Any name not on that list"
  echo "      is real data loss -- restore it now with the command shown."
fi

echo
NOW=$(git rev-list --count --all --not --remotes="$REMOTE")
echo "unreachable-from-$REMOTE commits now: $NOW"
if [ -n "$DROP" ]; then
  echo "expected drop from the step-4 baseline: $DROP"
  echo "(a LARGER drop means work outside the reviewed set was destroyed -- restore from $BACKUP)"
fi

echo
echo "=== surviving worktrees (dirty counts should match pre-cleanup) ==="
git worktree list --porcelain \
  | awk '/^worktree /{wt=$2} /^branch /{sub("refs/heads/","",$2); print wt "\t" $2}' \
  | while IFS=$'\t' read -r path br; do
      echo "$path  $br  dirty=$(git -C "$path" status --porcelain 2>/dev/null | wc -l)"
    done

echo
echo "local branches remaining: $(git for-each-ref refs/heads | wc -l)"
exit $FAIL
