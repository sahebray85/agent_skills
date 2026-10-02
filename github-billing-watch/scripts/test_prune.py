"""Self-check for prune.py's keep rules (no network): python test_prune.py"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prune import artifacts_to_delete, versions_to_delete  # noqa: E402

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
print("test_prune: all checks passed")
