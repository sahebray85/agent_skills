#!/usr/bin/env bash
# The verification ladder: is a branch's work REALLY on the server under a different SHA?
# Run on every branch audit-unreachable.sh flags, before deleting it.
# Usage: verify-presquash.sh <branch> [base-ref] [scan-depth]
set -euo pipefail
export MSYS_NO_PATHCONV=1   # else `rev:path` args get mangled and files look missing

BR="${1:?usage: verify-presquash.sh <branch> [base-ref] [scan-depth]}"
BASE="${2:-origin/development}"
DEPTH="${3:-800}"

COMMITS=$(git rev-list "$BR" --not --remotes=origin)
if [ -z "$COMMITS" ]; then
  echo "PASS: every commit on $BR already exists on origin. Safe to delete."
  exit 0
fi
echo "branch $BR has $(echo "$COMMITS" | wc -l) commit(s) on no origin ref"

echo
echo "### 1. patch-id -- the decisive test"
# Identical patch-id proves the same change exists on the server under another SHA
# (rebased or cherry-picked), even though the SHA-based reachability test flags it.
# Scan the same-named remote branch first -- a rebased twin is nearly always there, and
# the broad scan costs ~25s per 200 commits.
PIDS=$(mktemp)
CANDIDATES=$(mktemp)
if git rev-parse --verify -q "origin/$BR" >/dev/null 2>&1; then
  git rev-list "origin/$BR" --not "$BASE" > "$CANDIDATES"
  echo "  (scanning origin/$BR: $(wc -l < "$CANDIDATES") commit(s))"
fi
if [ ! -s "$CANDIDATES" ]; then
  git log --remotes=origin --format='%H' -n "$DEPTH" > "$CANDIDATES"
  echo "  (no origin/$BR -- scanning $(wc -l < "$CANDIDATES") recent remote commits)"
fi
while read -r r; do
  git show "$r" 2>/dev/null | git patch-id --stable
done < "$CANDIDATES" > "$PIDS" || true
for c in $COMMITS; do
  pid=$(git show "$c" | git patch-id --stable | awk '{print $1}')
  m=$(awk -v p="$pid" '$1==p{print $2; exit}' "$PIDS" || true)
  if [ -n "$m" ]; then
    echo "  MATCH  $c -> origin $m (identical patch-id)"
  else
    echo "  no match  $c  $(git log -1 --format=%s "$c")"
  fi
done
rm -f "$PIDS" "$CANDIDATES"

echo
echo "### 2. files touched must exist in $BASE (or have been deliberately deleted)"
for c in $COMMITS; do
  git diff-tree --no-commit-id --name-only -r "$c"
done | sort -u | while read -r f; do
  [ -z "$f" ] && continue
  # git ls-tree <rev> -- <path>, never <rev>:<path>: MSYS mangles the colon form.
  if git ls-tree "$BASE" -- "$f" | grep -q .; then
    echo "  present  $f"
  else
    d=$(git log "$BASE" --diff-filter=D --format='%h %ad' --date=short -1 -- "$f")
    if [ -n "$d" ]; then
      echo "  deleted  $f (removed by $d -- deliberate, not lost)"
    else
      echo "  MISSING  $f -- not in $BASE and never deleted there"
    fi
  fi
done

echo
echo "### 3. identifiers introduced must exist in $BASE"
IDS=$(for c in $COMMITS; do git show "$c" -- ; done 2>/dev/null \
      | grep '^+' \
      | grep -oE '[A-Za-z_][A-Za-z0-9_]{5,}' \
      | sort -u | head -40)
for s in $IDS; do
  if git grep -q -w "$s" "$BASE" -- 2>/dev/null; then
    echo "  found    $s"
  else
    n=$(git log -S"$s" --oneline "$BASE" 2>/dev/null | wc -l)
    echo "  ABSENT   $s -- not in $BASE; $n commit(s) in its history ever touched it"
  fi
done

echo
echo "VERDICT: safe to delete if every commit shows MATCH, or if no file is MISSING and"
echo "no identifier is ABSENT. Otherwise KEEP the branch -- the work exists only locally."
