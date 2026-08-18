---
name: address-parser
description: Parses free-text addresses in any country/format to extract postal code, state/region, and ISO country code, using deterministic lookup against a GeoNames-derived global knowledge base plus India Post and Mauritius directories -- never guesses, returns blank when nothing is safely corroborated. Use when asked to extract, validate, or enrich a pincode/ZIP/postcode/state/country from address text or a CSV of address records, or to write Java code that does the same.
---

# address-parser

Deterministic, explainable postal-code/state/country extraction. No LLM
guessing and no vector/semantic search -- every result is either a real
key in `knowledge/global_postal_code_map.csv` (or the India/Mauritius
overrides) or blank. See [REFERENCE.md](REFERENCE.md) for the full
signal/safety model before changing any matching logic.

## Quick start

Single address:

```bash
python scripts/parse_address.py "91 Leopold Avenue, Birmingham, B20 1EX, UK" --phone +447393873459
```

Returns JSON: `postalCode`, `state`, `countryCode`, `confidence`, `reasons`,
and `diagnostics` (which signals fired). All fields come back blank rather
than a low-confidence guess when nothing is corroborated -- a blank field
reads as "needs review" downstream; a wrong one silently doesn't.

Batch CSV:

```bash
python scripts/enrich_csv.py customers.csv customers_enriched.csv \
    --address-col address1 --phone-col primaryPhone
```

Fill-only-when-blank: a row whose `pincode` column already has a value is
never touched, even if re-parsing today would produce something different.
Prints a structural validation block (row count, and a hard check that no
previously-present value was cleared or altered) every run.

## How matching works, briefly

1. Collect signals: the phone's dial code, and any country name/alias
   found in the address text (`knowledge/geonames_country_info.txt`
   supplies both names and dial codes).
2. Letter-containing postal formats (UK, Canada, Ireland, ...) are tried
   unconditionally -- their shape plus a real map hit is enough. Pure-digit
   formats (US, India, Australia, ...) are only tried when a signal from
   step 1 supports that specific country -- otherwise a coincidental digit
   match from an unrelated country can and did produce a wrong answer (see
   REFERENCE.md's Argentina/Texas incidents).
3. Every match is checked against the address text for a *different*,
   explicitly-named country before being accepted.

`config.yaml` holds the tunable knobs (confidence scoring, per-country
overrides like India's or UAE's) -- edit that, not the matching logic in
`scripts/core.py`, to retune behavior.

## Refreshing the knowledge base

Automatic, stale-while-revalidate: every `AddressParser()` construction
checks `knowledge/cache_meta.json`'s `downloaded_at` against
`config.yaml`'s `knowledge_cache.expiry_days` (60 by default). Past that,
it kicks off `refresh_knowledge.py` as a fully detached background
subprocess and immediately continues using the **existing** knowledge
files -- a refresh never blocks a parse or a batch run. The subprocess
downloads to temp files and atomically swaps them in, so a concurrent
read never sees a half-written file; only the *next* invocation, after
the swap, sees the fresh data. A lock file prevents piling up duplicate
downloads if several invocations happen while one is already running.

You normally never need to run anything by hand. To force an immediate
refresh anyway: `python scripts/refresh_knowledge.py`. Check
`knowledge/LAST_REFRESHED.txt` or `cache_meta.json` for when this last
happened, and `knowledge/refresh_last_run.log` for the most recent run's
output. See the script's own docstring for what it does and doesn't cover
(India Post and Mauritius data have no auto-refresh source).

## Writing Java

If asked for a Java implementation of any part of this (a validator, a
knowledge-file loader, a full port), see
[JAVA_REFERENCE.md](JAVA_REFERENCE.md) -- generate fresh from `core.py`
each time rather than reusing Java from an earlier conversation.
