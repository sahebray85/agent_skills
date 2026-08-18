"""
Shared address-parsing core for the address-parser skill.

Given a free-text address (optionally paired with a phone number for extra
corroboration), returns the best-supported (postal_code, state, countryCode)
triple, or blanks if nothing can be safely determined.

SAFETY MODEL (read this before changing anything):

1. A postal-code-shaped substring is only ever ACCEPTED if it also exists as
   a real key in knowledge/global_postal_code_map.csv (or the India/Mauritius
   overrides) for that specific country. Format-matching alone never wins --
   this is what makes it safe to attempt a country's pattern speculatively.

2. Countries whose postal-code format is pure digits (e.g. India, US, AU)
   are "unsafe alone" -- the same 5-6 digit shape recurs across many
   countries, so a coincidental cross-country collision is possible (this
   bit a real customer once: a Paris arrondissement code, 75013, is also a
   real Texas ZIP). These are only attempted when something else in the row
   corroborates the country: the phone number's dial code, or the country's
   own name appearing in the address text.

3. Countries whose postal-code format includes letters (e.g. UK, Canada,
   Ireland) are distinctive enough on their own -- attempted unconditionally,
   self-gated by shape + map validation.

4. Every accepted match is re-checked against the address text for an
   explicit, different country name -- if the text plainly says "France"
   but the winning match is a digit-country guess, the guess is dropped
   rather than trusted (see check_contradiction()).

Format/classification data (which shape each country's postal code has, and
the regex to extract it) comes straight from GeoNames' own reference file
(knowledge/geonames_country_info.txt) -- the same source the postal lookup
map itself was built from, so the ISO-3166 codes always agree.

A country can have a perfectly good format/regex here and still never
resolve anything, if knowledge/global_postal_code_map.csv has zero rows for
it (no real postal-code data was ever found for that country in GeoNames'
export) -- Saudi Arabia is a concrete example: SA has a real format entry
("#####") but zero rows in the postal map, so it will never match until a
real Saudi source (like the Mauritius file) is supplied.
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    from cache_manager import maybe_trigger_background_refresh
except ImportError:
    def maybe_trigger_background_refresh(config):
        return False

SKILL_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = SKILL_DIR / "knowledge"
CONFIG_PATH = SKILL_DIR / "config.yaml"

COUNTRY_INFO_PATH = KNOWLEDGE_DIR / "geonames_country_info.txt"
GLOBAL_MAP_PATH = KNOWLEDGE_DIR / "global_postal_code_map.csv"
INDIA_MAP_PATH = KNOWLEDGE_DIR / "india_pincode_state_map.csv"
MAURITIUS_SOURCE_PATH = KNOWLEDGE_DIR / "mauritius_post_office_codes.csv"
PHONE_PREFIX_PATH = KNOWLEDGE_DIR / "phone_country_prefixes.csv"

# Country-name aliases real address text uses that GeoNames' own "Country"
# column doesn't (colloquial names, sub-nation names, old names). Extend
# this deliberately when a real address is found using one -- don't guess
# ahead of evidence, same discipline as the rest of this knowledge base.
NAME_ALIASES = {
    "usa": "US", "america": "US",
    "uk": "GB", "britain": "GB", "great britain": "GB",
    "england": "GB", "scotland": "GB", "wales": "GB", "northern ireland": "GB",
    "holland": "NL",
    "uae": "AE", "dubai": "AE", "abu dhabi": "AE",
    "burma": "MM",
    "ivory coast": "CI",
    "south korea": "KR", "north korea": "KP",
    "russia": "RU",
    "vietnam": "VN",
}

# Short tokens (<=3 chars) are only trusted as a country signal when they
# appear in the text in this EXACT case -- "us"/"in" are common English
# words and would false-positive constantly if matched case-insensitively.
# Mirrors the case-sensitive US-state-abbreviation guard already proven
# necessary in phase2/enrich_pincode_global.py this session.
SHORT_TOKEN_MAXLEN = 3


def _clean_digits(s):
    return re.sub(r"\D", "", s or "")


def load_config():
    defaults = {
        "require_corroboration_for_digit_formats": True,
        "knowledge_cache": {
            "expiry_days": 60,
            "auto_refresh": True,
        },
        "confidence_points": {
            "map_validated": 40,
            "phone_corroborated": 20,
            "keyword_corroborated": 20,
            "alpha_format_self_gated": 15,
            "contradiction_penalty": -100,
        },
        "country_overrides": {
            # iso2 -> "always_require_corroboration" | "never_attempt"
            # e.g. AE's postal data is synthetic Makani-style, not a real
            # postal system -- keep requiring corroboration even though a
            # future GeoNames refresh might otherwise reclassify it.
            "AE": "always_require_corroboration",
        },
    }
    if yaml is None or not CONFIG_PATH.exists():
        return defaults
    with open(CONFIG_PATH, encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    defaults.update(loaded)
    return defaults


def load_country_info():
    """iso2 -> {name, dial, fmt, regex, is_digit_format, pattern}"""
    countries = {}
    with open(COUNTRY_INFO_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 15:
                continue
            iso2, name, dial, fmt, regex = cols[0], cols[4], cols[12], cols[13], cols[14]
            if not fmt or not regex:
                continue  # country has no postal-code concept at all
            pattern = None
            is_digit_format = True
            try:
                anchored = re.compile(regex.strip(), re.IGNORECASE)
                # Don't trust the '@' (letter placeholder) in the human
                # format string alone -- some countries' letter positions
                # are OPTIONAL in the real regex (Argentina's leading/
                # trailing letters are both `?`/`{0,3}`), so a pure-digit
                # string still satisfies them. Empirically test: if any
                # plausible all-digit length fully matches the ORIGINAL
                # anchored regex, this format can produce a bare-digit
                # match and must be treated as needing corroboration,
                # regardless of what the format string suggests.
                is_digit_format = any(anchored.fullmatch("1" * n) for n in range(3, 11))
                # Strip anchors for extraction: search anywhere in the
                # address text instead of requiring the whole string to be
                # just the postal code.
                body = regex.strip()
                body = re.sub(r"^\^", "", body)
                body = re.sub(r"\$$", "", body)
                pattern = re.compile(body, re.IGNORECASE)
            except re.error:
                pattern = None
            countries[iso2] = {
                "name": name, "dial": dial, "fmt": fmt, "regex": regex,
                "is_digit_format": is_digit_format, "pattern": pattern,
            }
    return countries


def build_name_to_iso2(country_info):
    mapping = {}
    for iso2, info in country_info.items():
        mapping[info["name"].lower()] = iso2
    for alias, iso2 in NAME_ALIASES.items():
        mapping[alias] = iso2
    return mapping


def build_dialcode_to_iso2(country_info):
    """numeric dial-code string -> list of candidate iso2s, longest-prefix first."""
    by_code = defaultdict(list)
    for iso2, info in country_info.items():
        code = _clean_digits(info["dial"])
        if code:
            by_code[code].append(iso2)
    return by_code


def load_postal_map(country_info):
    """iso2 -> {postalCode: state}, then IN/MU overridden by dedicated sources."""
    gmap = defaultdict(dict)
    if GLOBAL_MAP_PATH.exists():
        with open(GLOBAL_MAP_PATH, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                iso2 = row["countryCode"]
                pc = row["postalCode"].strip('="')
                gmap[iso2][pc] = row["state"]

    # India: prefer the India Post directory-derived map -- more complete
    # and more accurate than GeoNames' own sparse IN rows.
    if INDIA_MAP_PATH.exists():
        gmap["IN"] = {}
        with open(INDIA_MAP_PATH, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                pc = row["pincode"].strip('="')
                gmap["IN"][pc] = row["state"]

    # Mauritius: GeoNames has zero usable rows for MU (confirmed this
    # session) -- entirely sourced from the user-supplied local file.
    if MAURITIUS_SOURCE_PATH.exists():
        counts = defaultdict(lambda: defaultdict(int))
        with open(MAURITIUS_SOURCE_PATH, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                code = (row.get("Code") or "").strip()
                locality = (row.get("Locality") or "").strip()
                if code and locality:
                    counts[code][locality] += 1
        gmap["MU"] = {code: max(loc_counts, key=loc_counts.get)
                      for code, loc_counts in counts.items()}
    return gmap


class AddressParser:
    def __init__(self):
        self.config = load_config()
        if maybe_trigger_background_refresh(self.config):
            print("address-parser: knowledge cache is stale, refreshing in the "
                  "background (this run still uses the current data)", file=sys.stderr)
        self.country_info = load_country_info()
        self.name_to_iso2 = build_name_to_iso2(self.country_info)
        self.dialcode_to_iso2 = build_dialcode_to_iso2(self.country_info)
        self.postal_map = load_postal_map(self.country_info)
        self._dial_codes_by_len = sorted(self.dialcode_to_iso2, key=len, reverse=True)

    # ---- signal detection -------------------------------------------------

    def dial_isos_from_phone(self, phone):
        digits = _clean_digits(phone).lstrip("0")
        if not digits:
            return []
        if digits.startswith("1"):
            return ["US", "CA"]  # NANP: dominant real-world case, not fully decodable without area codes
        for code in self._dial_codes_by_len:
            if digits.startswith(code) and code != "1":
                return list(self.dialcode_to_iso2[code])
        return []

    def keyword_isos_in(self, text):
        text = text or ""
        hits = set()
        for name, iso2 in self.name_to_iso2.items():
            if len(name) <= SHORT_TOKEN_MAXLEN:
                pat = r"\b" + re.escape(name.upper()) + r"\b"
                if re.search(pat, text):  # case-sensitive on purpose
                    hits.add(iso2)
            else:
                pat = r"\b" + re.escape(name) + r"\b"
                if re.search(pat, text, re.IGNORECASE):
                    hits.add(iso2)
        return hits

    # ---- candidate extraction ---------------------------------------------

    def candidates_for(self, iso2, text):
        """Each match yields several key VARIANTS to try against the map,
        most-specific first: the full matched code as-is, with internal
        whitespace collapsed, with whitespace removed entirely, and just
        the first whitespace-separated token (the "outward code"/FSA
        convention some existing map data was built with, e.g. GB stores
        "B20" not "B20 1EX", CA stores "P7B" not "P7B 6J5"). Trying all
        variants means this works regardless of which granularity a given
        knowledge-map refresh happened to store."""
        info = self.country_info.get(iso2)
        if not info or not info["pattern"]:
            return []
        # Outer order: last-in-text match first (trailing zip/postcode
        # convention). Inner order, PER match: most-specific variant
        # first -- callers take the first validated hit, so within one
        # match a short accidental prefix (e.g. "B2") must never be
        # preferred over the fuller, correct code ("B20") just because
        # it also happens to validate against the map.
        out = []
        matches = list(info["pattern"].finditer(text or ""))
        for m in reversed(matches):
            raw = m.group(0).strip().upper()
            collapsed = re.sub(r"\s+", " ", raw)
            no_space = re.sub(r"\s+", "", raw)
            first_token = collapsed.split(" ")[0]
            variants = [collapsed, no_space, first_token]
            if not info["is_digit_format"]:
                # Alphanumeric formats often have a short area/routing-key
                # PREFIX that's all our map has state-level data for (e.g.
                # Ireland's Eircode "D15X4Y0" -> map key "D15"), and real
                # addresses often omit the separating space entirely
                # ("D15X4Y0", not "D15 X4Y0"), so whitespace-splitting
                # alone can't find it. Longest prefix first -- most
                # specific still wins if multiple prefix lengths validate.
                # Only tried for letter-containing formats -- a short
                # numeric prefix risks colliding with an unrelated
                # country's own full-length numeric code.
                variants += [no_space[:4], no_space[:3], no_space[:2]]
            for variant in variants:
                if variant and variant not in out:
                    out.append(variant)
        return out

    def determine_country_candidates(self, phone, address1):
        phone_isos = set(self.dial_isos_from_phone(phone))
        keyword_isos = self.keyword_isos_in(address1)
        overrides = self.config.get("country_overrides", {})

        digit_isos_available = {iso for iso, info in self.country_info.items()
                                 if info["is_digit_format"]}
        alpha_isos_available = {iso for iso, info in self.country_info.items()
                                 if not info["is_digit_format"]}

        for iso, action in overrides.items():
            if action == "always_require_corroboration":
                alpha_isos_available.discard(iso)
                digit_isos_available.add(iso)
            elif action == "self_gating":
                digit_isos_available.discard(iso)
                alpha_isos_available.add(iso)
            elif action == "never_attempt":
                digit_isos_available.discard(iso)
                alpha_isos_available.discard(iso)

        digit_from_phone = phone_isos & digit_isos_available
        digit_from_keyword = keyword_isos & digit_isos_available
        digit_candidates = digit_from_phone | digit_from_keyword

        # alpha formats only need to be present in our knowledge base to
        # attempt -- shape + map-validation is enough gating on its own.
        alpha_candidates = alpha_isos_available & set(self.postal_map)

        candidates = sorted(alpha_candidates | (digit_candidates & set(self.postal_map)))
        diagnostics = {
            "phone_isos": sorted(phone_isos),
            "keyword_isos": sorted(keyword_isos),
        }
        return candidates, diagnostics

    def check_contradiction(self, matched_iso2, address1):
        """True if the text plainly names a DIFFERENT country than the match."""
        named = self.keyword_isos_in(address1)
        others = named - {matched_iso2}
        return sorted(others) if others else []

    # ---- top-level entry point ---------------------------------------------

    def parse(self, address1, phone=None):
        candidates, diag = self.determine_country_candidates(phone, address1 or "")
        points = self.config["confidence_points"]
        # Try independently-corroborated candidates (phone dial-code and/or
        # a country-name keyword actually found in the text) before
        # falling back to a self-gated-only alpha-format match. Without
        # this, an alphabetically-early self-gated country can coincidentally
        # validate against the map (e.g. "TA14" inside an email address
        # happens to be a real UK postcode) and win over the genuinely
        # corroborated country purely on alphabetical luck.
        def corroboration_strength(iso2):
            return (iso2 in diag["phone_isos"]) + (iso2 in diag["keyword_isos"])
        candidates = sorted(candidates, key=lambda iso2: (-corroboration_strength(iso2), iso2))
        for iso2 in candidates:
            for cand in self.candidates_for(iso2, address1):  # already ordered: last-in-text, most-specific first
                if cand in self.postal_map.get(iso2, {}):
                    contradictions = self.check_contradiction(iso2, address1)
                    if contradictions:
                        continue  # text names a different country -- don't trust this guess
                    score = points["map_validated"]
                    reasons = ["map-validated"]
                    if iso2 in diag["phone_isos"]:
                        score += points["phone_corroborated"]
                        reasons.append("phone-corroborated")
                    if iso2 in diag["keyword_isos"]:
                        score += points["keyword_corroborated"]
                        reasons.append("keyword-corroborated")
                    if not self.country_info[iso2]["is_digit_format"]:
                        score += points["alpha_format_self_gated"]
                        reasons.append("self-gating format")
                    return {
                        "postalCode": cand, "countryCode": iso2,
                        "state": self.postal_map[iso2][cand],
                        "confidence": score, "reasons": reasons,
                        "diagnostics": diag,
                    }
        return {
            "postalCode": "", "countryCode": "", "state": "",
            "confidence": 0, "reasons": ["no corroborated match"],
            "diagnostics": diag,
        }
