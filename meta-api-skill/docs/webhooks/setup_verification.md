# Webhook Setup and Verification — Specification

> **When to load**: You are configuring the callback URL, verify token, field subscriptions, or debugging why Meta says the webhook cannot be verified or stops delivering.

## Quick Reference
| Field | Value |
|---|---|
| Verification request | `GET <callback>?hub.mode=subscribe&hub.verify_token=<TOKEN>&hub.challenge=<INT>` |
| Verification response | HTTP 200, body = the `hub.challenge` value only (plain text) |
| Event delivery | `POST` JSON, header `X-Hub-Signature-256: sha256=<hex>` |
| Webhook object | `whatsapp_business_account` |
| Required TLS | Valid certificate (self-signed not accepted) |
| Expected response to POST | HTTP 200, fast, empty body is fine |
| Retry on non-200 | Immediately, then with decreasing frequency over 36 h (Graph webhooks page); WhatsApp overview page says up to 7 days. Both are documented; plan for the longer window |
| Batching | Up to 1000 updates may arrive in one POST |
| Subscribe call | `POST https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps` (unverified 2026-10-04, standard Cloud API step) |

## Setup steps
1. Create a public HTTPS endpoint with a CA-signed certificate. It must answer both GET (verification) and POST (events) on the same URL.
2. In the Meta App Dashboard, WhatsApp > Configuration, set Callback URL and Verify Token. The verify token is a string you choose; keep it in config (see `docs/common/config.md`).
3. Meta sends the GET verification. Compare `hub.verify_token` with your configured value; if equal and `hub.mode == subscribe`, return 200 with `hub.challenge` as the raw body. Otherwise return 403.
4. Subscribe the app to the fields you need (at minimum `messages`). Subscribing fields in the dashboard does not by itself guarantee delivery for a WABA; ensure the app is subscribed to the WABA via `subscribed_apps` (unverified 2026-10-04).
5. Respond 200 to every POST before doing slow work. Persist the raw payload (or enqueue), then process asynchronously.

## Verification request
| Query param | Meaning |
|---|---|
| `hub.mode` | Always `subscribe` |
| `hub.verify_token` | The string you configured |
| `hub.challenge` | Integer-like string you must echo |

Note PHP-style frameworks rewrite dots to underscores (`hub_mode`); Spring `@RequestParam("hub.mode")` works as written.

## Example
```
GET /webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=<VERIFY_TOKEN>&hub.challenge=1158201444 HTTP/1.1

HTTP/1.1 200 OK
Content-Type: text/plain

1158201444
```

## Subscription fields (WhatsApp, 20 fields per overview page)
The overview page lists 20 fields; verified names used in this skill: `messages`, `message_template_status_update`, `message_template_quality_update`, `template_category_update`, `phone_number_quality_update`, `account_update`, `account_alerts`. Other fields: see the Meta page (names not re-verified here, unverified 2026-10-04). Subscribe only to what you handle; unknown fields must still be answered 200.

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| Dashboard "callback URL or verify token couldn't be validated" | Endpoint returned non-200, wrong body, or token mismatch | Return the challenge as plain text, not JSON-quoted; check token | Fix then re-save |
| TLS error | Self-signed, expired, or incomplete chain | Install full chain | Fix then re-save |
| Meta sees non-200 on POST | Your handler threw or timed out | Return 200 early, queue the work | Meta retries (see Quick Reference) |
| No events arriving | Field not subscribed, app not subscribed to WABA, app in dev mode with non-test numbers | Check subscriptions and app mode | n/a |
| Duplicate events | Retries or at-least-once delivery | Dedupe on `messages[].id` / `statuses[].id`+`status` | n/a |

## Quirks and gotchas
- Return the challenge exactly: no JSON quoting, no trailing HTML. A framework that serialises a String as JSON will add quotes and fail.
- Verification and event delivery share the URL; routing must split on HTTP method.
- Out-of-order delivery is normal: `read` can arrive before `delivered`. Never assume ordering.
- After prolonged failures Meta may disable the subscription; re-save the callback URL to re-verify.
- Do not log full payloads at INFO; they contain user phone numbers and message text (see `docs/common/logging_privacy.md`).
- Verify the signature before parsing JSON (see `signature_validation.md`).

## Sources (verified 2026-10-04)
- https://developers.facebook.com/docs/graph-api/webhooks/getting-started (verification, retries 36 h, 1000 batch; verified by caller)
- WhatsApp webhooks overview page (object name, 7-day retry, 20 fields; verified by caller)
- Not verified: `subscribed_apps` endpoint page was not fetched in this run.
