# Send Template Message — Specification

> **When to load**: Sending an approved WhatsApp template (the only message type allowed outside the 24 h customer service window), including header media, positional or named parameters, buttons, carousel, limited-time-offer and authentication templates.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/{version}/{phone-number-id}/messages` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` (system user or business token) |
| **Purpose** | Send a pre-approved template to an opted-in WhatsApp user, in or outside the customer service window |
| **Idempotency / retry** | None. The API has no idempotency key; a retry after a timeout can deliver twice. De-duplicate on your side (store your own key against the returned `wamid`). Do not blindly retry 131049 / 131056 / 131026. Delivery order across several sends is not guaranteed to match request order. |

## Request

Envelope fields (JSON body):

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `messaging_product` | string | yes | Always `"whatsapp"` | Fixed value |
| `recipient_type` | string | no | `individual` or `group` | Default `individual`; group sends need group support on the number |
| `to` | string | yes | Recipient phone number | Docs examples use `+16505551234`; whether a leading `+` is required is not stated. Use digits with country code (e.g. `919999999999`), which Meta also accepts in practice (unverified 2026-10-04) |
| `type` | string | yes | `"template"` | Fixed value |
| `template.name` | string | yes | Template name | Template must be `APPROVED` |
| `template.language.code` | string | yes | Language/locale code such as `en_US`, `en`, `hi` | Must match a language the template was approved in |
| `template.components` | array | conditional | Parameter values per component | Required whenever the template has variables, media header or dynamic buttons |
| `context.message_id` | string | no | `wamid` of a message to reply to (quoted reply) | Message must be in the same thread |
| `biz_opaque_callback_data` | string | no | Opaque string echoed back in status webhooks | Use it for correlation ids. Max length not stated in the pages fetched (unverified 2026-10-04) |

### Component objects

| Component | Shape | Notes |
|---|---|---|
| Header text | `{"type":"header","parameters":[{"type":"text","text":"..."}]}` | Only if the header has a variable |
| Header image | `{"type":"header","parameters":[{"type":"image","image":{"link":"https://..."}}]}` | `image` takes `id` (uploaded media id) or `link` |
| Header video | `... {"type":"video","video":{"link":"https://..."}}` | `id` or `link` |
| Header document | `... {"type":"document","document":{"link":"https://...","filename":"x.pdf"}}` | `filename` shown to the user (field confirmed from general Cloud API usage; unverified 2026-10-04 on this page) |
| Header location | `... {"type":"location","location":{"latitude":"37.44","longitude":"-122.16","name":"Philz Coffee","address":"101 Forest Ave, Palo Alto, CA 94301"}}` | Specified at send time |
| Body positional | `{"type":"body","parameters":[{"type":"text","text":"Pablo"},{"type":"text","text":"860198-230332"}]}` | Order maps to `{{1}}`, `{{2}}` |
| Body named | `{"type":"text","parameter_name":"first_name","text":"Jessica"}` | For templates created with named placeholders `{{first_name}}`; every named parameter must be supplied |
| Quick reply button | `{"type":"button","sub_type":"quick_reply","index":"0","parameters":[{"type":"payload","payload":"UNSUBSCRIBE_PROMOS"}]}` | `payload` returned in the inbound `button` webhook |
| URL button (dynamic suffix) | `{"type":"button","sub_type":"url","index":"0","parameters":[{"type":"text","text":"summer2023"}]}` | Only the variable suffix is sent; the base URL is fixed in the template. Named URL parameters use `parameter_name` |
| Copy code button | `{"type":"button","sub_type":"copy_code","index":"0","parameters":[{"type":"coupon_code","coupon_code":"250FF"}]}` | Coupon code string |
| Phone button | `{"type":"button","sub_type":"phone_number","index":"0","parameters":[{"type":"text","text":"15550051310"}]}` | Components page shows this form; the number is normally fixed at creation so params are usually not needed (unverified 2026-10-04) |

`index` is the zero-based button position in the template. Examples on Meta's page show it as a string.

### Carousel (media card) templates
```json
{
  "type": "carousel",
  "cards": [
    {
      "card_index": 0,
      "components": [
        {"type": "header", "parameters": [{"type": "image", "image": {"id": "<MEDIA_ID>"}}]},
        {"type": "button", "sub_type": "quick_reply", "index": 0,
         "parameters": [{"type": "payload", "payload": "MORE_INFO_0"}]}
      ]
    }
  ]
}
```
- Cards: minimum 2, maximum 10, and "an approved template can only be used to send the same number of cards as defined during its creation".
- Card body/button parameters follow the same shapes as above, nested under `cards[].components`.

### Limited-time-offer templates
```json
{"type": "limited_time_offer",
 "parameters": [{"type": "limited_time_offer", "limited_time_offer": {"expiration_time_ms": 1209600000}}]}
```
plus a `copy_code` button as above (`CARIBE25` in Meta's example). Meta describes `expiration_time_ms` as "offer code expiration time as a UNIX timestamp in milliseconds"; the sample value `1209600000` is shown as a 14 day window, which is inconsistent with an absolute Unix timestamp. Test before relying on either reading (unverified 2026-10-04).

### Authentication templates
Body and the one-tap/copy-code URL button both carry the same code, "this value must appear twice in the payload", max 15 characters:
```json
[{"type": "body", "parameters": [{"type": "text", "text": "123456"}]},
 {"type": "button", "sub_type": "url", "index": "0", "parameters": [{"type": "text", "text": "123456"}]}]
```
Authentication templates are created with `otp_type` `COPY_CODE` or `ONE_TAP` (create-time only).

## Example request
```bash
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "919999999999",
    "type": "template",
    "biz_opaque_callback_data": "order-1001",
    "template": {
      "name": "order_confirmation",
      "language": {"code": "en_US"},
      "components": [
        {"type": "header", "parameters": [
          {"type": "image", "image": {"id": "<MEDIA_ID>"}}]},
        {"type": "body", "parameters": [
          {"type": "text", "parameter_name": "first_name", "text": "Asha"},
          {"type": "text", "parameter_name": "order_number", "text": "SB-1001"}]},
        {"type": "button", "sub_type": "url", "index": "0", "parameters": [
          {"type": "text", "text": "SB-1001"}]},
        {"type": "button", "sub_type": "quick_reply", "index": "1", "parameters": [
          {"type": "payload", "payload": "TRACK_SB-1001"}]}
      ]
    }
  }'
```

Positional variant of the body: `{"type":"body","parameters":[{"type":"text","text":"Asha"},{"type":"text","text":"SB-1001"}]}`.

## Response
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{"input": "919999999999", "wa_id": "919999999999"}],
  "messages": [{"id": "wamid.HBgM...", "message_status": "accepted"}]
}
```

| Field | Type | Description |
|---|---|---|
| `contacts[].input` | string | The `to` value as you sent it |
| `contacts[].wa_id` | string | Canonical WhatsApp id; may differ from input (formatting, country quirks). Store it |
| `messages[].id` | string | `wamid` used to match status webhooks |
| `messages[].message_status` | string, optional | `accepted`, `held_for_quality_assessment`, `paused`. Only present for marketing templates in some cases. See `messaging_rules.md` |

Success only means accepted for processing. Delivery and failure arrive later in `statuses` webhooks (`sent`, `delivered`, `read`, `failed`).

## Errors
Error body: `{"error":{"message","type","code","error_subcode","error_data":{"messaging_product","details"},"fbtrace_id"}}`.

| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131049 | Per-user marketing template limit: Meta withheld delivery to keep the user's experience healthy | Do not resend the same marketing template to this user soon; send later or via a different channel | Later only (after hours/days), not immediately |
| 131056 | Pair rate limit: too many messages to the same recipient too fast | Back off and slow the per-recipient rate | Yes, with backoff |
| 131026 | Recipient is not a WhatsApp user or cannot receive the message | Mark number undeliverable; verify the number | No |
| 131047 | Re-engagement: more than 24 h since the user's last message (free-form only) | Use a template instead | No (switch to template) |
| 131053 | Media upload error (bad link, unsupported type, fetch failure) | Check link reachability, MIME and size; prefer uploaded media ids | After fixing |
| 130429 | Cloud API throughput exceeded | Reduce send rate | Yes, with backoff |
| 131057 | Account in maintenance (seen during throughput upgrade) | Wait | Yes |
| 132000 | Template parameter count mismatch (unverified 2026-10-04) | Match the number of components/params to the template | After fixing |
| 132001 | Template does not exist in that language, or not approved (unverified 2026-10-04) | Check name and `language.code` | After fixing |
| 132012 | Template parameter format mismatch (unverified 2026-10-04) | Fix parameter types (e.g. `parameter_name` missing) | After fixing |
| 131030 | Recipient not in the allowed list (test numbers) (unverified 2026-10-04) | Add to allowed list | No |

## Quirks and gotchas
- The template must be `APPROVED`; paused or disabled templates fail. Template names are case-sensitive and lowercase with underscores.
- `language.code` must match an approved translation exactly. `en` and `en_US` are different languages.
- Named versus positional is fixed at template creation. Mixing them fails.
- Header media: prefer uploaded `id` over `link`. The Cloud API caches a link asset for 10 minutes and reuses it while the link string is identical; append a random query string to force a refetch.
- Media ids returned by the upload API live 30 days; ids from webhooks live 7 days. Re-upload when stale.
- Marketing templates may be held or paused: US (+1) marketing templates have been paused since 2025-04-01 per Meta marketing pages (kept as stated; see `messaging_rules.md`).
- `button.index` identifies the position among buttons (0-based), not among dynamic buttons only.
- Authentication code max 15 characters and must be supplied in both body and button.
- Sending order for a burst of messages is not guaranteed; do not rely on sequencing for dependent messages. Wait for `sent` or `delivered` before the next one.
- The leading `+` in `to` is documented inconsistently; normalise to digits and store the returned `wa_id`.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/components
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/media-card-carousel-templates
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/limited-time-offer-templates
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/zero-tap-authentication-templates
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages
- Earlier run: reference/messages page (envelope fields, `message_status`)

Moved or rendered empty:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/template-messages (redirect notice to templates/overview)
- https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates (redirect notice)
- .../templates/authentication-templates/authentication-templates (create-time examples only, no send JSON)
- .../templates/authentication-templates/one-time-password-buttons (rendered empty)
