---
name: sor-skill
description: >
  Workflow automation for the sor-service Spring Boot monorepo (sharanaya-boutique/sor-service).
  Use when working on sor-service tasks: rebasing onto development, compiling Java, committing,
  raising PRs to development, or preserving session context across Claude context windows.
  Triggers: "sor-service", "rebase development", "compile", "raise PR", "implement issue #NNN".
---

# sor-skill

## Constants (never re-derive these)

```bash
REPO="D:/Projects/SharanayaBoutique/repositories/sor-service"
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

## Quick reference

| Task | Command shortcut |
|------|-----------------|
| Get project version | `$MVN help:evaluate -Dexpression=project.version -q -DforceStdout` |
| Compile client-api only | `MAVEN_OPTS="..." $MVN compile -pl client-api -DskipTests "-Drevision=$VER"` |
| Read surefire failures | `find . -path "*/surefire-reports/*.txt" | xargs grep -l "FAILED" | xargs head -80` |
| Current branch ahead count | `git rev-list --count HEAD ^origin/development` |
