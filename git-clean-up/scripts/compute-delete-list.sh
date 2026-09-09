#!/usr/bin/env bash
# The merge gate: a branch is deletable if it is an ancestor of any protected branch
# OR is the head ref of a merged PR (catches squash merges, which ancestry misses).
#
# Usage: compute-delete-list.sh --protected "development release master"
#                              [--keep-file FILE] [--remote origin]
#                              [--out FILE] [--gh-limit 1000]
set -euo pipefail
export MSYS_NO_PATHCONV=1   # else MSYS mangles rev:path args

PROTECTED=""; KEEP_FILE=""; REMOTE=origin; OUT=""; GH_LIMIT=1000
while [ $# -gt 0 ]; do
  case "$1" in
    --protected) PROTECTED="$2"; shift 2 ;;
    --keep-file) KEEP_FILE="$2"; shift 2 ;;
    --remote)    REMOTE="$2"; shift 2 ;;
    --out)       OUT="$2"; shift 2 ;;
    --gh-limit)  GH_LIMIT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PROTECTED" ] || { echo "--protected is required (e.g. \"development release master\")" >&2; exit 2; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
KEEP="$TMP/keep.txt"; HEADS="$TMP/merged_pr_heads.txt"

# keep = protected  ∪  branches checked out in ANY worktree  ∪  user's extra keeps
for b in $PROTECTED; do echo "$b"; done > "$KEEP"
git worktree list --porcelain | awk '/^branch /{sub("refs/heads/","",$2); print $2}' >> "$KEEP"
[ -n "$KEEP_FILE" ] && [ -f "$KEEP_FILE" ] && cat "$KEEP_FILE" >> "$KEEP"
sort -u -o "$KEEP" "$KEEP"

: > "$HEADS"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh pr list --state merged --limit "$GH_LIMIT" --json headRefName \
     -q '.[].headRefName' 2>/dev/null | sort -u > "$HEADS" || true
  echo "merged-PR head refs: $(wc -l < "$HEADS")" >&2
else
  echo "WARNING: gh unavailable or unauthenticated — falling back to ANCESTRY ONLY." >&2
  echo "WARNING: squash-merged branches will NOT be detected and will be kept." >&2
fi

RESULT="$TMP/to_delete.txt"
git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do
  grep -qxF "$b" "$KEEP" && continue          # -F: names contain / and . — not regex
  merged=0
  for p in $PROTECTED; do
    if git merge-base --is-ancestor "$b" "$REMOTE/$p" 2>/dev/null; then merged=1; break; fi
  done
  [ "$merged" -eq 0 ] && grep -qxF "$b" "$HEADS" && merged=1
  [ "$merged" -eq 1 ] && echo "$b"
done > "$RESULT" || true

TOTAL=$(git for-each-ref refs/heads | wc -l)
DEL=$(wc -l < "$RESULT")
echo "total local branches: $TOTAL"
echo "kept (protected + checked out + explicit): $(wc -l < "$KEEP")"
echo "DELETABLE: $DEL   (survivors: $((TOTAL - DEL)))"
if [ -n "$OUT" ]; then cp "$RESULT" "$OUT"; echo "list written to $OUT"; else cat "$RESULT"; fi
