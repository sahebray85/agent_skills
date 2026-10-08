#!/usr/bin/env python3
"""READ-ONLY GitHub billing and storage report for an org and (optionally) the enterprise that bills it.

Sections: plan, billing-lock signals, real vs billed storage, month-to-date usage by product/SKU, allowance used,
budgets, warnings. Needs an authenticated `gh` with org admin + billing read. Never writes anything.

  python report.py [--org ORG] [--enterprise SLUG] [--month YYYY-MM]
"""
import argparse
import urllib.parse
import datetime as dt
import json
import subprocess
from collections import defaultdict

# plan: (Actions minutes, storage GB) included each month. Per account, not per seat.
ALLOWANCE = {"free": (2000, 0.5), "team": (3000, 2), "enterprise": (50000, 50)}
STORAGE_SKUS = ("Packages storage", "Actions storage")  # these two share the storage allowance
HOURS_PER_MONTH = 744  # GitHub turns GB-hours into GB-months with 744 hours, whatever the month's length
GB = 1024 ** 3
WARNINGS = []

PKG_QUERY = """
query($org:String!, $cursor:String) {
  organization(login:$org) {
    packages(first:20, after:$cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        repository { name }
        versions(first:100) { totalCount nodes { files(first:100) { totalCount nodes { size } } } }
      }
    }
  }
}"""


def gh(*args):
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(((out.stderr or out.stdout).strip().splitlines() or ["?"])[0][:200])
    return json.loads(out.stdout) if out.stdout.strip() else None


def gh_list(path, key=None):
    pages = gh("--paginate", "--slurp", path)
    return [item for page in pages for item in (page[key] if key else page)]


def soft(fn, *args):
    try:
        return fn(*args)
    except RuntimeError as e:
        print(f"  unavailable: {e}")
        return None


def section(title):
    print(f"\n== {title}")


def is_lock_run(run):
    return run["conclusion"] == "startup_failure" and (not run["name"] or run["path"] == "BuildFailed")


def lock_state(latest):
    """latest: {repo: its newest run}. Returns ({repo: time} still locked, {repo: time} stale).

    A billing lock fails every run org-wide, so a lock-shaped run older than a normal run elsewhere is stale:
    the lock lifted and that repo simply hasn't run since.
    """
    normal = max((r["created_at"] for r in latest.values() if not is_lock_run(r)), default="")
    locked = {repo: r["created_at"] for repo, r in latest.items() if is_lock_run(r)}
    return ({k: v for k, v in locked.items() if v > normal}, {k: v for k, v in locked.items() if v <= normal})


def allowance_used(items, plan):
    """Month-to-date (minutes, minutes included, GB-hours, GB-hours included), or None for an unknown plan."""
    if plan not in ALLOWANCE:
        return None
    # ponytail: raw minutes. Windows and macOS runners count 2x and 10x; weight them if they ever appear.
    minutes = sum(i["quantity"] for i in items if i["product"].lower() == "actions" and i["unitType"] == "Minutes")
    gb_hours = sum(i["quantity"] for i in items if i["sku"] in STORAGE_SKUS)
    max_minutes, max_gb = ALLOWANCE[plan]
    return minutes, max_minutes, gb_hours, max_gb * HOURS_PER_MONTH


def billed_without_live(billed_gb_hours, live_bytes, floor=0.5):
    """Repos billed for Packages storage that hold no live package: deleted-but-restorable versions still bill."""
    return sorted(repo for repo, qty in billed_gb_hours.items() if qty >= floor and not live_bytes.get(repo))


def lock_signals(org, enterprise, repos):
    section("Billing-lock signals")
    if enterprise:
        events = soft(gh, f"/enterprises/{enterprise}/audit-log?phrase=action:billing.lock&per_page=1")
        if events:
            at = dt.datetime.fromtimestamp(events[0]["@timestamp"] / 1000, dt.timezone.utc)
            print(f"  latest billing.lock on {enterprise}: {at:%Y-%m-%d %H:%M}Z (the run check below is the live signal)")
    latest = {}
    for repo in repos:
        runs = (soft(gh, f"/repos/{org}/{repo}/actions/runs?per_page=1") or {}).get("workflow_runs") or []
        if runs:
            latest[repo] = runs[0]
    recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    locked, stale = lock_state(latest)
    locked = {repo: at for repo, at in locked.items() if at > recent}
    shown = lambda runs: ", ".join(f"{repo} ({at[:16]}Z)" for repo, at in sorted(runs.items()))
    if locked:
        print(f"  latest run is a nameless startup_failure (path BuildFailed) in: {shown(locked)}")
        WARNINGS.append(f"Actions looks billing-locked in {len(locked)} repo(s): no CI result proves anything until it lifts")
    else:
        print("  no repo is billing-locked")
    if stale:
        print(f"  stale (a normal run elsewhere is newer, so the lock lifted): {shown(stale)}")


def package_sizes(org):
    rows, cursor, truncated = [], None, False
    while True:
        args = ["graphql", "-f", f"query={PKG_QUERY}", "-f", f"org={org}"] + (["-f", f"cursor={cursor}"] if cursor else [])
        page = gh(*args)["data"]["organization"]["packages"]
        for p in page["nodes"]:
            vs = p["versions"]
            size = sum(f["size"] or 0 for v in vs["nodes"] for f in v["files"]["nodes"])
            rows.append((p["name"], (p["repository"] or {}).get("name", "?"), vs["totalCount"], size))
            truncated |= vs["totalCount"] > len(vs["nodes"]) or any(
                v["files"]["totalCount"] > len(v["files"]["nodes"]) for v in vs["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return rows, truncated
        cursor = page["pageInfo"]["endCursor"]


def container_inventory(org):
    """GHCR images. GitHub exposes no container sizes (the GraphQL query above misses them), so count versions."""
    section("Container images (GHCR): version counts only, GitHub exposes no sizes")
    rows = []
    for pkg in gh_list(f"/orgs/{org}/packages?package_type=container&per_page=100"):
        vs = gh_list(f"/orgs/{org}/packages/container/{urllib.parse.quote(pkg['name'], safe='')}/versions?per_page=100")
        tagged = sum(1 for v in vs if ((v.get("metadata") or {}).get("container") or {}).get("tags"))
        rows.append((pkg["name"], len(vs), tagged))
    for name, total, tagged in sorted(rows, key=lambda r: -r[1])[:8]:
        print(f"  image    {name:<44} {total:>4} versions ({tagged} tagged, {total - tagged} untagged)")
    total = sum(r[1] for r in rows)
    print(f"  {len(rows)} images, {total} versions in all")
    if total > 20 * max(len(rows), 1):
        WARNINGS.append(f"{total} container versions across {len(rows)} images: the billing page's Packages storage counts "
                        "them but the REAL line above does not. Plan with: prune.py containers")


def storage(org, repos):
    section("Storage (real bytes now vs billed yesterday)")
    pkgs, truncated = package_sizes(org)
    pkg_bytes = sum(r[3] for r in pkgs)
    live_bytes = defaultdict(int)
    for name, repo, count, size in pkgs:
        live_bytes[repo] += size
    for name, repo, count, size in sorted(pkgs, key=lambda r: -r[3])[:5]:
        if size:
            print(f"  package  {name:<50} {count:>4} versions {size / 1024**2:>9.1f} MB")
    art_bytes, art_count = 0, 0
    for repo in repos:
        live = [a for a in gh_list(f"/repos/{org}/{repo}/actions/artifacts?per_page=100", "artifacts") if not a["expired"]]
        size = sum(a["size_in_bytes"] for a in live)
        art_bytes, art_count = art_bytes + size, art_count + len(live)
        if live:
            print(f"  artifacts {repo:<49} {len(live):>4} live     {size / 1024**2:>9.1f} MB")
    print(f"  REAL (Maven etc., not containers): packages {pkg_bytes / GB:.3f} GB{' (undercount: >100 versions/files)' if truncated else ''}"
          f" + artifacts {art_bytes / GB:.3f} GB ({art_count}) = {(pkg_bytes + art_bytes) / GB:.3f} GB")

    soft(container_inventory, org)

    day = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    data = soft(gh, f"/organizations/{org}/settings/billing/usage?year={day.year}&month={day.month}&day={day.day}")
    billed, billed_by_repo = defaultdict(float), defaultdict(float)
    for it in (data or {}).get("usageItems", []):
        if it["unitType"] == "GigabyteHours":
            billed[it["sku"]] += it["quantity"] / 24
        if it["sku"] == "Packages storage":
            billed_by_repo[it.get("repositoryName") or "?"] += it["quantity"]
    for sku, avg in sorted(billed.items()):
        print(f"  BILLED {day}: {sku:<20} avg {avg:.3f} GB")
    if billed.get("Packages storage", 0) > 2 * pkg_bytes / GB + 0.05:
        WARNINGS.append("billed Packages storage is far above real bytes: usage lags a day, or deleted-but-restorable "
                        "versions are still billed (they purge after 30 days)")
    ghosts = billed_without_live(billed_by_repo, live_bytes)
    if ghosts:
        WARNINGS.append(f"Packages storage was billed on {day} for repos with no live package ({', '.join(ghosts)}): "
                        "deleted versions keep billing until they purge")


def usage(base, label, year, month):
    section(f"Usage {year}-{month:02d}: {label}")
    data = soft(gh, f"{base}/settings/billing/usage?year={year}&month={month}")
    if data is None:
        return None
    items = data.get("usageItems", [])
    agg = defaultdict(lambda: {"qty": 0.0, "gross": 0.0, "net": 0.0, "unit": ""})
    days = defaultdict(dict)  # sku -> {day: net}
    for it in items:
        a = agg[(it["product"], it["sku"])]
        a["qty"] += it["quantity"]
        a["gross"] += it["grossAmount"]
        a["net"] += it["netAmount"]
        a["unit"] = it["unitType"]
        day = it["date"][:10]
        days[it["sku"]][day] = days[it["sku"]].get(day, 0.0) + it["netAmount"]
    for (product, sku), a in sorted(agg.items(), key=lambda kv: (-kv[1]["net"], -kv[1]["gross"])):
        print(f"  {product:<14} {sku:<26} {a['qty']:>12.2f} {a['unit']:<14} gross ${a['gross']:>8.2f}  net ${a['net']:>8.2f}")
        warning = f"{sku} net ${a['net']:.2f} (a licence, or metered use past the free allowance)"
        if a["net"] >= 0.01 and warning not in WARNINGS:  # org and enterprise views repeat the same line items
            WARNINGS.append(warning)
    print(f"  TOTAL gross ${sum(a['gross'] for a in agg.values()):.2f}  net ${sum(a['net'] for a in agg.values()):.2f}")
    for sku, by_day in sorted(days.items()):
        charged = {d: n for d, n in by_day.items() if n >= 0.005}
        if charged:  # shows whether a charge is still accruing after you switched something off
            last = max(charged)
            print(f"  charged: {sku:<26} on {len(charged)} day(s), latest {last} ${charged[last]:.2f}")
    return items


def allowance(items, plan):
    section("Allowance used this month (per account, not per seat)")
    used = allowance_used(items or [], plan)
    if used is None:
        print(f"  no allowance table for plan '{plan}'")
        return
    minutes, max_minutes, gb_hours, max_gb_hours = used
    for label, value, limit, unit in (("Actions minutes", minutes, max_minutes, "minutes"),
                                      ("Packages + artifact storage", gb_hours, max_gb_hours, "GB-hours")):
        print(f"  {label:<28} {value:>9.0f} of {limit:>6.0f} {unit:<9} {value / limit:>5.0%}")
        if value >= 0.8 * limit:
            WARNINGS.append(f"{label}: {value / limit:.0%} of the {plan} allowance is used. Past 100%, a $0 hard-stop "
                            "budget stops CI (minutes) or refuses uploads with HTTP 402 (storage)")


def budgets(base, label):
    section(f"Budgets: {label}")
    data = soft(gh, f"{base}/settings/billing/budgets")
    for b in (data or {}).get("budgets", []):
        target = b.get("budget_product_sku") or ",".join(b.get("budget_product_skus") or [])
        print(f"  {b['budget_type']:<15} {target:<22} {b['budget_scope']:<12} ${b['budget_amount']:<7} "
              f"hard_stop={b['prevent_further_usage']}  id={b['id']}")
        if not b["prevent_further_usage"]:
            WARNINGS.append(f"{label} budget {target} has no hard stop: it only alerts")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--org", default="sharanaya-boutique")
    p.add_argument("--enterprise", default="", help="slug of the enterprise that bills the org, if any")
    p.add_argument("--month", help="YYYY-MM, default current UTC month")
    a = p.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    year, month = map(int, a.month.split("-")) if a.month else (now.year, now.month)

    plan = (soft(gh, f"/orgs/{a.org}") or {}).get("plan", {}).get("name", "?")
    print(f"org {a.org}: plan={plan}   report at {now:%Y-%m-%d %H:%M}Z")
    repos = [r["name"] for r in gh_list(f"/orgs/{a.org}/repos?per_page=100")]  # archived repos' artifacts still bill
    lock_signals(a.org, a.enterprise, repos)
    storage(a.org, repos)
    allowance(usage(f"/organizations/{a.org}", f"org {a.org}", year, month), plan)
    if a.enterprise:
        usage(f"/enterprises/{a.enterprise}", f"enterprise {a.enterprise}", year, month)
    budgets(f"/organizations/{a.org}", f"org {a.org}")
    if a.enterprise:
        budgets(f"/enterprises/{a.enterprise}", f"enterprise {a.enterprise}")
    section("Warnings")
    print("\n".join(f"  ! {w}" for w in WARNINGS) or "  none")


if __name__ == "__main__":
    main()
