#!/usr/bin/env bash
# Remove worktrees safely. Worktrees MUST go before branches -- git refuses to delete a
# checked-out branch.
# Usage: remove-worktrees.sh [--execute] [--force] <path>...
set -euo pipefail
export MSYS_NO_PATHCONV=1

EXECUTE=0; FORCE=0; PATHS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --execute) EXECUTE=1; shift ;;
    --force)   FORCE=1; shift ;;
    *) PATHS+=("$1"); shift ;;
  esac
done
[ ${#PATHS[@]} -gt 0 ] || { echo "usage: remove-worktrees.sh [--execute] [--force] <path>..." >&2; exit 2; }

for p in "${PATHS[@]}"; do
  echo "--- $p"
  if [ ! -d "$p" ]; then echo "    not present, skipping"; continue; fi
  lock=$(git worktree list --porcelain | grep -A3 -F "worktree $p" | grep '^locked' || true)
  dirty=$(git -C "$p" status --porcelain 2>/dev/null | wc -l || echo "?")
  br=$(git -C "$p" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  echo "    branch=$br dirty=$dirty ${lock:+[$lock]}"

  # 'locked initializing' means a crashed `git worktree add`, NOT a live session.
  # Before forcing past any lock, confirm the reason and that nothing is at stake.
  if [ -n "$lock" ] && [ "$FORCE" -eq 0 ]; then
    echo "    LOCKED -- inspect the reason above, then re-run with --force"; continue
  fi
  if [ "$dirty" != "0" ] && [ "$FORCE" -eq 0 ]; then
    echo "    DIRTY ($dirty entries) -- rescue anything worth keeping, then --force"; continue
  fi
  if [ "$EXECUTE" -eq 0 ]; then echo "    DRY RUN -- would remove"; continue; fi

  if [ -n "$lock" ]; then git worktree unlock "$p" 2>/dev/null || true; fi
  if [ "$FORCE" -eq 1 ]; then
    git worktree remove --force "$p" || true
  else
    git worktree remove "$p" || true
  fi

  # CRITICAL (Windows): "Filename too long" is a PARTIAL failure, not a refusal. Git has
  # already removed the admin entry and freed the branch. Trust ls, not the error text.
  if [ -d "$p" ]; then
    echo "    !! directory still on disk (Windows MAX_PATH). The branch IS already freed."
    echo "    !! clear it via the PowerShell tool:"
    echo "    !!   powershell -File purge-longpath-dir.ps1 -Target '$p'"
  else
    echo "    removed"
  fi
done

if [ "$EXECUTE" -eq 1 ]; then
  git worktree prune
  echo "pruned worktree admin entries"
fi
exit 0
