# Integration Checklist — Specification

> **When to load**: Before go-live or code review of any WhatsApp Cloud API integration.

## Quick Reference
| Area | Must be true |
|---|---|
| Token | System user token in a secret store |
| Webhook | Verified, signature checked on raw bytes, 200 returned fast |
| Idempotency | Dedupe by wamid and (id,status) |
| Errors | Classified by code into buckets |
| Limits | Producer-side throttling, 131049/131056 deferral |
| Privacy | PII redacted, retention set |

## Checklist
### Setup
- [ ] `v26.0` configured via property; EOL calendar noted (v21.0: 2027-01-21)
- [ ] `<WABA_ID>` and `<PHONE_NUMBER_ID>` not confused
- [ ] Callback URL on CA-signed TLS; verify token configured
- [ ] App subscribed to required fields (`messages`, template, account fields)
### Webhooks
- [ ] `X-Hub-Signature-256` validated over raw bytes, constant-time compare
- [ ] Respond 200 before processing; async queue
- [ ] Unknown fields/types ignored without error; lenient JSON parsing
- [ ] Out-of-order statuses handled by a state machine
- [ ] Inbound media downloaded by id promptly (URL 5 min, webhook id 7 days)
- [ ] Opt-out keywords honoured and stored (`docs/workflows/inbound_chat_and_optout.md`)
### Sending
- [ ] Outside 24 h window use templates only (131047)
- [ ] Template name + language + parameter count validated pre-send
- [ ] wamid stored for status correlation; `biz_opaque_callback_data` used if needed
- [ ] Sync and async errors share one classifier (`errors.md`)
### Reliability
- [ ] Backoff with jitter on RETRY; none on AUTH/ACCOUNT/TEMPLATE/REJECTED
- [ ] 131049 deferred 24 h, 131056 deferred 1 h
- [ ] Per-number token bucket under throughput limit
- [ ] Tier changes consumed from `phone_number_quality_update`
- [ ] Template status/quality/category webhooks update local state
### Security and privacy
- [ ] Secrets never logged; `appsecret_proof` if "Require App Secret" is on
- [ ] Phone numbers masked in logs and metrics
- [ ] Raw payload TTL and erasure path defined

## Example
Smoke test: send a template to an allow-listed number, confirm `sent` -> `delivered` webhooks arrive with valid signatures, reply from the phone, confirm inbound `text` is parsed and the wamid is deduped on replay.

## Errors / failure modes
| Symptom | First check |
|---|---|
| No webhook events | Field subscription, app-to-WABA subscription, mode |
| Signature mismatch | Raw body, App Secret |
| 131047 | 24 h window |
| 132001 | Template name/language/approval |
| 131049 | Marketing cap, defer |

## Quirks and gotchas
- A passing sync response does not mean delivery.
- Test numbers and production behave differently (allow-lists, tiers).

## Sources (verified 2026-10-04)
Aggregates the other docs under `docs/webhooks/` and `docs/common/`; no new facts.
