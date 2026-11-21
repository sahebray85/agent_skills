---
name: release-pr
description: Raises or refreshes the draft release PR (development -> release) and writes its release notes. It writes "User Communication", a plain-language message for the people who use the system daily (boutique staff and owner) that is ready to paste into an email or WhatsApp, and audits the release's PRs for missing documentation. Works with repos that have the release-pr workflow and scripts (sor-service) and opens the PR itself where they don't exist yet (sharanaya-ui). Use when the user asks to raise, prepare or update a release PR, write release notes or a changelog for a release, list what's in the next release, or tell staff about a release.
---

# Release PR

Produces a **draft PR from `development` to `release`** whose body is the release notes. The body has four
marked sections, and each has one owner:

| Section (markers `<!-- release:NAME:start -->` / `<!-- release:NAME:end -->`) | Owner | Content |
|---|---|---|
| `user-communication` | **this skill** | the staff/owner message, plus the hidden `<!-- release:covers: … -->` list |
| `dev-refs` | CI (`release-pr.yml`) | every PR in `release..development` by type, notes from PR bodies |
| `docs-audit` | **this skill** | documentation gaps in the release's PRs |
| `checks` | CI (`release-pr.yml`) | advisory warnings; never blocks a merge |

On merge, CI (sor-service `ci_release.yml`) tags the merge commit, publishes User Communication + Developer
references as the GitHub Release, and commits the same text to `CHANGELOG.md` on `development`.

## Never

- Create or push `vX.Y.Z` / `vYYYY.MM.DD-NNN` tags. CI tags on merge, and a pre-existing tag fails the release run.
- Mark the PR ready, merge it, or push to `release` or `master`. The user does that.
- Edit the CI-owned sections (`dev-refs`, `checks`): every refresh rewrites them.
- Edit a version (`<revision>` in `pom.xml`, `version` in `package.json`).
- Open a docs PR without asking.

## Steps

### 1. Preflight

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
git fetch origin release development --tags
git log --oneline --first-parent origin/release..origin/development | head -50   # nothing listed = nothing to release
git log --no-merges --format='%h %s' origin/development..origin/release          # what release has that development lacks
```

The second command should list nothing except the legacy `Release version X [skip ci]` / `Bump the version for X`
commits. Anything else is a hotfix that never reached `development`: warn the user.

### 2. Find or open the draft PR

```bash
PR=$(gh pr list --repo "$REPO" --base release --head development --state open --json number --jq '.[0].number // empty')
```

If there's no PR, use the first of these that works:
1. **The repo has `.github/workflows/release-pr.yml` on `development`**: run
   `gh workflow run release-pr.yml --repo "$REPO" --ref development`, then poll `gh pr list` (as above) for up to
   about 3 minutes. Check `gh run list --repo "$REPO" --workflow release-pr.yml --limit 1` for the run.
2. **The run warned that it couldn't open the PR, but the checkout has `scripts/release/release-pr.sh`**: run
   `bash scripts/release/release-pr.sh refresh --create` from the repo root. It opens the PR with your own `gh`
   login. On Windows, use Git Bash.
3. **Neither exists** (e.g. sharanaya-ui today): create it yourself.
   - Body: the skeleton in [Section format](#section-format).
   - Version: the next minor after the highest exact `vX.Y.Z` tag:
     `git tag -l 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1`.
   - Command:
     ```bash
     gh pr create --repo "$REPO" --draft --base release --head development \
       --title "Release vX.Y.0 (DD-MM-YYYY)" --body-file body.md
     ```

     Never put `[skip ci]` in the title: it becomes the merge commit message.

### 3. Gather the release's PRs

```bash
git log --first-parent --format=%s origin/release..origin/development |
  sed -nE 's/^Merge pull request #([0-9]+) .*/\1/p; s/.*\(#([0-9]+)\)$/\1/p'
gh pr view <N> --repo "$REPO" --json number,title,body,labels,closingIssuesReferences,files
```

Read every PR's body and its linked issues (`gh issue view`) to learn what changed for the people using the system.
Read the diff (`gh pr diff <N>`) only when the body doesn't say.

### 4. Docs audit

For each `feat`/`fix` PR, check that the repo documents what it added:
- **Endpoints**: new `@GetMapping`/`@PostMapping`/`@PutMapping`/`@PatchMapping`/`@DeleteMapping` paths in the
  diff. `git grep -n "<path>" origin/development -- README.md docs/` must find them.
- **Configuration**: new keys or env vars in `application*.yml`, `.env*` or compose files, documented in
  README/docs.
- **User-visible errors**: new error codes or statuses a client or staff member sees.
- **UI repos**: new routes or screens, documented where that repo keeps its docs.

Write one bullet per gap, e.g. `- #1348: POST /v1/... isn't in README.md ("Products" section)`. With no gaps,
write `No documentation gaps found.` Then ask the user whether to open a docs PR to `development` for the gaps.

### 5. Write User Communication

**Audience: boutique staff and the owner**, the people who use the system every day. They aren't developers or
shoppers.
- Plain language. Say what changes for them and what to do differently. No PR numbers, class or endpoint names,
  or jargon (refactor, CI, heap, DTO).
- Group by area under short plain-text headings that end with a colon, e.g. "Store Pickup:", "LIVE sessions:",
  "Orders:", "Uploads:". Use plain `-` bullets with one level, no tables and no links, so it pastes cleanly into
  email and WhatsApp.
- Leave out internal-only changes: CI, refactors with no visible effect, docs, infrastructure flags. If nothing
  staff can see changed, say so in one line.
- Be accurate: claim only what the PRs say shipped. If you can't tell whether a change is visible to staff, leave
  it out and mention it in your report to the user.
- Start with a one-line greeting. End with "Reply here if anything looks wrong."
- Add `<!-- release:covers: 1311,1312,… -->` listing **every** PR you read, including the ones you left out. CI
  uses it to warn about PRs merged after you wrote the message.

### 6. Write your two sections into the PR body

```bash
gh pr view "$PR" --repo "$REPO" --json body --jq .body > body.md   # re-read right before editing
```

- **Replace only** the `user-communication` and `docs-audit` sections. Keep everything else byte-for-byte.
- **Missing markers**: put `user-communication` at the top, and `docs-audit` right after `<!-- release:dev-refs:end -->`.
- **If the repo has `scripts/release/release-pr.sh`**, use its tested helpers from the repo root in Git Bash.
  Sourcing it defines functions without running anything:
  ```bash
  ( source scripts/release/release-pr.sh
    replace_section user-communication body.md uc.md > b2.md
    replace_section docs-audit b2.md docs.md > new.md )
  gh pr edit "$PR" --repo "$REPO" --body-file new.md
  ```
  `uc.md` and `docs.md` hold the complete sections, start and end markers included.

### 7. Confirm

- Wait for the `release-pr.yml` run that your edit triggered (`gh run list --repo "$REPO" --workflow
  release-pr.yml --limit 1`) to finish.
- Re-read the body. Your two sections must be intact, and the `checks` section must no longer say "placeholder".
- If a concurrent refresh overwrote your sections, redo step 6 once and tell the user.

### 8. Report to the user

- The PR link, and the predicted version and tags (`bash scripts/release/version.sh release minor` where it exists).
- The User Communication text, so they can copy it.
- The docs gaps, and whether a docs PR was opened.
- The warnings in the `checks` section.
- Next steps:
  - optional, sor-service: a dry run of the GitHub Release body and CHANGELOG entry,
    `gh workflow run ci_release.yml --ref development -f pr=<N>`;
  - `gh pr ready <N>` (starts CI);
  - merge with a **merge commit**, not a squash.

Re-running the skill later, e.g. after the checks report PRs merged after the message was written, is safe: it
rewrites only its own two sections.

## Section format

Skeleton for a new PR (step 2.3); CI fills `dev-refs` and `checks` where the workflow exists:

```markdown
<!-- release:user-communication:start -->
## User Communication

Hi team,

This update brings:

Store Pickup:
- You can now create an order for pickup at the store, and see today's pickups in one list.

LIVE sessions:
- Start a Facebook or YouTube LIVE, scan sarees during it, and close or reopen it.

Reply here if anything looks wrong.
<!-- release:covers: 1311,1312,1315 -->
<!-- release:user-communication:end -->

<!-- release:dev-refs:start -->
## Developer references
- #1315 feat(orders): … (one line per PR, grouped by type)
<!-- release:dev-refs:end -->

<!-- release:docs-audit:start -->
## Docs audit
- No documentation gaps found.
<!-- release:docs-audit:end -->

<!-- release:checks:start -->
<!-- release:checks:end -->
```

## Repo notes

- **sor-service**: fully automated. `release-pr.yml` and `scripts/release/` handle the PR; `ci_release.yml`
  publishes the notes. Versions come from git tags (`scripts/release/version.sh`) and are never committed. See
  `docs/BRANCHING_STRATEGY.md#releasing`.
- **sharanaya-ui**: until its release-pr workflow lands, this skill opens the PR itself (step 2.3) and writes
  `dev-refs` by hand in the skeleton's format. Its `package.json` version is still committed there; don't touch it.
