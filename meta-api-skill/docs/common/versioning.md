# API Versioning — Specification

> **When to load**: You are choosing or bumping the Graph API version, or an old version is approaching end of life.

## Quick Reference
| Field | Value |
|---|---|
| Current version in this skill | `v26.0` (changelog entry dated 2026-07-29) |
| Soon-to-expire | `v21.0` end of life 2027-01-21 |
| Format | `https://graph.facebook.com/v26.0/<path>` |
| Lifetime | Each version available at least 2 years after release |
| On expiry | Calls to the expired version are redirected to the next oldest available version by default |
| Response header | `facebook-api-version` reports the version that served the call (unverified 2026-10-04: versioning page did not mention it) |

## Rules
1. Always put the version in the URL; make it a config value (`meta.graph.version`), not a literal in code.
2. Upgrade deliberately: read the changelog, run contract tests against the new version in staging, then flip config.
3. Unversioned calls get the oldest available version or an app default; avoid them.
4. Record the version used in logs for debugging field differences.

## Example
```
POST https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages
```

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| (none verified) | Expired version is redirected rather than rejected | Upgrade before EOL | No |
| 100 | Parameter removed/renamed in a version | Check changelog | No |

## Quirks and gotchas
- Webhook payload shape is not versioned by the URL; the app's webhook version in the dashboard governs it. Set it deliberately (webhook field versioning specifics unverified 2026-10-04).
- Fields can be added at any time within a version; parse leniently.
- A silent redirect after expiry can change behaviour with no code change, so watch the EOL calendar (v21.0: 2027-01-21).
- Version-dependent field removals noted in pages: `current_limit`/`old_limit` on `phone_number_quality_update` were slated for removal in February 2026.

## Sources (verified 2026-10-04)
- https://developers.facebook.com/docs/graph-api/guides/versioning (lifetime, redirect; content returned in German)
- Graph API changelog entries for v26.0 and v21.0 EOL (caller-verified; changelog page not re-fetched this run).
