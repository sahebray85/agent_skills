---
name: sor-skill
description: >
  Workflow automation for the sor-service Spring Boot monorepo (sharanaya-boutique/sor-service).
  Use when working on sor-service tasks: rebasing onto development, compiling Java, committing,
  raising PRs to development, preserving session context across Claude context windows, or
  recovering a stuck release branch (409 Conflict re-publishing a version, dead/unreleased
  version blocking release CI).
  Triggers: "sor-service", "rebase development", "compile", "raise PR", "implement issue #NNN",
  "release CI failed", "409 conflict release", "release stuck".
---

# sor-skill

## Constants (never re-derive these)

```bash
REPO="$`{pwd}`"
MVN="/c/Users/saheb/.m2/wrapper/dists/apache-maven-3.9.12-bin/5nmfsn99br87k5d4ajlekdq10k/apache-maven-3.9.12/bin/mvn"
MAVEN_OPTS="-Xmx768m -XX:+UseSerialGC -XX:MaxMetaspaceSize=256m"
BASE_BRANCH="development"
```

---

## Workflow 1: Start of session — rebase

```bash
cd "$REPO"
git fetch origin development
git rebase origin/development
git status
git log --oneline -5
```

Report: current branch, commits ahead of development, any conflicts.

---

## Workflow 2: Compile / Test

```bash
cd "$REPO"
VER=$($MVN help:evaluate -Dexpression=project.version -q -DforceStdout)

# Compile service (includes client-api via -am)
MAVEN_OPTS="$MAVEN_OPTS" $MVN compile -pl service -am -DskipTests "-Drevision=$VER" \
  2>&1 | tee build.log | tail -20
```

**Parse result — execute these checks after every build:**

```bash
if grep -q "BUILD SUCCESS" build.log; then
  echo "COMPILE OK"
else
  # OOM? Retry client-api alone
  if grep -q "insufficient memory\|malloc failed" build.log; then
    echo "OOM detected — retrying client-api alone"
    MAVEN_OPTS="$MAVEN_OPTS" $MVN compile -pl client-api -DskipTests "-Drevision=$VER" 2>&1 | tail -10
  fi

  # Test failures? Extract surefire detail
  find . -path "*/surefire-reports/*.txt" -newer build.log 2>/dev/null \
    | xargs grep -l "FAILED\|ERROR" 2>/dev/null \
    | head -5 \
    | xargs head -80 2>/dev/null \
    | tee .claude/last-build-failure.txt
  echo "COMPILE FAILED — failure detail in .claude/last-build-failure.txt"
fi
```

Run tests (when needed):

```bash
MAVEN_OPTS="$MAVEN_OPTS" $MVN test -pl service -Dtest=<TestClass> "-Drevision=$VER" \
  2>&1 | tee build.log | tail -20
```

---

## Workflow 3: Commit + PR

Single commit, linked to issue:

```bash
cd "$REPO"
# Stage only tracked/intended files — never use git add -A
git add <specific files>
git status  # verify before committing

git commit -m "$(cat <<'EOF'
feat(#NNN): <short description>

<body: what changed and why>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"

git push origin $(git branch --show-current)

gh pr create \
  --title "feat(#NNN): <short description>" \
  --base development \
  --body "$(cat <<'EOF'
## Summary

- Bullet 1
- Bullet 2

## Test plan

- [ ] ...

Closes #NNN

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Workflow 4: Context snapshot (run when context window is filling)

```bash
cd "$REPO"
cat > .claude/session-state.md <<EOF
# Session State — $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Branch
$(git branch --show-current) — $(git log --oneline -1)

## Issue
#NNN — <issue title>

## Files modified this session
$(git diff --name-only HEAD~$(git rev-list --count HEAD ^origin/development) 2>/dev/null || git diff --name-only)

## Last build
$(tail -3 build.log 2>/dev/null || echo "No build log")

## Key decisions
- <Claude summarises decisions made in this session>
EOF
cat .claude/session-state.md
```

Claude must fill in `#NNN`, issue title, and Key decisions from conversation context.

---

## Workflow 5: Full feature workflow

- [ ] **Rebase** — run Workflow 1
- [ ] **Implement** — make code changes (read files before editing)
- [ ] **Compile** — run Workflow 2; fix errors before proceeding
- [ ] **Commit + PR** — run Workflow 3
- [ ] **Snapshot** — run Workflow 4

---

## Workflow 6: Release CI recovery (stuck/dead version on `release`)

**Symptom:** a push to `release` fails at `Build and Publish Release Artifact` with
`mvn deploy` → `409 Conflict` re-publishing `sor-service:pom:<version>` (or any of
`client-api`/`database`/`service`). GitHub Packages rejects re-publishing existing
coordinates — Maven versions are immutable there.

**Root cause pattern:** `ci_release.yml`'s `advance-version-release` job only bumps the
`<revision>` when it's `-SNAPSHOT`; if it's already a plain version (non-SNAPSHOT) it
*reuses* it, on the assumption a prior run bumped the pom but died before publishing
anything. That assumption breaks when a prior run actually **finished publishing**
(Maven + Docker) and only failed a *later* gate — almost always
`trivy-scan-sor-service-release` finding real CVEs. `finalize-release` never runs (needs
Trivy to pass), so there's no git tag/GitHub Release, but the artifacts are permanently
burned. Every subsequent push to `release` reuses the same dead version and 409s forever
until it's corrected.

**Related bug to check for in the same pipeline:** `docker-service-release` may push the
mutable `:release` Docker tag *before* Trivy scans it — meaning a failed scan still leaves
`:release` pointing at a vulnerable image. If so, fix the ordering (scan a versioned-only
tag first, retag `:release` from inside `finalize-release` after the scan gate passes,
e.g. via `docker buildx imagetools create`) as part of the same recovery.

**Diagnosis:**

```bash
gh run list --repo sharanaya-boutique/sor-service --workflow=ci_release.yml --limit 5 \
  --json databaseId,displayTitle,status,conclusion,createdAt,event
gh run view <failed-run-id> --repo sharanaya-boutique/sor-service   # find which job failed
gh run view --job <job-id> --repo sharanaya-boutique/sor-service --log-failed | tail -100

# Find the PRIOR run that actually published the now-burned version — check its
# publish-artifact-release / docker-service-release job conclusions, and what gate
# (usually trivy-scan-sor-service-release) it died on:
gh run view <prior-run-id> --repo sharanaya-boutique/sor-service

# Confirm the dead version is really published (immutable) before assuming a collision:
gh api "orgs/sharanaya-boutique/packages/maven/com.sharanaya.sorservice.sor-service/versions?per_page=5" \
  --jq '.[] | "\(.id) \(.name) \(.created_at)"'

# Confirm development vs release <revision> divergence:
MSYS_NO_PATHCONV=1 git show origin/development:pom.xml | grep -m1 "<revision>"
MSYS_NO_PATHCONV=1 git show origin/release:pom.xml | grep -m1 "<revision>"
```

**Fix (two PRs, standard branch flow — do not push directly to `release`, it's ruleset-protected):**

1. **PR to `development`** (normal flow): fix whatever failed the gate (e.g. bump the CVE'd
   dependencies — check whether each is Boot-BOM-managed or independently pinned via this
   repo's own `<properties>`/`<dependencyManagement>` in root `pom.xml` before assuming a
   parent bump alone fixes it), and bump `<revision>` past the dead `MAJOR.MINOR` — the
   release bump formula only reads `MAJOR.MINOR` (patch is discarded), so any
   `<dead-minor>.x-SNAPSHOT` will keep colliding. E.g. dead version `0.20.0` → bump
   development to `0.20.1-SNAPSHOT` (skips into the next-minor line) so the next release
   cut computes `0.21.0`, unused.
2. **PR directly from `development` → `release`** (this repo's existing promotion pattern,
   e.g. past PRs like #777/#780 — not a rule violation, it's the standard second leg):
   ```bash
   git fetch origin development release
   git checkout -b promote-development-to-release origin/release
   git merge origin/development --no-edit
   # Expect exactly one conflict, on pom.xml's <revision> line — release's stale dead
   # version vs development's corrected one. Take development's value:
   ```
   Resolve by editing out the `<<<<<<</=======/>>>>>>>` markers, keeping development's
   `<revision>`, `git add pom.xml`, `git commit --no-edit`, push, `gh pr create --base release`.
   Everything else (dependency bumps, workflow fixes) merges cleanly since `release` has no
   independent changes beyond the dead version-bump commit.
3. Merging PR 2 triggers `ci_release.yml` fresh — watch it end-to-end
   (`gh run list --workflow=ci_release.yml --limit 1`, then `gh run view <id>` /
   `gh pr checks <pr> --watch`). Full run ≈ 5-7 min (advance ~20-30s, publish ~2min,
   docker build ~2-3min, trivy ~30-60s, finalize ~30s).

**Note:** merging into `development` may be auto-approved by the harness; merging into
`release` has been blocked by the auto-mode classifier even when explicitly instructed to
auto-merge — expect to hand that merge back to the user.

**Optional cleanup (destructive, only after the new release finalizes successfully — confirm
first, GitHub Packages deletions are irreversible):**

```bash
# 4 Maven package versions for the dead release:
for pkg in sor-service client-api database service; do
  gh api -X DELETE "orgs/sharanaya-boutique/packages/maven/com.sharanaya.sorservice.$pkg/versions/<id>"
done
# Container image version carrying the dead version AND (if scanned-before-tagged) :release:
gh api -X DELETE "orgs/sharanaya-boutique/packages/container/sor-service/versions/<id>"
```

Get version IDs via `gh api ".../versions?per_page=5" --jq '.[] | select(.name=="<dead-version>") | .id'`
(Maven) or `--jq '.[] | select(.metadata.container.tags[]? == "<dead-version>") | .id'` (container).
Deleting the container version removes *every* tag it carries — if that includes `:release`,
the tag disappears until the next successful build recreates it (safer than leaving it
pointing at a vulnerable image, given the tag-ordering bug above).

---

## Quick reference

| Task | Command shortcut |
|------|-----------------|
| Get project version | `$MVN help:evaluate -Dexpression=project.version -q -DforceStdout` |
| Compile client-api only | `MAVEN_OPTS="..." $MVN compile -pl client-api -DskipTests "-Drevision=$VER"` |
| Read surefire failures | `find . -path "*/surefire-reports/*.txt" | xargs grep -l "FAILED" | xargs head -80` |
| Current branch ahead count | `git rev-list --count HEAD ^origin/development` |
| Release deploy 409 Conflict | See Workflow 6 — dead version reuse, not a transient failure |
