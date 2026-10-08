# Configuration Reference — Specification

> **When to load**: You are defining properties, environment variables and secrets for a WhatsApp Cloud API integration.

## Quick Reference
| Property (example) | Env var | Secret? | Notes |
|---|---|---|---|
| `meta.graph.base-url` | `META_GRAPH_BASE_URL` | no | Default `https://graph.facebook.com` |
| `meta.graph.version` | `META_GRAPH_VERSION` | no | `v26.0` |
| `meta.waba-id` | `META_WABA_ID` | no | `<WABA_ID>` |
| `meta.phone-number-id` | `META_PHONE_NUMBER_ID` | no | `<PHONE_NUMBER_ID>` |
| `meta.access-token` | `META_ACCESS_TOKEN` | yes | `<TOKEN>`, system user |
| `meta.app-secret` | `META_APP_SECRET` | yes | `<APP_SECRET>`; webhook HMAC and `appsecret_proof` |
| `meta.webhook.verify-token` | `META_WEBHOOK_VERIFY_TOKEN` | yes | Chosen by you |
| `meta.require-app-secret-proof` | `META_APP_SECRET_PROOF` | no | Match dashboard toggle |
| `meta.timeouts.connect/read` | | no | e.g. 3 s / 10 s |
| `meta.retry.max-attempts` / `base-delay` | | no | See `errors.md` |
| `meta.throughput.per-number-mps` | | no | Below your tier (default 80 mps, unverified) |
| `meta.media.download-dir` / `max-bytes` | | no | Limits in `inbound_messages.md` |

## Example (Spring YAML)
```yaml
meta:
  graph:
    base-url: https://graph.facebook.com
    version: v26.0
  waba-id: ${META_WABA_ID}
  phone-number-id: ${META_PHONE_NUMBER_ID}
  access-token: ${META_ACCESS_TOKEN}
  app-secret: ${META_APP_SECRET}
  webhook:
    verify-token: ${META_WEBHOOK_VERIFY_TOKEN}
```
Secrets come from AWS Secrets Manager in production, never from files in git.

## Errors / failure modes
| Symptom | Likely config cause | Action |
|---|---|---|
| 190/0 | Stale `access-token` | Rotate |
| Webhook verify fails | `verify-token` mismatch | Align with dashboard |
| Signature mismatch | Wrong `app-secret` (other app / rotated) | Update secret |
| 131030 or 131037 | Test number or no display name | Dashboard setup |
| 100 on send | Wrong `phone-number-id` vs `waba-id` | Do not swap them |

## Quirks and gotchas
- Fail startup if a required secret is blank; fail loudly, never default.
- Use separate apps/tokens per environment; dev numbers can only message allow-listed recipients.
- Version must be configurable (see `versioning.md`).
- Placeholders in docs are never real values.

## Sources (verified 2026-10-04)
Derived from the other docs in this skill: `auth.md`, `versioning.md`, `rate_limits.md`; engineering convention, not a Meta page.
