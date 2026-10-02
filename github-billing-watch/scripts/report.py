#!/usr/bin/env python3
"""READ-ONLY GitHub billing and storage report for an org and (optionally) its enterprise.

Sections: plan, billing-lock signals, real vs billed storage, month-to-date usage by product/SKU, budgets, warnings.
Needs an authenticated `gh` with org admin + billing read. Never writes anything.

  python report.py [--org ORG] [--enterprise SLUG | --enterprise ""] [--month YYYY-MM]
"""
import argparse
import datetime as dt
import json
import subprocess
from collections import defaultdict

FREE_STORAGE_GB = 0.5  # Free plan: GitHub Packages + Actions artifacts share this allowance
GB = 1024 ** 3
WARNINGS = []

PKG_QUERY = """
query($org:String!, $cursor:String) {
  organization(login:$org) {
    packages(first:20, after:$cursor) {
      pageInfo { hasNextPage endCursor }
      nodes { name versions(first:100) { totalCount nodes { files(first:100) { totalCount nodes { size } } } } }
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


def lock_signals(org, enterprise, repos):
    section("Billing-lock signals")
    if enterprise:
        events = soft(gh, f"/enterprises/{enterprise}/audit-log?phrase=action:billing.lock&per_page=1")
        if events:
            at = dt.datetime.fromtimestamp(events[0]["@timestamp"] / 1000, dt.timezone.utc)
            print(f"  latest billing.lock on {enterprise}: {at:%Y-%m-%d %H:%M}Z (the run check below is the live signal)")
    recent = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)
    locked = []
    for repo in repos:
        runs = (soft(gh, f"/repos/{org}/{repo}/actions/runs?per_page=1") or {}).get("workflow_runs") or []
        run = runs[0] if runs else None
        if run and dt.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) > recent \
                and run["conclusion"] == "startup_failure" and (not run["name"] or run["path"] == "BuildFailed"):
            locked.append(f"{repo} ({run['created_at'][:16]}Z)")
    if locked:
        print(f"  latest run is a nameless startup_failure (path BuildFailed) in: {', '.join(locked)}")
        WARNINGS.append(f"Actions looks billing-locked in {len(locked)} repo(s): no CI result proves anything until it lifts")
    else:
        print("  no recent nameless startup_failure runs")


def package_sizes(org):
    rows, cursor, truncated = [], None, False
    while True:
        args = ["graphql", "-f", f"query={PKG_QUERY}", "-f", f"org={org}"] + (["-f", f"cursor={cursor}"] if cursor else [])
        page = gh(*args)["data"]["organization"]["packages"]
        for p in page["nodes"]:
            vs = p["versions"]
            rows.append((p["name"], vs["totalCount"], sum(f["size"] or 0 for v in vs["nodes"] for f in v["files"]["nodes"])))
            truncated |= vs["totalCount"] > len(vs["nodes"]) or any(
                v["files"]["totalCount"] > len(v["files"]["nodes"]) for v in vs["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return rows, truncated
        cursor = page["pageInfo"]["endCursor"]


def storage(org, repos, plan):
    section("Storage (real bytes now vs billed yesterday)")
    pkgs, truncated = package_sizes(org)
    pkg_bytes = sum(r[2] for r in pkgs)
    for name, count, size in sorted(pkgs, key=lambda r: -r[2])[:5]:
        if size:
            print(f"  package  {name:<50} {count:>4} versions {size / 1024**2:>9.1f} MB")
    art_bytes, art_count = 0, 0
    for repo in repos:
        live = [a for a in gh_list(f"/repos/{org}/{repo}/actions/artifacts?per_page=100", "artifacts") if not a["expired"]]
        size = sum(a["size_in_bytes"] for a in live)
        art_bytes, art_count = art_bytes + size, art_count + len(live)
        if live:
            print(f"  artifacts {repo:<49} {len(live):>4} live     {size / 1024**2:>9.1f} MB")
    real = (pkg_bytes + art_bytes) / GB
    print(f"  REAL: packages {pkg_bytes / GB:.3f} GB{' (undercount: >100 versions/files)' if truncated else ''}"
          f" + artifacts {art_bytes / GB:.3f} GB ({art_count}) = {real:.3f} GB")
    if plan == "free":
        print(f"  Free allowance {FREE_STORAGE_GB} GB -> {real / FREE_STORAGE_GB:.0%} used")
        if real > 0.8 * FREE_STORAGE_GB:
            WARNINGS.append(f"storage {real:.2f} GB is over 80% of the Free {FREE_STORAGE_GB} GB: plan a cleanup")

    day = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    data = soft(gh, f"/organizations/{org}/settings/billing/usage?year={day.year}&month={day.month}&day={day.day}")
    billed = defaultdict(float)
    for it in (data or {}).get("usageItems", []):
        if it["unitType"] == "GigabyteHours":
            billed[it["sku"]] += it["quantity"] / 24
    for sku, avg in sorted(billed.items()):
        print(f"  BILLED {day}: {sku:<20} avg {avg:.3f} GB")
    if billed.get("Packages storage", 0) > 2 * pkg_bytes / GB + 0.05:
        WARNINGS.append("billed Packages storage is far above real bytes: usage lags a day, or deleted-but-restorable "
                        "versions are still billed (they purge after 30 days)")


def usage(base, label, year, month):
    section(f"Usage {year}-{month:02d}: {label}")
    data = soft(gh, f"{base}/settings/billing/usage?year={year}&month={month}")
    if data is None:
        return
    agg = defaultdict(lambda: {"qty": 0.0, "gross": 0.0, "net": 0.0, "unit": ""})
    for it in data.get("usageItems", []):
        a = agg[(it["product"], it["sku"])]
        a["qty"] += it["quantity"]
        a["gross"] += it["grossAmount"]
        a["net"] += it["netAmount"]
        a["unit"] = it["unitType"]
    for (product, sku), a in sorted(agg.items()):
        print(f"  {product:<14} {sku:<26} {a['qty']:>12.2f} {a['unit']:<14} gross ${a['gross']:>8.2f}  net ${a['net']:>8.2f}")
        warning = f"{sku} net ${a['net']:.2f} (a licence, or metered use past the free allowance)"
        if a["net"] >= 0.01 and warning not in WARNINGS:  # org and enterprise views repeat the same line items
            WARNINGS.append(warning)
    print(f"  TOTAL gross ${sum(a['gross'] for a in agg.values()):.2f}  net ${sum(a['net'] for a in agg.values()):.2f}")


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
    p.add_argument("--enterprise", default="krishna-ai-solutions", help='"" to skip enterprise sections')
    p.add_argument("--month", help="YYYY-MM, default current UTC month")
    a = p.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    year, month = map(int, a.month.split("-")) if a.month else (now.year, now.month)

    plan = (soft(gh, f"/orgs/{a.org}") or {}).get("plan", {}).get("name", "?")
    print(f"org {a.org}: plan={plan}   report at {now:%Y-%m-%d %H:%M}Z")
    repos = [r["name"] for r in gh_list(f"/orgs/{a.org}/repos?per_page=100")]  # archived repos' artifacts still bill
    lock_signals(a.org, a.enterprise, repos)
    storage(a.org, repos, plan)
    usage(f"/organizations/{a.org}", f"org {a.org}", year, month)
    if a.enterprise:
        usage(f"/enterprises/{a.enterprise}", f"enterprise {a.enterprise}", year, month)
    budgets(f"/organizations/{a.org}", f"org {a.org}")
    if a.enterprise:
        budgets(f"/enterprises/{a.enterprise}", f"enterprise {a.enterprise}")
    section("Warnings")
    print("\n".join(f"  ! {w}" for w in WARNINGS) or "  none")


if __name__ == "__main__":
    main()
