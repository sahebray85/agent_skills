---
name: github-billing-watch
description: Reports GitHub org and enterprise billing (month-to-date cost by product and SKU, budgets and hard stops, real vs billed storage against the Free plan's 0.5 GB, billing-lock signals) and safely prunes GitHub Actions artifacts and GitHub Packages versions through a reviewed dry-run plan. Use when the user asks about GitHub cost, bill, invoice, budgets, spending limits, storage or quota, "data transfer out quota has been exceeded", nameless startup_failure runs, or wants to clean up, prune or delete old artifacts or package versions.
---

# GitHub billing watch

Two scripts in `scripts/` next to this file, driven by an authenticated `gh` (org admin + billing read). Run them as
`python "<this skill's dir>/scripts/<script>.py"`, with forward slashes or a quoted path. Defaults:
`--org sharanaya-boutique`, `--enterprise krishna-ai-solutions` (pass `--enterprise ""` once the org leaves it).

## Monitor (read-only, any time)

```
python scripts/report.py [--month YYYY-MM]
```

Read it in this order and report figures, not guesses:
1. **Billing-lock signals.** A repo whose latest run is a nameless `startup_failure` (path `BuildFailed`) is
   billing-locked, not broken YAML. While locked, no CI result proves anything.
2. **Storage.** REAL is the bytes stored now. BILLED is yesterday's average from the usage API, which lags a day and
   has no hourly view. BILLED far above REAL the day after a cleanup is normal; check again the next day.
3. **Usage.** Net > 0 on a metered SKU means the free allowance is used up or the SKU has no free tier. Licence SKUs
   (Enterprise Cloud, Code Quality licences) are always net > 0 and no budget can cap them.
4. **Budgets.** Org budgets don't stop usage billed through an enterprise; check the enterprise budgets too.

Explain what a figure means before recommending anything; see [REFERENCE.md](REFERENCE.md) for the billing rules.

## Clean up (destructive: follow every step)

- [ ] 1. Run `report.py`. Know what fills the space, and whether a cleanup is needed at all.
- [ ] 2. Agree the keep rule with the user. Defaults: **artifacts** are kept if younger than 10 days OR among the
      newest 10 per repo; **packages** keep the newest 10 `-SNAPSHOT` + 10 release versions each.
- [ ] 3. Find pinned versions: another repo's pom that depends on a fixed (non-SNAPSHOT) version of an org package.
      `gh search code "com.sharanaya" --owner sharanaya-boutique --filename pom.xml`, read the hits, and pass each
      as `--pin PACKAGE_PREFIX:VERSION` (e.g. `--pin com.sharanaya.securityservice.:0.4.0`).
- [ ] 4. Dry run. It only reads, prints a per-repo or per-package table, and writes a plan JSON to the temp dir:
      ```
      python scripts/prune.py artifacts --keep-days 10 --keep-newest 10
      python scripts/prune.py packages --keep-snapshots 10 --keep-releases 10 --pin ... [--drop WHOLE_PACKAGE]
      ```
      `--drop` is for packages nobody consumes: a deprecated repo, or a boot jar every Dockerfile builds from source.
- [ ] 5. Show the user the table, every `WARN` line, and the undo story: **artifacts are gone for good**; packages
      are restorable for 30 days unless that version is published again. Wait for an explicit yes.
- [ ] 6. `python scripts/prune.py apply "<plan.json>"` deletes exactly the reviewed targets: paced, 404 counted as
      done, aborts if the first deletes all fail. For more than ~200 targets run it in the background.
- [ ] 7. Verify: re-run the same dry run (expect 0 deletes) and `report.py` (REAL storage dropped). BILLED storage
      drops in the next day's usage.

Never delete without a dry run the user saw. Never delete a version a `--pin` protects. Never `--drop` a package
another repo resolves from GitHub Packages.

## Stop regrowth (offer; don't do it unasked)

- `retention-days: N` on large recurring `upload-artifact` steps, such as coverage reports. This is the narrowest fix.
- Org-wide: `gh api -X PUT /orgs/ORG/actions/permissions/artifact-and-log-retention -F days=N`. This also shortens
  how long run logs are kept.
- `<maven.deploy.skip>true</maven.deploy.skip>` on modules nobody downloads, such as Spring Boot jars.
- Re-run `report.py` monthly, or whenever a bill or a quota error shows up.
