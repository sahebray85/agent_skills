"""Self-check for the pure logic in prune.py and report.py (no network): python selftest.py"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prune import artifacts_to_delete, container_versions_to_delete, is_container_release, versions_to_delete  # noqa: E402
from report import HOURS_PER_MONTH, allowance_used, billed_without_live, lock_state  # noqa: E402

now = dt.datetime(2026, 1, 31, tzinfo=dt.timezone.utc)


def art(repo, i, days_old):
    return {"repo": repo, "id": f"{repo}{i}", "created": now - dt.timedelta(days=days_old)}


# repo a: 2 fresh + 12 old (20..31 days). Newest 10 = 2 fresh + 8 old, so the 4 oldest go.
# repo b: 3 old ones. The newest-10 rule keeps a quiet repo from being emptied.
arts = [art("a", i, 1) for i in range(2)] + [art("a", 10 + i, 20 + i) for i in range(12)] + [art("b", i, 40 + i) for i in range(3)]
assert sorted(x["id"] for x in artifacts_to_delete(arts, now, 10, 10)) == ["a18", "a19", "a20", "a21"]
assert len(artifacts_to_delete(arts, now, 10, 0)) == 15, "days-only rule deletes every old artifact"
assert artifacts_to_delete(arts, now, 60, 0) == [], "nothing is older than 60 days"


def ver(i, name):
    return {"id": i, "name": name, "created_at": f"2026-01-{i:02d}T00:00:00Z"}


# releases 0.1.0..0.12.0 (ids 1-12), snapshots 1.1.0..1.12.0-SNAPSHOT (ids 13-24), oldest first
vs = [ver(i, f"0.{i}.0") for i in range(1, 13)] + [ver(12 + i, f"1.{i}.0-SNAPSHOT") for i in range(1, 13)]
ids = lambda pins, name="com.x.client-api": sorted(v["id"] for v in versions_to_delete(name, vs, 10, 10, pins))
assert ids([]) == [1, 2, 13, 14]
assert ids([("com.x.", "0.1.0")]) == [2, 13, 14], "pinned oldest release survives"
assert ids([("com.y.", "0.1.0")]) == [1, 2, 13, 14], "a pin only applies to its own package prefix"


def cver(i, *tags):
    return {"id": i, "created_at": f"2026-01-{i:02d}T00:00:00Z", "metadata": {"container": {"tags": list(tags)}}}


# ids 1-12 tagged v1..v12, id 13 untagged child manifest, id 14 oldest-looking "latest" is id 2 (re-tagged)
cvs = [cver(i, f"v{i}") for i in range(1, 13)] + [cver(13)]
cvs[1] = cver(2, "v2", "latest")
cids = lambda protect=frozenset(), name="img": sorted(v["id"] for v in container_versions_to_delete(name, cvs, 10, protect))
assert cids() == [1], "newest 10 tagged kept, `latest` kept even when old, untagged never planned"
assert cids({"v1"}) == [], "a bare protected tag is kept for any image"
assert cids({("other", "v1")}) == [1], "an IMAGE:TAG protect only applies to its own image"
assert cids({("img", "v1")}) == []


# 9 newer SNAPSHOT builds bury the releases: newest-10 alone would keep no release.
def ctags(i, *tags): return cver(i, *tags)
rel = [ctags(i, f"1.{i}.0") for i in range(1, 5)] + [ctags(10 + i, f"2.{i}.0-SNAPSHOT") for i in range(1, 13)]
rd = lambda m: sorted(v["id"] for v in container_versions_to_delete("img", rel, 10, set(), m))
assert rd(0) == [1, 2, 3, 4, 11, 12], "without the floor every release is dropped"
assert rd(3) == [1, 11, 12], "the newest 3 releases survive"
assert [is_container_release(v) for v in (cver(1, "0.19.0", "latest"), cver(2, "0.19.1-SNAPSHOT", "snapshot"), cver(3))] == [True, False, False]

def item(product, sku, unit, qty):
    return {"product": product, "sku": sku, "unitType": unit, "quantity": qty}


# Packages and artifact storage share the allowance; Git LFS has its own and must not count.
usage = [item("actions", "Actions Linux", "Minutes", 115), item("packages", "Packages storage", "GigabyteHours", 380),
         item("actions", "Actions storage", "GigabyteHours", 4), item("git_lfs", "Git LFS storage", "GigabyteHours", 25)]
assert allowance_used(usage, "free") == (115, 2000, 384, 0.5 * HOURS_PER_MONTH), "0.5 GB is 372 GB-hours a month"
assert allowance_used(usage, "team")[1::2] == (3000, 2 * HOURS_PER_MONTH)
assert allowance_used(usage, "no-such-plan") is None

# "gone" is billed but holds no live package; "noise" is under the floor; "live" still has bytes.
assert billed_without_live({"gone": 3.0, "live": 80.0, "noise": 0.07}, {"live": 21_000_000, "gone": 0}) == ["gone"]


def run(at, locked):
    return {"created_at": at, "conclusion": "startup_failure" if locked else "success",
            "name": "" if locked else "CI", "path": "BuildFailed" if locked else ".github/workflows/ci.yml"}


lock = "2026-01-02T10:00:00Z"
assert lock_state({"a": run(lock, True), "b": run("2026-01-02T09:00:00Z", False)}) == ({"a": lock}, {}), "still locked"
assert lock_state({"a": run(lock, True), "b": run("2026-01-02T11:00:00Z", False)}) == ({}, {"a": lock}), "lock lifted"
print("selftest: all checks passed")
