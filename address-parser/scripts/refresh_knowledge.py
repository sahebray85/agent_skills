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

Run this periodically (there's no fixed schedule -- GeoNames' postal data
doesn't change often; a reasonable cadence is whenever a country you need
comes back with suspiciously stale or missing data). Writes a dated stamp
to knowledge/LAST_REFRESHED.txt so staleness is always visible without
having to check file mtimes.
"""
import csv
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
COUNTRY_INFO_URL = "https://download.geonames.org/export/dump/countryInfo.txt"
POSTAL_ZIP_URL = "https://download.geonames.org/export/zip/allCountries.zip"


def refresh_country_info():
    dest = KNOWLEDGE_DIR / "geonames_country_info.txt"
    urllib.request.urlretrieve(COUNTRY_INFO_URL, dest)
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
    conflicts = 0
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["countryCode", "postalCode", "state"])
        for (country, postal), counter in sorted(votes.items()):
            if len(counter) > 1:
                conflicts += 1
            state = counter.most_common(1)[0][0]
            writer.writerow([country, f'="{postal}"', state])

    countries = {c for c, _ in votes}
    print(f"Raw rows: {raw_rows}  Deduped rows: {len(votes)}  "
          f"Countries with usable state data: {len(countries)}  Conflicts resolved: {conflicts}")
    print(f"Refreshed {dest}")

    for tmp_file in tmpdir.glob("*"):
        tmp_file.unlink()
    tmpdir.rmdir()


def stamp():
    dest = KNOWLEDGE_DIR / "LAST_REFRESHED.txt"
    # Timestamp is passed by the caller (no wall-clock access in some
    # environments) -- if run interactively, just note "run manually".
    note = sys.argv[1] if len(sys.argv) > 1 else "unspecified date -- pass a date string as argv[1] next time"
    with open(dest, "w", encoding="utf-8") as f:
        f.write(f"Knowledge data last refreshed: {note}\n")
        f.write("Refreshed by: scripts/refresh_knowledge.py\n")
        f.write("Not refreshed by this script: india_pincode_state_map.csv, "
                "india_post_directory_source.csv (India Post), "
                "mauritius_post_office_codes.csv (user-supplied) -- replace by hand if a fresher copy exists.\n")
    print(f"Stamped {dest}")


if __name__ == "__main__":
    refresh_country_info()
    refresh_postal_map()
    stamp()
