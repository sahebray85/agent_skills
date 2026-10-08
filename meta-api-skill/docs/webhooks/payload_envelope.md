# Webhook Payload Envelope — Specification

> **When to load**: You need the outer structure of every WhatsApp webhook POST and how to route by `field` and by what is present inside `value`.

## Quick Reference
| Field | Value |
|---|---|
| `object` | `"whatsapp_business_account"` |
| `entry[].id` | WABA id (`<WABA_ID>`) |
| `entry[].time` | Unix seconds (number) on template/account fields; absent on the `messages` examples |
| `entry[].changes[].field` | Subscription field name, e.g. `messages` |
| `entry[].changes[].value` | Field-specific object |
| Batching | `entry` and `changes` are arrays; up to 1000 updates per POST |
| Timestamps inside messages/statuses | Strings of unix seconds |

## Envelope
| Path | Type | Notes |
|---|---|---|
| `object` | string | Always `whatsapp_business_account` for this product |
| `entry[]` | array | One element per WABA with updates |
| `entry[].id` | string | WABA id |
| `entry[].changes[]` | array | Iterate all; never read only `[0]` |
| `changes[].field` | string | `messages`, `message_template_status_update`, ... |
| `changes[].value.messaging_product` | string | `"whatsapp"` on `messages` |
| `changes[].value.metadata.display_phone_number` | string | Business number, digits |
| `changes[].value.metadata.phone_number_id` | string | Which business number received the event (`<PHONE_NUMBER_ID>`) |

## Routing inside `field = messages`
`value` contains exactly one of these families (check which keys exist):
| Present key | Meaning | See |
|---|---|---|
| `messages[]` (+ `contacts[]`) | Inbound user message | `inbound_messages.md` |
| `statuses[]` | Outbound delivery status | `statuses.md` |
| `errors[]` (no messages) | System-level error (example: 130429) | `inbound_messages.md` errors section |

## Example
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "<WABA_ID>",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15550000000",
              "phone_number_id": "<PHONE_NUMBER_ID>"
            },
            "contacts": [ { "profile": { "name": "Test User" }, "wa_id": "919999999999" } ],
            "messages": [ { "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1744344496", "type": "text", "text": { "body": "Hi" } } ]
          }
        }
      ]
    }
  ]
}
```

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| Unknown `field` | Subscribed to a field you do not handle | Log field name, return 200 | No |
| Missing `messages` and `statuses` | Error-only or other value | Branch on keys, not on assumptions | No |
| JSON parse failure | Truncated or altered body | Reject only after signature check; return 400 | Meta retries |

## Quirks and gotchas
- Tolerate unknown fields everywhere (use `FAIL_ON_UNKNOWN_PROPERTIES=false`); Meta adds fields without a version bump.
- `entry[].time` is a number whereas `messages[].timestamp` is a string.
- A single POST can mix messages for several phone numbers; always read `metadata.phone_number_id` per `value`.
- Dedupe key: `messages[].id` for inbound; (`statuses[].id`, `statuses[].status`) for statuses.
- In the `messages` examples fetched, `entry[].time` was not shown (unverified 2026-10-04 whether it is always present).
- Sample payload numbers on Meta pages are Meta test numbers; use your own placeholders in tests.

## Sources (verified 2026-10-04)
- WhatsApp webhooks overview page (object, entry, changes, field; verified by caller)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/image (envelope example)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/errors (error-only value)
