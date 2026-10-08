# Logging and Privacy — Specification

> **When to load**: You are adding logs, metrics, audit records or retention for WhatsApp traffic, or handling erasure requests.

## Quick Reference
| Item | Rule |
|---|---|
| Never log | Access token, App Secret, verify token, `appsecret_proof`, full webhook bodies at INFO |
| Mask | Phone numbers (`wa_id`, `from`, `recipient_id`): keep last 2-4 digits |
| Always log | wamid, `phone_number_id`, template name+language, error `code`, `fbtrace_id`, HTTP status, correlation id |
| PII in payloads | `contacts[].profile.name`, message text, captions, locations, contact cards |
| Media | Treat downloaded media as personal data; encrypt at rest |
| Retention | Raw payloads: short TTL (e.g. 7-30 days); message state: per policy |

## Practices
1. Structured logging with a redaction filter applied centrally, not per call site.
2. Log status transitions by your own delivery or queue id, never by wamid (a wamid encodes the recipient's phone number) and never by content.
3. Store raw webhook payloads (for replay) in an encrypted store with TTL; keep out of general logs.
4. Hash or tokenize phone numbers for analytics.
5. Honour opt-outs: persist opt-out events with timestamp and source (see `docs/workflows/inbound_chat_and_optout.md`); this is consent evidence, keep per legal advice.
6. Support erasure: be able to delete a user's messages, media and profile name by `wa_id`.
7. Media ids from webhooks expire in 7 days and Meta stores media 30 days; if you need it longer, copy it to your own encrypted storage.

## Example (log line)
```
event=wa_status delivery_id=48213 status=failed code=131049 subcode= http=400 fbtrace=<TRACE_ID>
```
Not in the line: the wamid, the recipient (even masked), the template params, the body. Look the wamid up from `delivery_id` in your own store when you need it.
```
```

## Errors / failure modes
| Failure | Consequence | Action |
|---|---|---|
| Token in logs | Account takeover | Rotate token immediately |
| Full payload in logs | PII leak | Purge, add redaction |
| Signature failure logged with body | Attacker-controlled data in logs | Log header presence and source IP only |

## Quirks and gotchas
- Error `message` and `error_data.details` can embed phone numbers; run them through the redactor.
- Log injection: message text is user-controlled; encode newlines.
- Metrics labels must not contain phone numbers (cardinality and PII).
- Legal retention and consent rules depend on jurisdiction (India DPDP, GDPR); legal specifics are outside what this skill verified (unverified 2026-10-04).

## Sources (verified 2026-10-04)
- Media retention and expiry: .../business-phone-numbers/media (7-day webhook media id, 30-day storage)
- Webhook payload field lists: pages under `docs/webhooks/`
- Privacy guidance is general engineering practice, not a Meta page.
