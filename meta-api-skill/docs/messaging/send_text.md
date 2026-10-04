# Send Text, Reaction, Location, Contacts, Address, Sticker — Specification

> **When to load**: Sending free-form (non-template) messages inside the 24 h customer service window: text with link preview, emoji reaction, location pin, contact cards, India address form, or a sticker.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/{version}/{phone-number-id}/messages` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Reply with free-form content to a user who messaged or called within the last 24 h |
| **Idempotency / retry** | No idempotency key. Retrying a timed-out call can duplicate the message. Reaction to the same message id replaces the previous reaction, so reaction retries are effectively safe. |

Free-form messages require an open customer service window ("when a WhatsApp user messages you or calls you, a 24-hour timer ... starts"; each new inbound resets it to 24 h). Outside it use `send_template.md`.

## Request

Common envelope: `messaging_product` = `"whatsapp"` (required), `recipient_type` = `individual` | `group` (optional), `to` (required), `type` (required), optional `context.message_id` (quote a message) and `biz_opaque_callback_data`.

### type = text
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `text.body` | string | yes | Message text | Max 4096 characters; URLs are auto-hyperlinked |
| `text.preview_url` | boolean | no | `true` asks the client to render a link preview | Only the first URL is previewed; URL must start with `http://` or `https://`; if omitted or the fetch fails a clickable link is shown |

### type = reaction
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `reaction.message_id` | string | yes | `wamid` of the message to react to | Must be a message in this chat thread, not deleted, not itself a reaction |
| `reaction.emoji` | string | yes | Emoji character or its Unicode escape sequence | Empty string removal behaviour not stated (unverified 2026-10-04) |

If the target message is more than 30 days old, the reaction is not delivered. Failures can return error 131009. Webhook: only `sent` is triggered, no `delivered` or `read`.

### type = location
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `location.latitude` | string/number | yes | Decimal degrees | |
| `location.longitude` | string/number | yes | Decimal degrees | |
| `location.name` | string | no | Place name | |
| `location.address` | string | no | Address line | |

### type = contacts
`contacts` is an array (up to 257 contacts per message; fewer recommended). Each contact:

| Name | Type | Required | Description |
|---|---|---|---|
| `name.formatted_name` | string | yes | Shown beside the profile arrow button |
| `name.first_name`, `last_name`, `middle_name`, `suffix`, `prefix` | string | no | Name parts (Meta's docs state that at least one of the optional name parts must accompany `formatted_name` in practice; unverified 2026-10-04) |
| `addresses[]` | object | no | `street`, `city`, `state`, `zip`, `country`, `country_code`, `type` |
| `emails[]` | object | no | `email`, `type` |
| `org` | object | no | `company`, `department`, `title` |
| `phones[]` | object | no | `phone`, `type`, `wa_id` |
| `urls[]` | object | no | `url`, `type` |
| `birthday` | string | no | `YYYY-MM-DD` |

If a phone entry has `wa_id`, the card shows "Message" and "Save contact" buttons; without it, an "Invite to WhatsApp" button appears.

### type = interactive, interactive.type = address_message (India only)
```json
{"type":"interactive","interactive":{"type":"address_message","body":{"text":"Please confirm your delivery address"},
 "action":{"name":"address_message","parameters":{"country":"IN"}}}}
```
- `parameters.country` is mandatory; omitting it gives a validation error.
- Only available "for businesses based in India and their India customers".
- Form fields: `name`, `phone_number` (valid phones only), `in_pin_code` (max length 6), `house_number`, `floor_number`, `tower_number`, `building_name`, `address`, `landmark_area`, `city`, `state`. Optional `values` and `validation_errors` pre-fill or flag fields (names confirmed from general Cloud API usage; unverified 2026-10-04 on the fetched page).

### type = sticker
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `sticker.id` | string | one of | Uploaded media id (recommended) | |
| `sticker.link` | string | one of | HTTPS URL (not recommended) | |

Static WebP max 100 KB, animated WebP max 500 KB, MIME `image/webp`.

## Example request
```bash
# Text with link preview
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","recipient_type":"individual","to":"919999999999",
       "type":"text","text":{"preview_url":true,"body":"Track your order: https://example.com/track/SB-1001"}}'

# Reaction
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","recipient_type":"individual","to":"919999999999",
       "type":"reaction","reaction":{"message_id":"wamid.HBgM...","emoji":"👍"}}'

# Location
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"location",
       "location":{"latitude":"12.9716","longitude":"77.5946","name":"Sharanaya Boutique","address":"Bengaluru"}}'

# Contacts
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"contacts",
       "contacts":[{"name":{"formatted_name":"Support Desk","first_name":"Support"},
                    "phones":[{"phone":"+919999999998","type":"WORK","wa_id":"919999999998"}]}]}'

# Sticker by uploaded id
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"sticker","sticker":{"id":"<MEDIA_ID>"}}'
```

## Response
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{"input": "919999999999", "wa_id": "919999999999"}],
  "messages": [{"id": "wamid.HBgM..."}]
}
```

| Field | Type | Description |
|---|---|---|
| `contacts[].input` | string | `to` as sent |
| `contacts[].wa_id` | string | Canonical id |
| `messages[].id` | string | `wamid` for status webhooks and for later reactions/replies |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131047 | Re-engagement: more than 24 h since user's last inbound | Send a template | No |
| 131026 | Recipient not a WhatsApp user / undeliverable | Mark undeliverable | No |
| 131056 | Pair rate limit, same recipient too fast | Back off | Yes, backoff |
| 131053 | Media upload error (sticker link) | Check link/MIME/size | After fixing |
| 131009 | Invalid parameter or undeliverable reaction conditions | Check target message id, age, type | After fixing |
| 130429 | Throughput exceeded | Slow down | Yes, backoff |
| 131008 | Required parameter missing (unverified 2026-10-04) | Fix payload | After fixing |
| 131051 | Unsupported message type (unverified 2026-10-04) | Fix `type` | No |

## Quirks and gotchas
- Text has no template fallback: after the window closes, the request fails with 131047 and you must switch to a template.
- `preview_url` is per message; previews render client-side only for the first URL.
- Reactions never produce `delivered` or `read` webhooks, so do not wait for them.
- Contacts: up to 257 per message, but large cards harm user experience and quality signals.
- `address_message` is India-only and requires `country`.
- Prefer uploaded media ids for stickers; links are cached 10 minutes by the Cloud API (append a random query string to force refetch).
- Delivery order of rapid consecutive messages is not guaranteed.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/text-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/reaction-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/location-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/contacts-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/address-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/sticker-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages

Rendered empty or 404: none for this file. Items marked unverified come from outside the fetched pages.
