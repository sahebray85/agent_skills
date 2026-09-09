# git-clean-up reference

## Merge-status vocabulary

| Term | Meaning |
|---|---|
| `ANCESTOR` | branch tip is an ancestor of a protected branch — `git branch --merged` finds these |
| `PR_MERGED` | not an ancestor, but a **merged PR** has this branch as its head ref (squash merge) |
| `UNMERGED` | neither |
| *unreachable* | `git rev-list <b> --not --remotes=origin` is non-empty — commits on **no** origin ref |

`UNMERGED` and *unreachable* are independent axes, and conflating them is the main way this
job goes wrong. A branch can be merged (content on the server) yet unreachable (its own
commit objects local-only) — that is exactly what a squash merge produces.

## The classification grid

Every local branch lands in one of these. Only rows 1–4 are safely deletable.

| # | Status | vs `origin/<same-name>` | Verdict |
|---|---|---|---|
| 1 | ANCESTOR | SHA identical | delete |
| 2 | ANCESTOR | local ahead (extras already in the integration branch) | delete |
| 3 | ANCESTOR | no remote branch exists | delete |
| 4 | PR_MERGED | SHA identical | delete |
| 5 | PR_MERGED | unreachable commits | **verify first** — pre-squash original |
| 6 | UNMERGED | SHA identical (pushed; PR open or closed) | keep |
| 7 | UNMERGED | never pushed | **keep — deleting is real data loss** |
| 8 | PROTECTED | — | never touch |

## The verification ladder

For row 5, in increasing order of strength. `verify-presquash.sh` runs all of it.

1. **Subject match** against the integration branch's log. Weakest — subjects get reworded.
2. **File existence.** Every file the commit touched exists in the integration branch, *or*
   was deliberately removed later. Distinguish the two with
   `git log <base> --diff-filter=D -1 -- <file>` — absent-because-deleted is not lost work.
3. **Symbol presence.** `git grep -w <identifier> <base>` for each identifier introduced.
   If absent, `git log -S<identifier> <base>` says whether it *ever* existed there.
4. **`git patch-id --stable`.** Decisive. Identical patch-ids mean the same change, whatever
   the SHAs say:
   ```bash
   git show <local-sha>  | git patch-id --stable
   git show <remote-sha> | git patch-id --stable   # same id => same change, safe
   ```

Step 3 flagging something that step 4 clears is the normal outcome for a rebased branch —
trust the patch-id.

## Restore

Deleted branches leave **no reflog entry**. The backup file is the only path back:

```bash
grep '^<branch-name> ' <backup-file>   # find the SHA
git branch <branch-name> <sha>         # recreate it
```

Objects survive until `git gc` prunes them — roughly 90 days by default, but a manual
`git gc --prune=now` ends that immediately. Restore before running gc.

## Windows

**MSYS path conversion.** Git Bash rewrites `rev:path` arguments:
`origin/development:.gitignore` becomes `origin\development;.gitignore`, and git reports the
object as missing. This silently produces *false* "file missing" results in the verification
ladder — the exact failure mode that would make you delete real work. Export
`MSYS_NO_PATHCONV=1` and prefer `git ls-tree <rev> -- <path>` over the colon form.

**MAX_PATH on `git worktree remove`.** The command fails with `Filename too long` but the
failure is **partial, not atomic**: git has already removed `.git/worktrees/<name>` and
released the branch, leaving the directory orphaned on disk. `git worktree list` then looks
correct while gigabytes remain. Verify with `ls`, never the error text. `purge-longpath-dir.ps1`
clears the remains — robocopy `/MIR` handles long paths that `Remove-Item` cannot. Robocopy's
exit code is a bitmask; anything under 8 is success.

## Why the gate must be a union

- **Ancestry alone misses squash merges.** On one 284-branch repo, ancestry found 17 of 90
  merged feature branches; the merged-PR head refs found the other 73.
- **Protected branches are not each other's ancestors.** In a `feature → development →
  release → master` flow, `release` and `master` contain hotfixes never in `development`.
  Gating on `development` alone misjudges them. Union all three.
- **`gh pr list` needs no `--repo`** inside a repo with a GitHub remote. If `gh` is missing or
  unauthenticated the gate degrades to ancestry-only, which is *conservative* (keeps too much)
  rather than dangerous — but say so out loud, since the user will wonder why so little went.

## Scope discipline

Remote branch deletion is out of scope by default. It is irreversible for teammates, not just
for you, and belongs in its own separately-approved pass. The same applies to pushing anything
to rescue a local-only branch: on a local-only cleanup, an unmerged branch is simply kept.
