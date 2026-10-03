# GitHub billing rules and gotchas

Verified against the live API, real bills and GitHub docs. Re-check a rule against current docs before acting on it in
a new situation, because GitHub changes billing and prices often.

## What can and can't be capped

| Kind | Examples (product / SKU) | Budget effect |
|---|---|---|
| Metered | Actions minutes and storage, Packages storage, Git LFS, Codespaces, Models | A hard stop blocks further use |
| AI credits | Copilot, Copilot cloud agent, Spark, Code Quality AI credits | Bundled AI-credits budget (docs don't list Code Quality: use a SKU-level budget to be sure) |
| Licences | Enterprise Cloud seats, Team seats, Code Quality licences (per active committer), Copilot seats | Alerts only, never stopped |

**Budget types** when creating one:
- **Product-level** sums every SKU of one product.
- **SKU-level** covers one line item only.
- **Bundled AI credits** is one pool across AI-credit SKUs, and is the only type with per-user budgets.

The API names are `ProductPricing` and `BundlePricing`. What happens when two budgets overlap is undocumented.

**Scope matters:** an org-scope budget did not stop usage billed through the enterprise. It showed `consumed=$0`
while the org was being charged. Set the cap at the scope that pays the bill.

**A budget above $0 needs a payment method** on the account that pays. Without one, usage is blocked once the
allowance is used up. Whether a hard stop also stops the charge for bytes already stored is undocumented.

## Plans

Allowances are **per account, not per seat**: adding members raises the cost and nothing else.

| | Free | Team | Enterprise Cloud |
|---|---|---|---|
| Price per user per month (check github.com/pricing) | $0 | $4 | $21 |
| Actions minutes a month, private repos | 2,000 | 3,000 | 50,000 |
| Storage, shared by Packages and Actions artifacts | 0.5 GB | 2 GB | 50 GB |
| Org secrets, rulesets, drafts, CODEOWNERS in private repos | no | yes | yes |
| SAML single sign-on, IP allow list, audit-log streaming | no | no | yes |

- **Storage is metered in GB-hours.** A month's allowance is GB × 744 hours, so 0.5 GB is 372 GB-hours. Usage past
  that is billed at about $0.25 per GB-month; Actions minutes on Linux cost $0.006 each. Both rates come from a bill:
  gross amount ÷ quantity.
- **Break-even between two plans:** (seat-cost difference ÷ $0.006) + the cheaper plan's minutes. Below that many
  minutes a month the cheaper plan wins.
- **Org plan:** `gh api /orgs/ORG --jq .plan.name`.

**What Free switches off in private repos:**
- **Org-level secrets and variables** aren't readable. Repo-level secrets still work, and they are kept, not
  deleted, across a plan change. To find what breaks:
  - `gh api orgs/ORG/actions/secrets --jq '.secrets[] | [.name, .visibility] | @tsv'` lists the org secrets;
  - `gh search code "secrets.NAME" --owner ORG` finds the workflows that use one;
  - `gh api repos/ORG/REPO/actions/secrets --jq '[.secrets[].name]'` shows which repos already have their own copy.
- **Rulesets and branch protection** aren't enforced. `gh api repos/ORG/REPO/rulesets` returns 403 "Upgrade to GitHub
  Pro", so a required status check no longer gates a merge.
- **Draft PRs** can't be created; existing ones stay drafts. CODEOWNERS and required reviewers are off too.
- **Container registry (ghcr)** is currently free on every plan, so `docker push` doesn't use the storage allowance.
  GitHub's docs promise a month's notice before that changes.
- **Code Quality** has no free tier on private repos. It analyses only the default branch and PRs into it. To disable
  it: `gh api -X PATCH repos/OWNER/REPO/code-quality/setup -f state=not-configured`. Its licence kept charging daily
  for at least two days after it was disabled in every repo.

## Billing lock (unpaid or failed enterprise invoice)

- Audit log: `gh api "/enterprises/ENT/audit-log?phrase=action:billing.lock"`. The `phrase=action:` filter needs the
  full action name.
- **Every** Actions run fails at once: `conclusion=startup_failure`, empty `name`, `path=BuildFailed`. A broken
  workflow file shows its own path instead.
- GitHub Packages refuses downloads outside Actions with "Billing not allowed, data transfer out quota has been
  exceeded", so local builds can't resolve another repo's `client-api`.
- Deleting artifacts and package versions still works while locked.
- CI ran again after the invoice was settled and the org had left the locked enterprise. Which of the two lifted the
  lock wasn't isolated.

## Uploads refused with HTTP 402

- `maven-deploy-plugin` reports `status code: 402, reason phrase: Payment Required`.
- Cause: the month's storage allowance in GB-hours is used up and the Packages budget is a $0 hard stop.
- The bytes stored now can be tiny while this happens, because deleted versions and earlier days already used the
  allowance. `report.py` shows both figures.
- Fix: a payment method plus a small Packages budget, or stop publishing, or wait for the month to reset.

## Enterprise

- **Seats:** `gh api enterprises/ENT/consumed-licenses` lists who holds one. Outside collaborators on private repos
  use a seat too.
- **Remove an org:** Enterprise → Organizations → remove. The org drops to Free and keeps its repos, packages and
  secrets. The audit log records `business.remove_organization`.
- **An enterprise with no organizations still bills** a seat and any licence such as Code Quality, every day, until
  it is deleted.
- **Delete it** (no API; the owner does this in the browser):
  1. Save invoices and receipts first, because the billing history can go with it.
  2. Enterprise → People: remove members who belong to no organization. List them with
     `gh api graphql -f query='{ enterprise(slug:"ENT") { organizations { totalCount } members(first:20) { nodes { ... on EnterpriseUserAccount { login } } } } }'`.
  3. Enterprise → Settings → General → Danger Zone → Delete this enterprise. Any outstanding balance is charged then.
  4. An invoiced or trial enterprise can't be deleted this way; GitHub Sales closes it.
- **Confirm:** `gh api enterprises/ENT` returns 404.

## Usage API

- `/organizations/ORG/settings/billing/usage?year=&month=&day=` and `/enterprises/ENT/...`. Line items carry `date`,
  `product`, `sku`, `quantity`, `unitType`, `grossAmount`, `netAmount` and `repositoryName`.
- Daily is the finest view; `hour=` returns HTTP 400 (deprecated). Data lags, so the current day is always partial.
- GB-hours ÷ 24 = average GB stored that day.
- After an org leaves an enterprise, its usage appears under the org endpoint, and the enterprise endpoint keeps the
  earlier days.

## Packages

- Real bytes come only from GraphQL `PackageFile.size`. REST gives version counts, not sizes.
- Delete a version: `DELETE /orgs/ORG/packages/TYPE/NAME/versions/ID`. Delete a package: `DELETE /orgs/ORG/packages/TYPE/NAME`.
- `prune.py` never plans the deletion of every version of a package; deleting a whole package is an explicit `--drop`.
- Deleted items are restorable for 30 days. There's no purge API, so they drop out on their own.
- **Deleted versions are still billed:** a repo with no live package kept accruing storage the day after its packages
  were deleted. Expect that to last until they purge.
- REST package lists hide deleted packages.
- Spring Boot jars (~140 MB a version) dominate storage if `mvn deploy` publishes them. Skip publishing any module that
  nobody pulls from the registry.

## Artifacts

- `GET /repos/ORG/REPO/actions/artifacts` (skip `expired: true`). `DELETE .../actions/artifacts/ID` is permanent.
- Org retention: `GET|PUT /orgs/ORG/actions/permissions/artifact-and-log-retention`. The default and maximum are 90
  days, and the setting also governs run logs.
- `gh search code` covers private repos but only default branches. Its JSON has `repository.nameWithOwner`.
