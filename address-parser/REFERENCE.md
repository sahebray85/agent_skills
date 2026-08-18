# address-parser: algorithm and knowledge-base reference

## Signal model

Every parse combines up to three independent signals, computed in `AddressParser`:

- **Phone dial-code** (`dial_isos_from_phone`): the phone's leading digits,
  matched against every country's dial code from `geonames_country_info.txt`
  (longest-prefix-first). A bare `+1` maps to `["US", "CA"]` specifically --
  NANP has ~20 member territories sharing `+1`, and without a real area-code
  table there's no way to pick further; US/CA are the dominant real-world
  case for this pair.
- **Country-name keyword** (`keyword_isos_in`): the country's own name (or a
  known alias -- `NAME_ALIASES` in core.py) found in the address text.
  Names/aliases of 3 characters or fewer (`UK`, `US`, `IN`...) are matched
  **case-sensitively** only -- matched case-insensitively, `"in"` (the
  English preposition) would false-positive on nearly every address.
- **Format shape**: whether the extracted candidate's shape (digits only,
  vs. containing letters) matches a real, known postal-code pattern for a
  candidate country, AND the extracted value exists as a real key in
  `knowledge/global_postal_code_map.csv` (or the India/Mauritius overrides).

## Why some countries need corroboration and others don't

Countries are classified **empirically**, not by looking at the human-
readable format string: `core.py` tests each country's *original, anchored*
GeoNames regex against synthetic all-digit strings of length 3-10. If any
of them fully match, the format can produce a bare-digit result and is
classified `digit` (needs phone or keyword corroboration before being
attempted). Otherwise it's `alpha` (self-gating -- attempted unconditionally,
gated only by shape + map validation).

This matters because the naive alternative -- checking for a literal `@`
(letter placeholder) in the format string -- is wrong for real cases:
Argentina's official format is `@####@@@`, but the leading and trailing
letters are *optional* in the actual regex (`^[A-Z]?\d{4}[A-Z]{0,3}$`), so a
plain 4-digit string satisfies it. Classifying Argentina as self-gating on
the `@` alone let a coincidental digit sequence from an unrelated
US 5+-digit ZIP falsely validate as an Argentine postal code during this
skill's own testing -- exactly the class of bug documented below.

`config.yaml`'s `country_overrides` can force a country either direction:
- `AE` (UAE) is forced to `always_require_corroboration` even though its
  format looks ordinary -- its postal data is a synthetic Makani-style grid
  code, not a real postal system.
- `IN` (India) is forced to `self_gating` even though its format is pure
  digits. India's map is an unusually complete, authoritative 165K-row
  India Post directory, so a bare 6-digit match validating against it is
  safe. This override exists because of a real case found during this
  skill's validation: a genuinely Indian address (Kochi, Kerala) paired
  with a `+1` NANP phone number -- the mirror image of the Sharanaya
  Boutique dataset's own documented P2-37 pattern (a fake-looking Indian
  phone masking a real foreign address). Requiring corroboration for India
  would have silently failed this and every case like it.

## The contradiction guard

Every accepted match is checked against `keyword_isos_in(address1)`: if the
text names a country other than the one that matched, the match is dropped
rather than trusted (`check_contradiction`). This generalizes a bug found
and fixed in the Sharanaya Boutique project this knowledge base came from:
a French customer's Paris arrondissement code (`75013`) is *also* a real
Texas ZIP, and a phone-only signal let it resolve as Texas. Generalizing
the country-keyword table to all ~250 countries (instead of a hand-picked
`FR`/`DE` blocklist) means this guard now applies uniformly, and also means
France itself can now resolve correctly when its own name is in the text
(previously excluded entirely as "no data available", which turned out to
be wrong -- France has real rows in the postal map, it just was never on
the old system's hand-curated country list).

## Known limitations (found during this skill's own validation, not fixed)

- **Extraction only sees the strict, official GeoNames regex.** Real
  addresses sometimes insert stray whitespace mid-code (a Canadian postcode
  typed as `K2 J0 N 6` instead of `K2J 0N6`). The official regex tolerates
  at most one optional space in the right place, so this specific shape of
  messiness isn't extracted. `candidates_for()` recovers the analogous
  no-space case (`D15X4Y0` for Ireland) via prefix variants, but doesn't
  attempt a fully whitespace-tolerant re-scan. Trade-off accepted in favor
  of using the authoritative per-country regex for the other ~120
  countries rather than hand-tuning one more.
- **A historical pincode/state/countryCode value isn't always re-derivable
  from address1 alone.** If a downstream pipeline lets a human hand-correct
  a lookup column directly (bypassing the source address text) — the
  Sharanaya Boutique project's own workflow did exactly this — a fresh
  reparse of address1 can legitimately return blank even though the
  original file has a value, because the evidence for that value was never
  in address1 to begin with. This isn't a bug to chase; enrich_csv.py's
  fill-only-when-blank rule means it's harmless (an already-filled value is
  never touched).

## Output schema (`AddressParser.parse()`)

```json
{
  "postalCode": "B20",
  "countryCode": "GB",
  "state": "England",
  "confidence": 75,
  "reasons": ["map-validated", "keyword-corroborated", "self-gating format"],
  "diagnostics": {"phone_isos": ["IN"], "keyword_isos": ["GB"]}
}
```
All fields blank/zero/empty when nothing could be safely determined --
never a guess. `confidence` is a relative ranking score (see
`config.yaml`'s `confidence_points`), not a probability.

## Knowledge files

| File | Source | Schema |
|---|---|---|
| `geonames_country_info.txt` | GeoNames countryInfo.txt | tab-separated, see file's own `#` header row |
| `global_postal_code_map.csv` | GeoNames allCountries.zip, deduped | `countryCode,postalCode,state` |
| `india_pincode_state_map.csv` | India Post directory, majority-voted | `pincode,state,countryCode` |
| `india_post_directory_source.csv` | India Post (raw, for regeneration) | `circlename,regionname,...,pincode,...,statename,...` |
| `mauritius_post_office_codes.csv` | user-supplied | `Locality,Sub_locality,Street,Code` |

See `scripts/refresh_knowledge.py` for how the first two are regenerated.
