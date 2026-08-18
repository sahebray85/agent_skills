# Generating Java from this skill

There is no maintained Java port of this logic. When asked to write Java
that validates, parses, or loads this skill's postal-code knowledge,
generate it fresh from the Python source of truth (`scripts/core.py`) each
time -- don't reuse Java written in a previous conversation, since
`core.py` may have changed since. This keeps exactly one implementation
that can drift out of sync: none.

## What to translate

Read `scripts/core.py` and `REFERENCE.md` first. The pieces most often
worth generating:

1. **A postal-code format validator** for one specific country -- port
   that country's regex straight from `knowledge/geonames_country_info.txt`
   (column 15, the `postal_regex` field). Don't hand-write a new regex from
   memory; copy the exact pattern so behavior matches the Python side.
2. **A knowledge-file loader** -- `global_postal_code_map.csv` /
   `india_pincode_state_map.csv` / `mauritius_post_office_codes.csv` as
   classpath resources, loaded into a `Map<String, Map<String, String>>`
   keyed the same way as `core.py`'s `postal_map` (`countryCode ->
   postalCode -> state`). Remember the CSV's postal-code column is
   Excel-safe-wrapped (`="12345"`) -- strip the `="..."` wrapper on load,
   same as `load_postal_map()` does.
3. **The gating/corroboration decision** -- port `determine_country_candidates`
   and `corroboration_strength` faithfully, including: the empirical
   digit-vs-alpha classification (test the country's own regex against
   synthetic all-digit strings, don't infer from the `@`/`#` format
   string), the `config.yaml` country overrides, and the contradiction
   guard (`check_contradiction`). Skipping any one of these three
   reintroduces a real bug this skill's Python side already found and
   fixed (see REFERENCE.md's "Known limitations" / "Why some countries
   need corroboration" sections) -- don't simplify them away for brevity.

## Context for the Sharanaya Boutique backend specifically

If the request is about the `POST /v1/customers` Java backend this
knowledge base originated from: enums there are case-sensitive
(`channel=PHONE`, `contactType=WHATSAPP|MOBILE`, `customerType=INDIVIDUAL`,
`status=ACTIVE`), `id` and `fullAddress` are never populated client-side,
and `sex` is inferred from salutation only, never from a name -- these are
project conventions, not part of this skill's own logic, but relevant if
the generated Java is meant to plug into that specific backend.

## What NOT to do

- Don't generate a Java regex engine port of a Python regex that uses
  Python-only syntax -- GeoNames' `postal_regex` field is already
  vanilla-enough for both `re` and `java.util.regex.Pattern`; sanity-check
  the one you're porting compiles under both rather than assuming.
- Don't invent a "cleaner" simplified regex for a country when the real
  GeoNames one is available -- the whole point of using the authoritative
  source (see REFERENCE.md) was to stop hand-rolling per-country patterns
  that turn out to have edge cases (the Argentina optional-letter bug).
