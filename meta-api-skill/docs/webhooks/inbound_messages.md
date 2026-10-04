# Inbound Messages Webhook — Specification

> **When to load**: You are parsing `messages[]` from a `messages` webhook (any type), downloading inbound media, handling replies/buttons, or reasoning about the 24 h window.

## Quick Reference
| Field | Value |
|---|---|
| Webhook field | `messages` |
| Location | `entry[].changes[].value.messages[]` (+ `value.contacts[]`, `value.metadata`) |
| Common keys | `from`, `id` (`wamid...`), `timestamp` (unix-seconds string), `type`, and an object named after `type` |
| `type` values documented | text, image, document, video, audio, sticker, location, contacts, reaction, interactive, button, order, system, unsupported (+ `errors`) |
| Optional keys | `context`, `referral`, `errors` |
| Media download | Media id -> `GET /v26.0/<MEDIA_ID>` -> `url` -> GET with `Authorization: Bearer <TOKEN>` |
| Media URL life | 5 minutes |
| Media id life | Webhook-delivered ids expire after 7 days; stored media persists 30 days |
| Service window | 24 h timer starts when the user messages you |

## Common structure (all types)
| Path | Type | Notes |
|---|---|---|
| `value.metadata.phone_number_id` | string | Receiving business number |
| `value.contacts[].profile.name` | string | Sender's profile name (PII) |
| `value.contacts[].wa_id` | string | Sender's WhatsApp id (digits, no `+`) |
| `messages[].from` | string | Sender number |
| `messages[].id` | string | wamid; dedupe key |
| `messages[].timestamp` | string | Unix seconds |
| `messages[].type` | string | Discriminator |
| `messages[].context` | object | Present for replies, quoted/forwarded, button taps |
| `messages[].referral` | object | Only for Click to WhatsApp ads |

### context
| Field | Seen in | Meaning |
|---|---|---|
| `context.from` | button, interactive replies | Business display number that sent the original message |
| `context.id` | button, interactive replies | wamid of the message the user replied to / tapped |
| `context.forwarded` | video example | `true` if forwarded |
| `context.frequently_forwarded` | video example | `true` if forwarded many times |

### referral (Click to WhatsApp ads only; shown on document/video/sticker pages)
`source_url`, `source_id`, `source_type` ("ad"), `body`, `headline`, `media_type`, `image_url`, `video_url`, `thumbnail_url`, `ctwa_clid`, `welcome_message.text`. The dedicated referral reference page rendered empty (unverified 2026-10-04 beyond these fields).

## text
```json
{ "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1744344496", "type": "text", "text": { "body": "Does it come in another color?" } }
```
`text.body` (string). This is where STOP/opt-out keywords arrive (see `docs/workflows/inbound_chat_and_optout.md`).

## image
```json
{ "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1744344496", "type": "image",
  "image": { "caption": "Taj Mahal", "mime_type": "image/jpeg", "sha256": "<base64-sha256>", "id": "<MEDIA_ID>", "url": "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=..." } }
```
`caption` optional. `url` is being released gradually from 2025-11-12; do not rely on it. Always be able to fall back to the media id.

## document
Fields: `caption` (optional), `filename`, `mime_type`, `sha256`, `id`, `url`. `type = "document"`. `referral` may appear.

## video
Fields: `caption` (optional), `mime_type`, `sha256`, `id`, `url`. `context.forwarded` / `frequently_forwarded` may appear.

## audio / voice
Fields: `mime_type` (e.g. `audio/ogg; codecs=opus`), `sha256`, `id`, `url`, `voice` (boolean: `true` if recorded with the WhatsApp voice-note feature). Voice notes arrive as `type = "audio"` with `voice: true`, not a separate type.

## sticker
Fields: `mime_type`, `sha256`, `id`, `url`, `animated` (boolean). `referral` may appear.

## location
```json
{ "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1744344496", "type": "location",
  "location": { "address": "101 Forest Ave, Palo Alto, CA 94301", "latitude": 37.44221496582, "longitude": -122.16165924072, "name": "Philz Coffee", "url": "https://philzcoffee.com/" } }
```
`latitude`/`longitude` are numbers; `address`, `name`, `url` appear for shared places and may be absent for a live pin (unverified 2026-10-04).

## contacts
```json
{ "type": "contacts", "contacts": [ { "name": { "first_name": "Barbara", "last_name": "Johnson", "formatted_name": "Barbara J. Johnson" },
  "org": { "company": "Social Tsunami" }, "phones": [ { "phone": "+1 (415) 555-0829", "wa_id": "14125550829", "type": "MOBILE" } ] } ] }
```
Other vCard fields (emails, addresses, urls, birthday) exist in the send API; their inbound presence is unverified 2026-10-04.

## reaction
```json
{ "type": "reaction", "reaction": { "message_id": "wamid.TARGET", "emoji": "👍" } }
```
`emoji` is omitted when the user removes the reaction. `message_id` is the message that was reacted to.

## interactive
`type = "interactive"`; `interactive.type` selects the shape. Replies carry `context.id` of your original interactive message.
### button_reply
```json
{ "context": { "from": "15550000000", "id": "wamid.ORIG" }, "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1750025136", "type": "interactive",
  "interactive": { "type": "button_reply", "button_reply": { "id": "cancel-button", "title": "Cancel" } } }
```
### list_reply
`interactive.list_reply`: `id` (row id, e.g. `priority_express`), `title`, `description`.
### nfm_reply (Flows)
Not present on the fetched interactive page (unverified 2026-10-04). Commonly `interactive.nfm_reply` with `name`, `body`, `response_json` (a JSON string); confirm against the Flows docs before relying on it.

## button (template quick-reply tap)
```json
{ "context": { "from": "15550000000", "id": "wamid.TEMPLATE_MSG" }, "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1750091045", "type": "button",
  "button": { "payload": "Unsubscribe", "text": "Unsubscribe" } }
```
`button.payload` is the quick-reply payload (equal to the label unless you set a custom payload on send); `button.text` is the label. Use `context.id` to link back to the campaign message.

## order
`order.catalog_id`, `order.text` (optional), `order.product_items[]` with `product_retailer_id`, `quantity` (integer), `item_price` (number), `currency` (ISO code).

## system
```json
{ "from": "16505551234", "id": "wamid.XXXX", "timestamp": "1750269342", "type": "system",
  "system": { "body": "User Sheena Nelson changed from 16505551234 to 12195555358", "wa_id": "12195555358", "type": "user_changed_number" } }
```
`user_changed_number`: migrate your stored `wa_id` to `system.wa_id`.

## unsupported
```json
{ "from": "919999999999", "id": "wamid.XXXX", "timestamp": "1750090702", "type": "unsupported",
  "errors": [ { "code": 131051, "title": "Message type unknown", "message": "Message type unknown", "error_data": { "details": "Message type is currently not supported." } } ],
  "unsupported": { "type": "edit" } }
```
Page states error code is 131051 or 131060 (131060 not on the error-codes page fetched; unverified 2026-10-04). Do not treat as a failure of your system; optionally reply asking for another format.

## errors (system-level, no messages)
```json
{ "messaging_product": "whatsapp", "metadata": { "display_phone_number": "15550000000", "phone_number_id": "<PHONE_NUMBER_ID>" },
  "errors": [ { "code": 130429, "title": "Rate limit hit", "message": "Rate limit hit",
    "error_data": { "details": "Message failed to send because there were too many messages sent from this phone number in a short period of time" },
    "href": "/documentation/business-messaging/whatsapp/support/error-codes" } ] }
```
Sits directly under `value` with `field: "messages"`. Classify via `docs/common/errors.md`.

## Media download path
1. Take `<type>.id` from the webhook (do not wait; ids from webhooks expire in 7 days).
2. `GET https://graph.facebook.com/v26.0/<MEDIA_ID>` with `Authorization: Bearer <TOKEN>` returns JSON including a short-lived `url`.
3. `GET` that `url` with the same bearer header (omitting the token fails). The URL expires after 5 minutes: re-query the id for a new URL.
4. Verify the downloaded bytes against `sha256` (base64 in webhook).
5. Size limits: audio 16 MB, document 100 MB, image 5 MB, sticker 100-500 KB, video 16 MB.
When the webhook `url` is present you may use it directly with the bearer token, but keep the id path as the fallback.

## 24 h customer service window
"When a WhatsApp user messages you or calls you, a 24-hour timer called a customer service window starts." Each inbound message restarts it. Inside it you may send free-form messages; outside it only templates (error 131047). Reactions and system messages: whether they restart the window is unverified 2026-10-04.

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131051 | Unsupported message type | Ask user for text/another format | No |
| 131052 | Media download failed | Re-query media id, retry download | After delay |
| 130429 | Throughput limit (system error) | Back off sends | Yes after delay |
| Media 404/expired | URL older than 5 min or id older than 7 days | Re-query id; if gone, ask user to resend | No |

## Quirks and gotchas
- `from` and `wa_id` have no `+`; the `button` page example shows `+16505551234` as a send-side placeholder only.
- Branch on `type`, then read the same-named object; unknown types must not crash the handler.
- Messages from group or business-scoped user ids may differ; unverified 2026-10-04.
- Treat `contacts[].profile.name` and message text as PII.
- Replies carry `context.id`, which maps back to the wamid you stored on send.

## Sources (verified 2026-10-04)
Base: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages (overview) and `/image`, `/document`, `/video`, `/audio`, `/sticker`, `/location`, `/contacts`, `/reaction`, `/interactive`, `/button`, `/order`, `/system`, `/unsupported`, `/errors`; media: .../business-phone-numbers/media; window: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages.
Rendered empty: `/messages/referral` (referral fields taken from the document/video/sticker pages).
