#!/usr/bin/env bash
# Classify every local branch and worktree. Run this BEFORE asking the user anything --
# people decide on data, not descriptions.
# Usage: inventory.sh [--protected "development release master"] [--remote origin]
set -euo pipefail
export MSYS_NO_PATHCONV=1

PROTECTED="development release master"; REMOTE=origin
while [ $# -gt 0 ]; do
  case "$1" in
    --protected) PROTECTED="$2"; shift 2 ;;
    --remote)    REMOTE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
HEADS="$TMP/heads.txt"; : > "$HEADS"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh pr list --state merged --limit 1000 --json headRefName -q '.[].headRefName' \
    2>/dev/null | sort -u > "$HEADS" || true
else
  echo "WARNING: gh unavailable -- PR_MERGED (squash) detection disabled." >&2
fi

echo "=== WORKTREES ==="
git worktree list --porcelain | awk '
  /^worktree /{wt=$2}
  /^branch /{sub("refs/heads/","",$2); print wt "\t" $2}
  /^detached/{print wt "\tDETACHED"}
  /^bare/{print wt "\tBARE"}' > "$TMP/wt.txt"
while IFS=$'\t' read -r path br; do
  [ -z "${path:-}" ] && continue
  if [ "${br:-}" = "BARE" ]; then printf '%s\t(bare repo)\n' "$path"; continue; fi
  dirty=$(git -C "$path" status --porcelain 2>/dev/null | wc -l || echo "?")
  lock=$(git worktree list --porcelain | grep -A3 -F "worktree $path" | grep '^locked' || true)
  printf '%s\t%s\tdirty=%s\t%s\n' "$path" "$br" "$dirty" "$lock"
done < "$TMP/wt.txt"

echo
echo "=== LOCAL BRANCHES ==="
printf '%-55s %-10s %-8s %s\n' BRANCH STATUS UNREACH REMOTE
git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do
  st=UNMERGED
  for p in $PROTECTED; do
    if [ "$b" = "$p" ]; then st=PROTECTED; break; fi
    if git merge-base --is-ancestor "$b" "$REMOTE/$p" 2>/dev/null; then st=ANCESTOR; break; fi
  done
  if [ "$st" = UNMERGED ] && grep -qxF "$b" "$HEADS"; then st=PR_MERGED; fi
  n=$(git rev-list --count "$b" --not --remotes="$REMOTE" 2>/dev/null || echo 0)
  if git rev-parse --verify -q "$REMOTE/$b" >/dev/null 2>&1; then
    if [ "$(git rev-parse "$b")" = "$(git rev-parse "$REMOTE/$b")" ]; then r=same; else r=diverged; fi
  else
    r=NO_REMOTE
  fi
  printf '%-55s %-10s %-8s %s\n' "$b" "$st" "$n" "$r"
done

echo
echo "UNREACH>0 = commits on no $REMOTE ref."
echo "UNMERGED + NO_REMOTE + UNREACH>0 = never pushed: ALWAYS KEEP, deleting is real data loss."
echo "PR_MERGED + UNREACH>0 = pre-squash original: verify with verify-presquash.sh."
echo "totals: $(git for-each-ref refs/heads | wc -l) local, $(git for-each-ref "refs/remotes/$REMOTE" | wc -l) remote-tracking"
