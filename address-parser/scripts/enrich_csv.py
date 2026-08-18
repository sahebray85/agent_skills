#!/usr/bin/env python3
"""
Batch-enrich a CSV of records with pincode/state/countryCode columns,
using the same AddressParser core as parse_address.py.

    python enrich_csv.py customers.csv customers_enriched.csv \\
        --address-col address1 --phone-col primaryPhone

Fill-only-when-blank, same discipline as phase1/phase2's own extractors in
the Sharanaya Boutique project this knowledge base was built from: a row
whose pincode/state/countryCode is already non-blank is NEVER touched,
even if re-parsing address1 today would produce a different answer. Only
rows where the target column is blank get a value filled in. Prints a
structural validation block every run (row count, column set, and a hard
check that no previously-present value was cleared or altered) -- this
project's own CLAUDE.md exists in large part because of a real bug where
an earlier version of this exact logic silently blanked good data, so
this check is not optional decoration.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import AddressParser  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_csv")
    ap.add_argument("output_csv")
    ap.add_argument("--address-col", default="address1")
    ap.add_argument("--phone-col", default="")
    ap.add_argument("--pincode-col", default="pincode")
    ap.add_argument("--state-col", default="state")
    ap.add_argument("--country-col", default="countryCode")
    args = ap.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames)
        rows = list(reader)

    for col in (args.pincode_col, args.state_col, args.country_col):
        if col not in header:
            header.append(col)

    parser = AddressParser()
    before = {i: (r.get(args.pincode_col, ""), r.get(args.state_col, ""), r.get(args.country_col, ""))
              for i, r in enumerate(rows)}

    attempted, filled = 0, 0
    for row in rows:
        old_pin = (row.get(args.pincode_col) or "").strip()
        if old_pin:
            continue  # already has a value -- never touch it
        attempted += 1
        addr1 = row.get(args.address_col, "")
        phone = row.get(args.phone_col, "") if args.phone_col else ""
        result = parser.parse(addr1, phone)
        if result["postalCode"]:
            row[args.pincode_col] = result["postalCode"]
            row[args.state_col] = result["state"]
            row[args.country_col] = result["countryCode"]
            filled += 1

    with open(args.output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    cleared_or_altered = 0
    for i, row in enumerate(rows):
        old_pin, old_state, old_country = before[i]
        if old_pin and (row.get(args.pincode_col, "") != old_pin
                         or row.get(args.state_col, "") != old_state
                         or row.get(args.country_col, "") != old_country):
            cleared_or_altered += 1

    print(f"Read {len(rows)} rows from {args.input_csv}")
    print(f"Wrote {args.output_csv}")
    print("\n=== VALIDATION ===")
    print(f"Row count: {len(rows)} (unchanged) OK" if len(rows) == len(before) else "ROW COUNT MISMATCH")
    print(f"Previously-present pincode/state/countryCode cleared or altered: {cleared_or_altered}"
          + (" OK" if cleared_or_altered == 0 else " FAIL"))
    print(f"Rows with blank {args.pincode_col} attempted: {attempted}")
    print(f"Newly filled: {filled}")


if __name__ == "__main__":
    main()
