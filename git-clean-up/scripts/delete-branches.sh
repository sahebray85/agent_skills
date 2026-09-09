#!/usr/bin/env bash
# Delete the branches on the list. Uses -D deliberately: -d checks merged-into-UPSTREAM,
# which wrongly refuses branches that are ahead of their own remote but fully merged into
# the integration branch. The merge gate + review pause is the safety, not -d.
# Usage: delete-branches.sh [--execute] <delete-list-file>
set -euo pipefail
export MSYS_NO_PATHCONV=1

EXECUTE=0; LIST=""
while [ $# -gt 0 ]; do
  case "$1" in
    --execute) EXECUTE=1; shift ;;
    *) LIST="$1"; shift ;;
  esac
done
if [ -z "$LIST" ] || [ ! -f "$LIST" ]; then
  echo "usage: delete-branches.sh [--execute] <delete-list-file>" >&2; exit 2
fi

N=$(grep -c . "$LIST" || true)
if [ "$EXECUTE" -eq 0 ]; then
  echo "DRY RUN -- would delete $N branches:"
  cat "$LIST"
  echo
  echo "Confirm the backup file from backup-refs.sh exists, then re-run with --execute."
  exit 0
fi

ERR=$(mktemp); trap 'rm -f "$ERR"' EXIT
xargs -a "$LIST" -d '\n' -r git branch -D 2>"$ERR" || true
ERRS=$(grep -c 'error:' "$ERR" || true)
echo "requested $N, failed $ERRS, deleted $((N - ERRS))"

if grep -q 'used by worktree' "$ERR"; then
  echo
  echo "=== a branch is held by a worktree ==="
  # Usually a crashed session's leftover interactive rebase: the worktree's HEAD is on
  # some other branch, but rebase-merge/head-name still claims this one.
  GD=$(git rev-parse --path-format=absolute --git-common-dir)
  for f in "$GD"/worktrees/*/rebase-merge/head-name "$GD"/worktrees/*/rebase-apply/head-name; do
    [ -f "$f" ] && echo "  leftover rebase: $f -> $(cat "$f")"
  done
  echo "DO NOT abort a rebase you did not start. Leave the branch and report it."
fi
grep 'error:' "$ERR" >&2 || true
exit 0
