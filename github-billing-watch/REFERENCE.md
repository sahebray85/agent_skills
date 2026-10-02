# GitHub billing rules and gotchas

Verified against the live API and GitHub docs. Re-check a rule against current docs before acting on it in a new
situation, because GitHub changes billing often.

## What can and can't be capped

| Kind | Examples (product / SKU) | Budget effect |
|---|---|---|
| Metered | Actions minutes and storage, Packages storage, Git LFS, Codespaces, Models | A hard stop blocks further use |
| AI credits | Copilot, Copilot cloud agent, Spark, Code Quality AI credits | Bundled AI-credits budget (docs don't list Code Quality: use a SKU-level budget to be sure) |
| Licences | Enterprise Cloud seats, Code Quality licences (per active committer), Copilot seats | Alerts only, never stopped |

**Budget types** when creating one:
- **Product-level** sums every SKU of one product.
- **SKU-level** covers one line item only.
- **Bundled AI credits** is one pool across AI-credit SKUs, and is the only type with per-user budgets.

The API names are `ProductPricing` and `BundlePricing`. What happens when two budgets overlap is undocumented.

**Scope matters:** an org-scope budget did not stop usage billed through the enterprise. It showed `consumed=$0`
while the org was being charged. Set the cap at the scope that pays the bill.

## Free plan

- **Actions:** 2,000 minutes a month on private repos.
- **Storage:** 0.5 GB, shared between Packages and Actions artifacts.
- **Container registry (ghcr):** free, so `docker push` to ghcr doesn't eat the Packages allowance.
- **Code Quality:** no free tier on private repos. It analyses only the default branch and PRs into it, and can't be
  scoped to a release branch. To disable it: `gh api -X PATCH repos/OWNER/REPO/code-quality/setup -f state=not-configured`.
- **Org plan:** `gh api /orgs/ORG --jq .plan.name`.

## Billing lock (unpaid or failed enterprise invoice)

- Audit log: `gh api "/enterprises/ENT/audit-log?phrase=action:billing.lock"`. The `phrase=action:` filter needs the
  full action name.
- **Every** Actions run fails at once: `conclusion=startup_failure`, empty `name`, `path=BuildFailed`. A broken
  workflow file shows its own path instead.
- GitHub Packages refuses downloads outside Actions with "Billing not allowed, data transfer out quota has been
  exceeded", so local builds can't resolve another repo's `client-api`.
- Deleting artifacts and package versions still works while locked.

## Usage API

- `/organizations/ORG/settings/billing/usage?year=&month=&day=` and `/enterprises/ENT/...`. Line items carry
  `product`, `sku`, `quantity`, `unitType`, `grossAmount`, `netAmount` and `repositoryName`.
- Daily is the finest view; `hour=` returns HTTP 400 (deprecated). Data lags about one day.
- GB-hours ÷ 24 = average GB stored that day.

## Packages

- Real bytes come only from GraphQL `PackageFile.size`. REST gives version counts, not sizes.
- Delete a version: `DELETE /orgs/ORG/packages/TYPE/NAME/versions/ID`. Delete a package: `DELETE /orgs/ORG/packages/TYPE/NAME`.
- `prune.py` never plans the deletion of every version of a package; deleting a whole package is an explicit `--drop`.
- Deleted items are restorable for 30 days. There's no purge API, so they drop out on their own.
- REST package lists hide deleted packages.
- Spring Boot jars (~140 MB a version) dominate storage if `mvn deploy` publishes them. Skip publishing any module that
  nobody pulls from the registry.

## Artifacts

- `GET /repos/ORG/REPO/actions/artifacts` (skip `expired: true`). `DELETE .../actions/artifacts/ID` is permanent.
- Org retention: `GET|PUT /orgs/ORG/actions/permissions/artifact-and-log-retention`. The default and maximum are 90
  days, and the setting also governs run logs.
- `gh search code` covers private repos but only default branches. Its JSON has `repository.nameWithOwner`.
