# Send Interactive Message — Specification

> **When to load**: Sending reply buttons, list menus, CTA URL buttons, location requests, Flows or product messages as free-form interactive messages inside the 24 h window.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/{version}/{phone-number-id}/messages` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Offer tappable choices; user taps arrive as `interactive` inbound webhooks |
| **Idempotency / retry** | No idempotency key; retry can duplicate. Make button/row ids unique per message so that a late tap can be matched. |

Interactive messages are free-form: they need an open customer service window (24 h since the user's last message).

## Request

Envelope: `messaging_product` = `"whatsapp"`, `recipient_type` = `individual`, `to`, `type` = `"interactive"`, `interactive` = object below.

### Reply buttons (`interactive.type = "button"`)
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `interactive.header` | object | no | `text`, `image`, `video` or `document` | Text header: max 60 chars (stated for list and CTA pages) |
| `interactive.body.text` | string | yes | Body | Max 1024 chars |
| `interactive.footer.text` | string | no | Footer | Max 60 chars |
| `interactive.action.buttons[]` | array | yes | Items `{"type":"reply","reply":{"id","title"}}` | Max 3 buttons |
| `...reply.id` | string | yes | Returned in webhook | Max 256 chars |
| `...reply.title` | string | yes | Button label | Max 20 chars |

Webhook on tap: `button_reply: {"id","title"}`.

### List (`interactive.type = "list"`)
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `header` | object | no | Text header only | Max 60 chars |
| `body.text` | string | yes | Body | Max 4096 chars |
| `footer.text` | string | no | Footer | Max 60 chars |
| `action.button` | string | yes | Label of the button that opens the list | Max 20 chars |
| `action.sections[]` | array | yes | Sections | Up to 10 sections; at least 1 row overall |
| `sections[].title` | string | yes | Section title | Max 24 chars (required when more than one section; stated "Yes" by Meta) |
| `sections[].rows[]` | array | yes | Rows `{id,title,description}` | Up to 10 rows total across all sections |
| `rows[].id` | string | yes | Returned in webhook | Max 200 chars |
| `rows[].title` | string | yes | Row title | Max 24 chars |
| `rows[].description` | string | no | Row subtitle | Max 72 chars |

### CTA URL (`interactive.type = "cta_url"`)
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `body.text` | string | yes | Body | Max 1024 chars; URLs auto-link |
| `header` | object | no | `text` (max 60), `image`, `video` or `document` | |
| `footer.text` | string | no | Footer | Max 60 chars |
| `action.name` | string | yes | `"cta_url"` | Fixed |
| `action.parameters.display_text` | string | yes | Button label | Max 20 chars |
| `action.parameters.url` | string | yes | Target URL | HTTPS recommended |

### Location request (`interactive.type = "location_request_message"`)
`body.text` (max 1024) and `action: {"name":"send_location"}`. The user sees a location sharing screen; the reply arrives as an inbound `location` message.

### Flow (`interactive.type = "flow"`) — brief
Parameters under `action: {"name":"flow","parameters":{...}}`: `flow_message_version` (`"3"`), `flow_id` or `flow_name`, `flow_cta`, `flow_action` (`navigate` | `data_exchange`), `mode` (`draft` | `published`), `flow_token`, `flow_action_payload` (`screen`, `data`). Result of the Flow returns as an `nfm_reply` webhook. (unverified 2026-10-04; the Flow page returned empty, values come from general Cloud API knowledge)

### Product messages — brief
Single product: `interactive.type = "product"` with `action.catalog_id` and `action.product_retailer_id`. Multi-product: `interactive.type = "product_list"` with a text header, and `action.catalog_id` plus `action.sections[].product_items[].product_retailer_id`. Both need a catalog connected to the WABA. (unverified 2026-10-04; page returned empty)

## Example request
```bash
# Reply buttons
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","recipient_type":"individual","to":"919999999999","type":"interactive",
       "interactive":{"type":"button","body":{"text":"Confirm your order SB-1001?"},
         "footer":{"text":"Sharanaya Boutique"},
         "action":{"buttons":[
           {"type":"reply","reply":{"id":"CONFIRM_SB-1001","title":"Confirm"}},
           {"type":"reply","reply":{"id":"CANCEL_SB-1001","title":"Cancel"}}]}}}'

# List
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"interactive",
       "interactive":{"type":"list","body":{"text":"How can we help?"},
         "action":{"button":"Choose","sections":[{"title":"Orders","rows":[
           {"id":"TRACK","title":"Track order","description":"Where is my parcel"},
           {"id":"RETURN","title":"Return item"}]}]}}}'

# CTA URL
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"interactive",
       "interactive":{"type":"cta_url","body":{"text":"Track your parcel"},
         "action":{"name":"cta_url","parameters":{"display_text":"Track","url":"https://example.com/track/SB-1001"}}}}'

# Location request
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","recipient_type":"individual","to":"919999999999","type":"interactive",
       "interactive":{"type":"location_request_message","body":{"text":"Share your delivery location"},
         "action":{"name":"send_location"}}}'
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
| `contacts[].wa_id` | string | Canonical id |
| `messages[].id` | string | `wamid` for status webhooks |

Inbound tap webhook (`messages[].interactive`): `button_reply {id,title}`, `list_reply {id,title,description}`; Flow results as `nfm_reply`.

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131047 | Outside the 24 h window | Send a template (buttons can be defined on templates) | No |
| 131026 | Recipient not on WhatsApp | Mark undeliverable | No |
| 131056 | Pair rate limit | Back off | Yes |
| 130429 | Throughput exceeded | Slow down | Yes, backoff |
| 131009 | Parameter value not valid (length, count) | Check limits above | After fixing |
| 131051 | Unsupported message type (unverified 2026-10-04) | Check `interactive.type` | No |
| 100 | Invalid parameter (unverified 2026-10-04) | Fix payload | After fixing |

## Quirks and gotchas
- Reply buttons: max 3, title 20 chars, id 256 chars. Lists: max 10 rows total (not per section), row title 24, description 72, row id 200.
- Header types differ: list allows text only; buttons and CTA allow text, image, video or document.
- CTA URL buttons are one button per message; button labels must be unique if multiple appear.
- Button ids are your correlation tokens; encode order ids but never secrets (they travel through webhooks unencrypted at the app level).
- Interactive messages are not allowed outside the window; use template quick-reply or URL buttons then.
- Older WhatsApp clients may not render some interactive types; users see a fallback "message not supported" prompt (unverified 2026-10-04).
- Address form (`address_message`) is covered in `send_text.md`.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-reply-buttons-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-list-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-cta-url-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/location-request-messages

Rendered empty (facts marked unverified):
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-flow-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-product-messages
