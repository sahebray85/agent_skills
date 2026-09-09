#!/usr/bin/env bash
# Write the ONLY restore path for deleted branches. Deleted branches leave no reflog.
# Usage: backup-refs.sh [--execute] [--out-dir DIR]
set -euo pipefail
export MSYS_NO_PATHCONV=1

EXECUTE=0; OUT_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --execute)  EXECUTE=1; shift ;;
    --out-dir)  OUT_DIR="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Default to the common git dir so this works for bare repos and worktrees alike,
# and survives the job/session that created it.
if [ -z "$OUT_DIR" ]; then
  OUT_DIR="$(git rev-parse --path-format=absolute --git-common-dir)/branch-cleanup-backups"
fi
STAMP=$(date +%F)
REFS="$OUT_DIR/branch-refs-backup-$STAMP.txt"
WTS="$OUT_DIR/worktree-backup-$STAMP.txt"

N=$(git for-each-ref refs/heads | wc -l)
if [ "$EXECUTE" -eq 0 ]; then
  echo "DRY RUN — would back up $N branches to:"
  echo "  $REFS"
  echo "  $WTS"
  echo "Re-run with --execute."
  exit 0
fi

mkdir -p "$OUT_DIR"
git for-each-ref --format='%(refname:short) %(objectname)' refs/heads > "$REFS"
git worktree list > "$WTS"
echo "backed up $(wc -l < "$REFS") branches -> $REFS"
echo "backed up $(wc -l < "$WTS") worktrees -> $WTS"
echo
echo "Restore any branch with: git branch <name> <sha>"
echo "Objects survive until 'git gc' prunes them (~90 days by default)."
