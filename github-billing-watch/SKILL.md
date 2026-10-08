---
name: github-billing-watch
description: Reports GitHub org and enterprise billing (month-to-date cost by product and SKU, charges still accruing, budgets and hard stops, plan allowance used in Actions minutes and storage GB-hours, real vs billed storage, billing-lock signals), safely prunes GitHub Actions artifacts and GitHub Packages versions through a reviewed dry-run plan, and walks through changing plan (Free, Team, Enterprise) and leaving or deleting an enterprise. Use when the user asks about GitHub cost, bill, invoice, seats, budgets, spending limits, storage or quota, "402 Payment Required" on mvn deploy or a package publish, "data transfer out quota has been exceeded", nameless startup_failure runs, switching GitHub plan, or wants to clean up, prune or delete old artifacts or package versions.
---

# GitHub billing watch

Scripts in `scripts/` next to this file, driven by an authenticated `gh` (org admin + billing read). Run them as
`python "<this skill's dir>/scripts/<script>.py"`, with forward slashes or a quoted path. Default: `--org
sharanaya-boutique`. Pass `--enterprise SLUG` only when an enterprise bills the org.

## Monitor (read-only, any time)

```
python scripts/report.py [--month YYYY-MM] [--enterprise SLUG]
```

Read it in this order and report figures, not guesses:
1. **Billing-lock signals.** A repo whose latest run is a nameless `startup_failure` (path `BuildFailed`) is
   billing-locked, not broken YAML. "Stale" means a normal run elsewhere is newer, so the lock has lifted.
2. **Storage.** REAL covers Maven-style packages and artifacts only. **Container images (GHCR) are listed separately by
   version count, because GitHub exposes no sizes for them, yet they bill as Packages storage.** If the billing page
   shows more than REAL, containers are the usual cause. REAL is the bytes stored now. BILLED is yesterday's average from the usage API, which lags a day.
   A repo billed with no live package means deleted versions are still billing.
3. **Usage.** Sorted by net cost. A `charged:` line shows how many days a SKU charged and the latest day, which is how
   you see a licence still charging after it was switched off.
4. **Allowance.** Minutes and storage GB-hours used this month against the plan's allowance. This, not the bytes
   stored now, decides when CI stops or uploads are refused.
5. **Budgets.** An org budget doesn't stop usage billed through an enterprise; check the enterprise budgets too.

Explain what a figure means before recommending anything; see [REFERENCE.md](REFERENCE.md) for the billing rules.

## Uploads refused: HTTP 402 Payment Required

`mvn deploy` (or any package publish) fails with `status code: 402`, and jobs that need it are skipped.
- [ ] 1. Run `report.py`. Storage allowance at or past 100% with a $0 hard-stop Packages budget is the cause.
- [ ] 2. Offer the fixes; the user chooses:
      - add a payment method and raise the Packages budget a little (the user's billing page). Estimate the cost
        from the billed GB: GB × days left × the storage rate in REFERENCE.md;
      - or stop publishing: `maven.deploy.skip` on modules nobody downloads, or skip the publish step;
      - or wait for the month to reset.
- [ ] 3. Verify: re-run the failed workflow and confirm the publish step passes.

A cleanup alone doesn't fix it: deleted versions keep billing until they purge.

## Clean up (destructive: follow every step)

- [ ] 1. Run `report.py`. Know what fills the space, and whether a cleanup is needed at all.
- [ ] 2. Agree the keep rule with the user. Defaults: **artifacts** are kept if younger than 10 days OR among the
      newest 10 per repo; **packages** keep the newest 10 `-SNAPSHOT` + 10 release versions each; **containers**
      keep `latest` + the newest 10 tagged versions per image + every tag a deploy repo pins.
- [ ] 3. Find pinned versions: another repo's pom that depends on a fixed (non-SNAPSHOT) version of an org package.
      `gh search code "com.sharanaya" --owner sharanaya-boutique --filename pom.xml`, read the hits, and pass each
      as `--pin PACKAGE_PREFIX:VERSION` (e.g. `--pin com.sharanaya.securityservice.:0.4.0`).
- [ ] 4. Dry run. It only reads, prints a per-repo or per-package table, and writes a plan JSON to the temp dir:
      ```
      python scripts/prune.py artifacts --keep-days 10 --keep-newest 10
      python scripts/prune.py packages --keep-snapshots 10 --keep-releases 10 --pin ... [--drop WHOLE_PACKAGE]
      ```
      `--drop` is for packages nobody consumes: a deprecated repo, or a boot jar every Dockerfile builds from source.
      **Containers** (usually the biggest part; `packages` only handles Maven):
      first find what is deployed: `gh search code "ghcr.io/sharanaya-boutique" --owner sharanaya-boutique`, then read the
      deploy repo's compose files and `.env` version vars (e.g. `infrastructure_pipeline/production/.env.production.example`).
      Pass each deployed tag as `--protect IMAGE:TAG`:
      ```
      python scripts/prune.py containers --keep-newest 10 --protect sor-service:0.21.0 --protect sharanaya-ui:0.4.0-prod [--drop IMAGE]
      ```
      It plans **tagged** versions only. Untagged ones are usually child manifests of a kept multi-arch tag, so deleting them
      can break it; leave them. Sizes are not available, so the table shows counts. Images with no reference anywhere
      (stale, odd names) are candidates for `--drop`, but confirm with the user first: a base image such as
      `libpostal-base` is a build input, not a deployed tag.
- [ ] 5. Show the user the table, every `WARN` line, and the undo story: **artifacts are gone for good**; packages
      are restorable for 30 days unless that version is published again. Wait for an explicit yes.
- [ ] 6. `python scripts/prune.py apply "<plan.json>"` deletes exactly the reviewed targets: paced, 404 counted as
      done, aborts if the first deletes all fail. For more than ~200 targets run it in the background.
- [ ] 7. Verify: re-run the same dry run (expect 0 deletes) and `report.py` (REAL storage dropped, container version
      count dropped). For containers also confirm a kept image still pulls (`docker manifest inspect
      ghcr.io/ORG/IMAGE:TAG`). BILLED storage can stay high for up to 30 days, because deleted package versions keep
      billing until they purge.

Never delete without a dry run the user saw. Never delete a version a `--pin` protects. Never `--drop` a package
another repo resolves from GitHub Packages.

## Change plan, or leave or delete an enterprise

Billing-page steps are the user's. Your part is the checks before and after. Details and commands are in
[REFERENCE.md](REFERENCE.md) under "Plans" and "Enterprise".
- [ ] 1. Run `report.py`. Compare this month's minutes and storage with the target plan's allowance. Allowances are
      per account, so more seats raise the cost and not the allowance.
- [ ] 2. List what the target plan switches off in private repos: org secrets (find repos with no repo-level copy),
      rulesets and branch protection, draft PRs.
- [ ] 3. User: settle any open invoice, then remove the org from the enterprise. It drops to Free.
- [ ] 4. User: upgrade straight afterwards if moving to Team, so the Free gaps from step 2 stay short.
- [ ] 5. User: delete the emptied enterprise. It keeps billing a seat and licences until it is deleted.
- [ ] 6. Verify: the plan name, the enterprise returns 404, a CI run passes in a repo that relies on org secrets,
      a publish step passes, and the next day's `report.py` shows no new licence charge.

## Stop regrowth (offer; don't do it unasked)

- `retention-days: N` on large recurring `upload-artifact` steps, such as coverage reports. This is the narrowest fix.
- Org-wide: `gh api -X PUT /orgs/ORG/actions/permissions/artifact-and-log-retention -F days=N`. This also shortens
  how long run logs are kept.
- `<maven.deploy.skip>true</maven.deploy.skip>` on modules nobody downloads, such as Spring Boot jars.
- Re-run `report.py` monthly, or whenever a bill or a quota error shows up. `python scripts/selftest.py` checks the
  scripts' logic without the network.
