#!/usr/bin/env python3
"""
Refresh the skill's knowledge data (NOT its instructions/logic -- see
config.yaml for the tunable heuristics, and SKILL.md/core.py for the logic
itself, neither of which this script touches).

Re-downloads GeoNames' two source files:
  - geonames_country_info.txt (country names, dial codes, postal formats)
  - the global postal-code -> state map, rebuilt from GeoNames' full
    allCountries.zip export (~1.8M raw rows, dominant-state-wins dedup on
    (country, postal code) conflicts)

Does NOT touch india_pincode_state_map.csv or mauritius_post_office_codes.csv
-- those come from India Post's own directory and a user-supplied file
respectively, not GeoNames, and have no automated re-fetch source. If a
fresher copy of either becomes available, replace the file in knowledge/
directly and note it in LAST_REFRESHED.txt.

Normally you should NOT run this directly -- cache_manager.py runs it
automatically, as a detached background subprocess, whenever
knowledge/cache_meta.json's downloaded_at is older than config.yaml's
knowledge_cache.expiry_days (60 days by default). It's safe to run by
hand too (e.g. to force an immediate refresh); it just does the same
thing cache_manager.py would eventually trigger on its own.

Every file this script writes goes to a .tmp path first and is only
swapped into place via an atomic os.replace() once fully downloaded and
parsed -- a process reading the live file mid-refresh always sees either
the complete old version or the complete new one, never a half-written
file. cache_meta.json's downloaded_at (what cache_manager.py checks for
staleness) is only updated after BOTH files finish successfully.
"""
import csv
import os
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_manager import KNOWLEDGE_DIR, LOCK_PATH, read_meta, write_meta  # noqa: E402

COUNTRY_INFO_URL = "https://download.geonames.org/export/dump/countryInfo.txt"
POSTAL_ZIP_URL = "https://download.geonames.org/export/zip/allCountries.zip"


def refresh_country_info():
    dest = KNOWLEDGE_DIR / "geonames_country_info.txt"
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    urllib.request.urlretrieve(COUNTRY_INFO_URL, tmp)
    os.replace(tmp, dest)  # atomic on POSIX and Windows
    print(f"Refreshed {dest}")


def refresh_postal_map():
    tmpdir = Path(tempfile.mkdtemp())
    zip_path = tmpdir / "allCountries.zip"
    print("Downloading GeoNames allCountries.zip (can take a few minutes)...")
    urllib.request.urlretrieve(POSTAL_ZIP_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmpdir)

    votes = defaultdict(Counter)
    raw_rows = 0
    with open(tmpdir / "allCountries.txt", encoding="utf-8") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 4:
                continue
            country, postal, state = cols[0], cols[1], cols[3]
            raw_rows += 1
            if state:
                votes[(country, postal)][state] += 1

    dest = KNOWLEDGE_DIR / "global_postal_code_map.csv"
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    conflicts = 0
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["countryCode", "postalCode", "state"])
        for (country, postal), counter in sorted(votes.items()):
            if len(counter) > 1:
                conflicts += 1
            state = counter.most_common(1)[0][0]
            writer.writerow([country, f'="{postal}"', state])
    os.replace(tmp, dest)  # atomic swap -- readers never see a partial file

    countries = {c for c, _ in votes}
    print(f"Raw rows: {raw_rows}  Deduped rows: {len(votes)}  "
          f"Countries with usable state data: {len(countries)}  Conflicts resolved: {conflicts}")
    print(f"Refreshed {dest}")

    for tmp_file in tmpdir.glob("*"):
        tmp_file.unlink()
    tmpdir.rmdir()


def stamp(success):
    today = date.today().isoformat()
    meta = read_meta()
    if success:
        meta["downloaded_at"] = today
    meta["last_attempt"] = today
    meta["last_attempt_ok"] = success
    write_meta(meta)

    dest = KNOWLEDGE_DIR / "LAST_REFRESHED.txt"
    with open(dest, "w", encoding="utf-8") as f:
        f.write(f"Knowledge data last {'refreshed' if success else 'refresh attempt (FAILED)'}: {today}\n")
        f.write("Refreshed by: scripts/refresh_knowledge.py (auto-triggered by cache_manager.py "
                "when stale, or run manually)\n")
        f.write("Not refreshed by this script: india_pincode_state_map.csv, "
                "india_post_directory_source.csv (India Post), "
                "mauritius_post_office_codes.csv (user-supplied) -- replace by hand if a fresher copy exists.\n")
    print(f"Stamped {dest} (success={success})")


if __name__ == "__main__":
    ok = False
    try:
        refresh_country_info()
        refresh_postal_map()
        ok = True
    finally:
        stamp(ok)
        LOCK_PATH.unlink(missing_ok=True)
