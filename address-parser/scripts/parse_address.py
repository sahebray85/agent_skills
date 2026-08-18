#!/usr/bin/env python3
"""
Parse a single free-text address and print its best-supported
(postal code, state, country) as JSON.

    python parse_address.py "1007 231st PL NE, Sammamish, WA 98084" --phone +14257484493

Never guesses -- if nothing is corroborated (see core.py's module
docstring for the safety model), postalCode/state/countryCode come back
blank rather than a low-confidence guess. That's by design: a blank field
in a downstream system is obviously "needs review"; a wrong one silently
isn't.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import AddressParser  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("address", help="Free-text address, any format/language layout")
    ap.add_argument("--phone", default="", help="E.164 or raw phone number, optional but improves accuracy")
    args = ap.parse_args()

    parser = AddressParser()
    result = parser.parse(args.address, args.phone)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
