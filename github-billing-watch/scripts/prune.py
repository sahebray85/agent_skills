#!/usr/bin/env python3
"""Plan, then apply, deletions of GitHub Actions artifacts and GitHub Packages versions.

  prune.py artifacts [--keep-days 10] [--keep-newest 10]                       dry run -> plan JSON
  prune.py packages  [--keep-snapshots 10] [--keep-releases 10] [--pin PREFIX:VERSION]... [--drop NAME]...
  prune.py containers [--keep-newest 10] [--keep-releases 3] [--protect [IMAGE:]TAG]... [--drop NAME]...   GHCR images, tagged versions
  prune.py apply PLAN_JSON                                                      deletes exactly the plan's targets

Dry runs only read. `apply` is the only command that deletes. Deleted artifacts are gone for good; deleted packages
and versions are restorable for 30 days unless the same name/version is published again.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
import urllib.parse
from pathlib import Path

PLAN_DIR = Path(tempfile.gettempdir()) / "github-billing-watch"
MB = 1024 ** 2


def gh(*args):
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(((out.stderr or out.stdout).strip().splitlines() or ["?"])[0][:200])
    return json.loads(out.stdout) if out.stdout.strip() else None


def gh_list(path, key=None):
    pages = gh("--paginate", "--slurp", path)
    return [item for page in pages for item in (page[key] if key else page)]


def parse_time(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---- keep rules (pure; covered by selftest.py) ----

def artifacts_to_delete(arts, now, keep_days, keep_newest):
    """Keep an artifact if it is younger than keep_days OR among the newest keep_newest of its repo."""
    by_repo = defaultdict(list)
    for a in arts:
        by_repo[a["repo"]].append(a)
    newest = {a["id"] for group in by_repo.values()
              for a in sorted(group, key=lambda a: a["created"], reverse=True)[:keep_newest]}
    cutoff = now - dt.timedelta(days=keep_days)
    return [a for a in arts if a["created"] < cutoff and a["id"] not in newest]


def versions_to_delete(name, versions, keep_snapshots, keep_releases, pins):
    """Keep the newest N -SNAPSHOT and M release versions, plus any (package-prefix, version) pin."""
    newest_first = sorted(versions, key=lambda v: v["created_at"], reverse=True)
    snapshots = [v for v in newest_first if v["name"].endswith("-SNAPSHOT")]
    releases = [v for v in newest_first if not v["name"].endswith("-SNAPSHOT")]
    keep = {v["id"] for v in snapshots[:keep_snapshots] + releases[:keep_releases]}
    keep |= {v["id"] for v in versions if any(name.startswith(p) and v["name"] == ver for p, ver in pins)}
    return [v for v in newest_first if v["id"] not in keep]


def container_tags(v):
    return ((v.get("metadata") or {}).get("container") or {}).get("tags") or []


def is_container_release(v):
    """A release has tags and none is a SNAPSHOT (`0.38.0`, `0.19.0-prod`, `latest`); `1.2-SNAPSHOT`, `snapshot` are not."""
    tags = container_tags(v)
    return bool(tags) and not any("snapshot" in t.lower() for t in tags)


def container_versions_to_delete(name, versions, keep_newest, protect, keep_releases=0):
    """Delete only TAGGED container versions. Keep the newest N, the newest M releases, `latest`, and any protected tag.

    CI pushes many -SNAPSHOT builds per release, so the newest N alone can hold no release at all: keep_releases
    guarantees the last M release versions survive for rollback.

    `protect` holds bare tags (any image) or (image, tag) pairs. Untagged versions are never planned: on GHCR they are
    usually child manifests or layers of a kept multi-arch tag, and deleting them can break that tag.
    """
    tagged = sorted((v for v in versions if container_tags(v)), key=lambda v: v["created_at"], reverse=True)
    keep = {v["id"] for v in tagged[:keep_newest]}
    keep |= {v["id"] for v in [v for v in tagged if is_container_release(v)][:keep_releases]}
    for v in tagged:
        if any(t == "latest" or t in protect or (name, t) in protect for t in container_tags(v)):
            keep.add(v["id"])
    return [v for v in tagged if v["id"] not in keep]


# ---- dry runs ----

def write_plan(kind, org, rule, targets):
    if not targets:
        print("\nNothing to delete: no plan written.")
        return
    PLAN_DIR.mkdir(exist_ok=True)
    path = PLAN_DIR / f"{org}-{kind}-plan-{dt.datetime.now():%Y%m%d-%H%M%S}.json"
    created = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps({"kind": kind, "org": org, "rule": rule, "created": created, "targets": targets}, indent=1))
    size = sum(t.get("bytes") or 0 for t in targets)
    print(f"\nPLAN: {len(targets)} deletes{f', {size / MB:.1f} MB' if size else ''} -> {path.as_posix()}")
    print(f"Show the table above to the user; only after an explicit yes run: prune.py apply \"{path.as_posix()}\"")


def cross_run_consumers(org):
    """Workflows that download artifacts from *other* runs would break if those artifacts vanish."""
    hits = set()
    for query in ("download-artifact run-id", "action-download-artifact"):
        out = subprocess.run(["gh", "search", "code", query, "--owner", org, "--limit", "50", "--json", "repository,path"],
                             capture_output=True, text=True)
        if out.returncode:
            print(f"WARN could not run code search ({query}): check consumers by hand")
            continue
        hits |= {f"{r['repository']['nameWithOwner']}:{r['path']}" for r in json.loads(out.stdout)}
    for h in sorted(hits):
        print(f"WARN cross-run artifact download (default branch): {h}: keep what it needs")
    if not hits:
        print("cross-run artifact downloads (default branches): none found")


def cmd_artifacts(a):
    now = dt.datetime.now(dt.timezone.utc)
    arts = []
    for repo in [r["name"] for r in gh_list(f"/orgs/{a.org}/repos?per_page=100")]:
        for x in gh_list(f"/repos/{a.org}/{repo}/actions/artifacts?per_page=100", "artifacts"):
            if not x["expired"]:
                arts.append({"repo": repo, "id": x["id"], "name": x["name"], "bytes": x["size_in_bytes"],
                             "created": parse_time(x["created_at"])})
    delete = artifacts_to_delete(arts, now, a.keep_days, a.keep_newest)
    doomed = {d["id"] for d in delete}
    print(f"{'repo':<28} {'delete':>6} {'MB':>8} {'keep':>5} {'MB':>8}")
    for repo in sorted({x["repo"] for x in arts}):
        gone = [x for x in arts if x["repo"] == repo and x["id"] in doomed]
        kept = [x for x in arts if x["repo"] == repo and x["id"] not in doomed]
        print(f"{repo:<28} {len(gone):>6} {sum(x['bytes'] for x in gone) / MB:>8.1f} "
              f"{len(kept):>5} {sum(x['bytes'] for x in kept) / MB:>8.1f}")
    cross_run_consumers(a.org)
    rule = f"keep artifacts younger than {a.keep_days} days OR newest {a.keep_newest} per repo"
    write_plan("artifacts", a.org, rule, [
        {"path": f"/repos/{a.org}/{x['repo']}/actions/artifacts/{x['id']}", "bytes": x["bytes"],
         "label": f"{x['repo']} {x['name']} {x['created']:%Y-%m-%d}"} for x in delete])


def cmd_packages(a):
    pins = [tuple(p.rsplit(":", 1)) for p in a.pin]
    used_pins, seen, targets = set(), set(), []
    print(f"{'repo':<24} {'package':<52} {'total':>5} {'keep':>5} {'del':>5}")
    for pkg in gh_list(f"/orgs/{a.org}/packages?package_type={a.type}&per_page=100"):
        name, repo = pkg["name"], (pkg.get("repository") or {}).get("name", "-")
        base = f"/orgs/{a.org}/packages/{a.type}/{name}"
        seen.add(name)
        if name in a.drop:
            print(f"{repo:<24} {name:<52} {pkg.get('version_count', '?'):>5} {0:>5} {'ALL':>5}  (whole package)")
            targets.append({"path": base, "label": f"whole package {name}"})
            continue
        versions = gh_list(f"{base}/versions?per_page=100")
        delete = versions_to_delete(name, versions, a.keep_snapshots, a.keep_releases, pins)
        used_pins |= {(p, v["name"]) for v in versions for p, ver in pins if name.startswith(p) and v["name"] == ver}
        if delete and len(delete) == len(versions):
            print(f"WARN {name}: rule would delete every version; skipped (use --drop to delete the package)")
            continue
        print(f"{repo:<24} {name:<52} {len(versions):>5} {len(versions) - len(delete):>5} {len(delete):>5}")
        targets += [{"path": f"{base}/versions/{v['id']}", "label": f"{name} {v['name']}"} for v in delete]
    for name in set(a.drop) - seen:
        print(f"WARN --drop {name}: no such {a.type} package")
    for p in set(pins) - used_pins:
        print(f"WARN --pin {p[0]}:{p[1]} matched no version: typo, or that version is already gone")
    rule = (f"keep newest {a.keep_snapshots} SNAPSHOT + {a.keep_releases} release per package; "
            f"pins {a.pin or 'none'}; drop {a.drop or 'none'}")
    write_plan(f"packages-{a.type}", a.org, rule, targets)


def cmd_containers(a):
    protect = {tuple(p.split(":", 1)) if ":" in p else p for p in a.protect}
    seen, used, targets = set(), set(), []
    print(f"{'image':<34} {'total':>5} {'tagged':>6} {'keep':>5} {'del':>5} {'untagged (never planned)':>25}")
    for pkg in gh_list(f"/orgs/{a.org}/packages?package_type=container&per_page=100"):
        name = pkg["name"]
        base = f"/orgs/{a.org}/packages/container/{urllib.parse.quote(name, safe='')}"
        seen.add(name)
        if name in a.drop:
            print(f"{name:<34} {pkg.get('version_count') or '?':>5} {'':>6} {0:>5} {'ALL':>5}  (whole package)")
            targets.append({"path": base, "label": f"whole image {name}"})
            continue
        versions = gh_list(f"{base}/versions?per_page=100")
        delete = container_versions_to_delete(name, versions, a.keep_newest, protect, a.keep_releases)
        tagged = [v for v in versions if container_tags(v)]
        used |= {p for v in tagged for t in container_tags(v) for p in (t, (name, t)) if p in protect}
        print(f"{name:<34} {len(versions):>5} {len(tagged):>6} {len(tagged) - len(delete):>5} {len(delete):>5} "
              f"{len(versions) - len(tagged):>25}")
        targets += [{"path": f"{base}/versions/{v['id']}",
                     "label": f"{name} {','.join(container_tags(v))} {v['created_at'][:10]}"} for v in delete]
    for name in set(a.drop) - seen:
        print(f"WARN --drop {name}: no such container package")
    for p in protect - used:
        print(f"WARN --protect {p if isinstance(p, str) else ':'.join(p)} matched no version: typo, or already gone")
    print("NOTE GitHub does not expose container sizes, so no MB column. Check each kept image still pulls after apply.")
    rule = f"keep latest + newest {a.keep_newest} tagged + newest {a.keep_releases} releases + protect {sorted(map(str, a.protect)) or 'none'}; drop {a.drop or 'none'}"
    write_plan("containers", a.org, rule, targets)


# ---- apply ----

def delete(path):
    for _ in range(5):
        out = subprocess.run(["gh", "api", "-X", "DELETE", path], capture_output=True, text=True)
        err = (out.stderr or out.stdout).strip()
        if out.returncode == 0 or "HTTP 404" in err:  # 404 = already gone
            return None
        if "rate limit" in err.lower() or "HTTP 429" in err:
            time.sleep(60)
            continue
        return err.splitlines()[0][:200] if err else f"exit {out.returncode}"
    return "still rate limited after 5 tries"


def cmd_apply(a):
    plan = json.loads(Path(a.plan).read_text())
    targets = plan["targets"]
    print(f"{plan['kind']} plan for {plan['org']} made {plan['created']}: {len(targets)} deletes. Rule: {plan['rule']}")
    ok = fail = 0
    for i, t in enumerate(targets, 1):
        error = delete(t["path"])
        ok, fail = ok + (error is None), fail + (error is not None)
        if error:
            print(f"FAIL {t['label']}: {error}", flush=True)
        if fail >= 3 and ok == 0:
            print("ABORT: the first deletes all failed (permissions? billing lock?)")
            break
        if i % 50 == 0:
            print(f"[{i}/{len(targets)}] ok={ok} fail={fail}", flush=True)
        time.sleep(0.4)
    print(f"DONE ok={ok} fail={fail} of {len(targets)}")
    sys.exit(1 if fail else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    art = sub.add_parser("artifacts", help="dry run: plan Actions artifact deletes")
    art.add_argument("--keep-days", type=int, default=10)
    art.add_argument("--keep-newest", type=int, default=10, help="per repo")
    pkg = sub.add_parser("packages", help="dry run: plan package version deletes")
    pkg.add_argument("--type", default="maven")
    pkg.add_argument("--keep-snapshots", type=int, default=10)
    pkg.add_argument("--keep-releases", type=int, default=10)
    pkg.add_argument("--pin", action="append", default=[], help="PACKAGE_PREFIX:VERSION another repo depends on")
    pkg.add_argument("--drop", action="append", default=[], help="delete this whole package")
    con = sub.add_parser("containers", help="dry run: plan GHCR container image version deletes")
    con.add_argument("--keep-newest", type=int, default=10, help="newest tagged versions kept per image")
    con.add_argument("--keep-releases", type=int, default=3,
                     help="also keep the newest N non-SNAPSHOT release versions per image (rollback floor)")
    con.add_argument("--protect", action="append", default=[], help="[IMAGE:]TAG deployed or pinned somewhere (deploy repo)")
    con.add_argument("--drop", action="append", default=[], help="delete this whole image")
    for s in (art, pkg, con):
        s.add_argument("--org", default="sharanaya-boutique")
    ap = sub.add_parser("apply", help="delete exactly the targets of a reviewed plan")
    ap.add_argument("plan")
    a = p.parse_args()
    {"artifacts": cmd_artifacts, "packages": cmd_packages,
     "containers": cmd_containers, "apply": cmd_apply}[a.cmd](a)


if __name__ == "__main__":
    main()
