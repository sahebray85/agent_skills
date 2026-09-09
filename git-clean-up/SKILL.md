---
name: git-clean-up
description: Safely delete merged local branches and stale worktrees from a cluttered repo, including squash-merged branches that `git branch --merged` misses. Use when the user wants to clean up, prune, or delete merged/stale branches or worktrees, when `git branch` output has become unusable, or when deciding whether a branch's work is safe to delete.
---

# git-clean-up

Deletes merged local branches and stale worktrees. Never deletes work that exists
nowhere on the server.

**Deleted branches leave no reflog entry.** The backup file written in step 1 is the
only restore path. Never skip it.

## Core rules

- **Ancestry alone is wrong.** A squash-merged branch is not an ancestor of anything.
  The gate must be `ancestry ∪ merged-PR head refs` — on one real repo, ancestry alone
  missed 73 of 90 merged branches.
- **Union all long-lived branches.** `release` and `master` are usually *not* ancestors
  of `development`; gate against all three or hotfix branches get misjudged.
- **Worktrees before branches.** Git refuses to delete a checked-out branch.
- **`-D`, not `-d`.** `-d` checks merged-into-*upstream*, not into your integration
  branch, and wrongly refuses branches that are ahead of their own remote but fully
  merged into `development`. The step-3 gate is the real safety, not `-d`.
- **Local only by default.** Remote deletion is irreversible for teammates — a separate,
  separately-approved pass.
- **Never touch a rebase you did not start.** If `git branch -D` reports "used by
  worktree at X", check `X/.git/worktrees/*/rebase-merge/head-name` and stop. Report it.

## Workflow

Ask these five, one at a time, recommending an answer for each. Show the inventory
table (`scripts/inventory.sh`) *before* asking — users decide on data, not descriptions.

| # | Question | Default |
|---|---|---|
| 1 | Which worktrees? | Only throwaway ones (`.claude/worktrees/`); named ones are reused across sessions |
| 2 | Local only, or remote too? | **Local only** |
| 3 | Merge gate | Ancestry ∪ merged-PR heads |
| 4 | Pre-squash branches (content merged, commit objects local-only) | Delete after verification ladder passes |
| 5 | Never-pushed branches | **Always keep** — deleting them is real data loss |

Then run, pausing once at step 4:

```bash
S=<this skill dir>/scripts
bash $S/inventory.sh                                          # 1. classify everything
bash $S/backup-refs.sh --execute                              # 2. durable restore file
bash $S/compute-delete-list.sh --protected "development release master" \
     --keep-file extra-keeps.txt --out /tmp/to_delete.txt     # 3. the gate
bash $S/audit-unreachable.sh /tmp/to_delete.txt               # 4. REVIEW PAUSE
bash $S/remove-worktrees.sh --execute <paths...>              # 5. worktrees first
bash $S/delete-branches.sh --execute /tmp/to_delete.txt       # 6.
bash $S/verify.sh <backup-file> "development release master"  # 7.
```

Every script is dry-run unless given `--execute`. Bash scripts run via the Bash tool;
`purge-longpath-dir.ps1` via the PowerShell tool.

## Step 4 — the review pause

`audit-unreachable.sh` names every branch on the delete list holding commits that exist
on no origin ref. **A name appearing here is not automatically a crisis:** `--prune` drops
the remote-tracking ref of a branch deleted on GitHub after its PR merged, which exposes
its commits as newly unreachable even though the content landed via the squash.

Run `scripts/verify-presquash.sh <branch> origin/<integration>` on each. It passes if the
patch-id matches a remote commit, or if every file it touched exists in the integration
branch (or was deliberately deleted later) and every identifier it introduced is present.
Only if that fails does the branch come off the list.

Record `git rev-list --count --all --not --remotes=origin` here; step 7 asserts the drop
equals exactly the commits you consented to lose.

## Windows

Both of these have bitten this workflow and are handled inside the scripts:

- **`git worktree remove` failing with "Filename too long" is partial, not atomic.** Git
  still removes the admin entry and frees the branch, leaving the directory orphaned.
  Verify with `ls`, not the error text; clear the remains with `purge-longpath-dir.ps1`.
- **MSYS mangles `rev:path` arguments** (`origin/dev:.gitignore` → `origin\dev;.gitignore`),
  producing false "file missing" results. Scripts export `MSYS_NO_PATHCONV=1` and use
  `git ls-tree <rev> -- <path>`.

See [REFERENCE.md](REFERENCE.md) for the classification schema, the verification ladder,
and the restore procedure.
