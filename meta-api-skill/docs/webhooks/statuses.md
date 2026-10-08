# Delivery Status Webhook — Specification

> **When to load**: You are handling `statuses[]` (sent, delivered, read, played, failed), mapping failures to retry policy, or reading pricing info from webhooks.

## Quick Reference
| Field | Value |
|---|---|
| Webhook field | `messages` |
| Location | `entry[].changes[].value.statuses[]` |
| Status values | `sent`, `delivered`, `read`, `played`, `failed` |
| Timestamp | String of unix seconds |
| Correlation | `statuses[].id` equals the wamid returned by the send call |
| Failure detail | `errors[]` with `code`, `title`, `message`, `error_data.details`, `href` |
| Custom echo | `biz_opaque_callback_data` (the string set on send) |

## Payload (statuses[])
| Field | Type | Notes |
|---|---|---|
| `id` | string | wamid of your outbound message |
| `status` | string | See values below |
| `timestamp` | string | Unix seconds |
| `recipient_id` | string | User wa_id (digits) |
| `conversation` | object | `id`, `origin.type`, optionally `expiration_timestamp`; present on sent (shape shown in example) |
| `pricing` | object | `billable` (bool), `pricing_model` (`PMP` in current example; `CBP` in the overview example), `type` (`regular`), `category` |
| `errors[]` | array | Only on `failed` |
| `biz_opaque_callback_data` | string | Returned if you supplied it on send |
| `recipient_type` / `recipient_participant_id` | string | Group messaging only (`recipient_type: "group"`) |

### Status meanings
| Status | Meaning |
|---|---|
| `sent` | Accepted by WhatsApp; left the business side |
| `delivered` | Reached the user's device |
| `read` | User opened it (only if user has read receipts on) |
| `played` | Voice/audio message played |
| `failed` | Not delivered; see `errors[]` |

### pricing.category values
`authentication`, `authentication_international`, `marketing`, `marketing_lite`, `referral_conversion`, `service`, `utility`.

## Example
```json
{
  "object": "whatsapp_business_account",
  "entry": [ { "id": "<WABA_ID>", "changes": [ { "field": "messages", "value": {
    "messaging_product": "whatsapp",
    "metadata": { "display_phone_number": "15550000000", "phone_number_id": "<PHONE_NUMBER_ID>" },
    "statuses": [ {
      "id": "wamid.XXXX", "status": "sent", "timestamp": "1750000000", "recipient_id": "919999999999",
      "conversation": { "id": "<CONVERSATION_ID>", "origin": { "type": "marketing" } },
      "pricing": { "billable": true, "pricing_model": "PMP", "type": "regular", "category": "marketing" }
    } ] } } ] } ]
}
```
Failed example:
```json
{ "id": "wamid.XXXX", "status": "failed", "timestamp": "1750000100", "recipient_id": "919999999999",
  "errors": [ { "code": 131049, "title": "<title>", "message": "<message>", "error_data": { "details": "<details>" }, "href": "<doc link>" } ] }
```

## Errors / failure modes
Classify `errors[0].code` via `docs/common/errors.md`. Frequent ones:
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131049 | Per-user marketing limit / healthy ecosystem | Defer; Meta says wait 24+ h | DEFERRED 24 h |
| 131056 | Pair rate limit (recipient throttle) | Slow down to that user | DEFERRED 1 h |
| 131026 | Message undeliverable | Check number validity/WhatsApp, version, T&C | No (usually) |
| 131047 | Outside 24 h window | Send a template | Template only |
| 130472 | Experiment block | Do not retry | No |
| 132xxx | Template problem | Fix template/params | After fix |

## Quirks and gotchas
- Order is not guaranteed: `read` may precede `delivered`. Use a monotonic state machine (sent < delivered < read; `failed` is terminal unless a later non-failed status arrives).
- `sent` can carry `conversation`/`pricing`; later statuses may omit them (shown on `sent` in the example; completeness on other statuses unverified 2026-10-04).
- Retries cause duplicates; dedupe on (`id`, `status`).
- `pricing_model` was `PMP` on the status example and `CBP` on the messages overview page; treat as an opaque string.
- Billing is by pricing category on `sent`/`delivered`; do not compute cost from `conversation` alone.
- Never assume `errors[0].title` is stable; key policy off `code`.
- Multi-hour lag between `sent` and `delivered` is normal for offline users.

## Sources (verified 2026-10-04)
- WhatsApp status webhook reference page (caller-verified statuses and pricing categories)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages (overview, `CBP` example)
