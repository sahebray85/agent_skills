---
name: sharanaya-ui
description: Orchestrates the full Sharanaya UI feature development lifecycle in one command. Chains: context load → grill requirements → plan phases → parallel subagent execution → verify (tsc + lint + tests + screenshot) → squash commit → PR to development. Use when starting any new feature, fix, or improvement in this project.
---

# Sharanaya UI Feature Workflow

End-to-end orchestration for building features in this project. Run each phase in order. Do not skip phases.

---

## Phase 0 — Context Load

Before anything else:

1. Read `docs/PROJECT_OVERVIEW.md` (architecture, patterns, API client conventions)
2. If the feature touches orders, workflow, or dispute status: also read `docs/ORDER_PAGE.md`
3. Rebase the current branch from `development`:
   ```
   git fetch origin && git rebase origin/development
   ```
4. Confirm the working branch is **not** `development`, `release`, or `master`

---

## Phase 1 — Grill Requirements

Invoke the grill-me skill to stress-test the requirements before writing a single line of code:

```
/grill-me
```

Drive toward answers for:
- What API endpoints are called? What shape is the response?
- What are the state conditions and permission rules? (e.g. "only show if status = X")
- What are the conditional rendering rules?
- What edge cases exist? (empty state, loading state, error state)
- Does this touch the order workflow? Which substatuses and color groups?

Do not proceed to Phase 2 until all of these are answered.

---

## Phase 2 — Create Plan

Convert the grilled spec into a phased implementation plan:

```
/prd-to-plan
```

The plan must:
- Live in `plans/` as a `.md` file
- Have multiple phases, each with acceptance criteria
- Name the exact files to create or modify
- Call out reused patterns (existing API clients, color maps, cloudfront URL helper)

Key patterns to reference in the plan:
- API clients: `createSorClient`, `createBusinessOrchestratorClient` via `useMemo` + `useAppAuth()`
- CSRF: auto-injected by axios interceptor — do not add manually
- Image URLs: `cloudFrontBaseUrl + s3Path + fileName` (see `src/images/cloudfront.ts`)
- Order substatus colors: `SUBSTATUS_BADGE_COLORS` in `src/orders/statusColors.ts`
- Auth guard: `withCredentials: true` already set on all clients

---

## Phase 3 — Execute

Run the plan with parallel subagents:

```
/superpowers:subagent-driven-development
```

Each subagent must:
- Follow the API client pattern from Phase 2 (never create raw axios instances)
- Run `npx tsc --noEmit` after every `.ts`/`.tsx` change — fix errors immediately before continuing
- Not add features beyond what the acceptance criteria require

---

## Phase 4 — Verify

### 4a. Visual verification
```
/run
```
- Start the dev server and navigate to the changed feature
- Capture a screenshot as proof (save to `screenshots/`)
- Confirm the golden path works + check at least one edge case (empty/error state)

### 4b. Quality gates (run in this order, fix before proceeding)
```bash
npx tsc --noEmit       # TypeScript — must be zero errors
npm run lint           # ESLint — fix all errors
npm run test:coverage  # Vitest — tests must pass with coverage
```

Do not proceed to Phase 5 if any gate fails.

---

## Phase 5 — Ship

1. Squash all branch commits into one:
   ```
   /commit-commands:commit
   ```
   Commit message format: `feat(scope): description` (Conventional Commits)

2. Raise PR:
   - **Target branch: `development`** (never `release` or `master`)
   - Include the screenshot from Phase 4a in the PR description
   - PR body must reference the plan file from Phase 2

3. Invoke:
   ```
   /superpowers:finishing-a-development-branch
   ```

---

## Quick Reference: Project Constants

| Concern | Location |
|---------|---------|
| Service URLs | `src/config.ts` |
| API clients | `src/api/http.ts` |
| Auth hook | `src/auth/appAuth.tsx` → `useAppAuth()` |
| CloudFront URLs | `src/images/cloudfront.ts` |
| Order substatus colors | `src/orders/statusColors.ts` |
| SOR service (local) | `http://localhost:17280` |
| Swagger docs | `http://localhost:17280/swagger-ui/index.html` |
