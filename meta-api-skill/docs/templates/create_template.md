# Create Message Template — Specification

> **When to load**: You are submitting a new template (text, media header, buttons, named or positional variables) for Meta review.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/v26.0/<WABA_ID>/message_templates` |
| **Auth** | `Authorization: Bearer <TOKEN>` (System User token) |
| **Permissions** | `whatsapp_business_management` |
| **Purpose** | Create a template; Meta reviews it automatically ("up to 24 hours") |
| **Idempotency / retry** | NOT idempotent by key, but (name, language) is unique per WABA, so a duplicate create fails with a validation error rather than creating twice. On timeout, GET the list and check before retrying. Retry only 5xx / `is_transient` |

## Request

Body (JSON, `Content-Type: application/json`):

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | yes | string | Pattern `^[a-z0-9_]+$`, max 512 chars. Uppercase/space/special chars rejected with code 100 |
| `language` | yes | string | Language code, e.g. `en_US` |
| `category` | yes | enum | `AUTHENTICATION`, `MARKETING`, `UTILITY` (`FREE_SERVICE` exists in the enum) |
| `components` | usually | array | Header, body, footer, buttons. See components.md |
| `parameter_format` | no | enum | `NAMED` or `POSITIONAL` |
| `allow_category_change` | no | boolean | Lets Meta reassign the category instead of rejecting |
| `sub_category` | no | enum | Utility only: `ORDER_STATUS`, `ORDER_DETAILS`, `RICH_ORDER_STATUS`, `BOOKING_STATUS`, `FRAUD_ALERT`, `FLIGHT_DELAY_AND_GATE_CHANGE_ALERT`, `CALL_PERMISSIONS_REQUEST` |
| `message_send_ttl_seconds` | no | integer | Message lifespan (time to live) |
| `cta_url_link_tracking_opted_out` | no | boolean | Opt out of CTA URL link tracking |
| `display_format` | no | enum | `WhatsAppBusinessMessageDisplayFormat` |
| `is_primary_device_delivery_only` | no | boolean | |
| `send_type` | no | enum | `campaign` or `direct` |
| `library_template_name` | no | string | Clone from the template library |
| `library_template_button_inputs` | no | array | Button customisation when cloning |
| `library_template_body_inputs` | no | object | Body customisation when cloning |

Limits that apply at creation:
- Max 100 templates created per hour per WABA.
- Max 250 templates per unverified portfolio, 6,000 per verified portfolio (with approved display name).
- Components: header text 60 chars, body 1024, footer 60, button label 25, URL 2000.

## Example request
```bash
# Utility template, positional variables
curl -s -X POST "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{
    "name": "order_confirmation",
    "language": "en_US",
    "category": "UTILITY",
    "components": [
      { "type": "BODY",
        "text": "Hi {{1}}, your order {{2}} is confirmed.",
        "example": { "body_text": [["Asha", "ORD-1001"]] } },
      { "type": "FOOTER", "text": "Thank you" },
      { "type": "BUTTONS", "buttons": [
        { "type": "URL", "text": "Track order",
          "url": "https://example.com/track/{{1}}",
          "example": ["ORD-1001"] } ] }
    ]
  }'

# Named variables with image header (header_handle from resumable upload)
curl -s -X POST "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{
    "name": "festive_sale",
    "language": "en_US",
    "category": "MARKETING",
    "parameter_format": "NAMED",
    "components": [
      { "type": "HEADER", "format": "IMAGE",
        "example": { "header_handle": ["<HANDLE>"] } },
      { "type": "BODY",
        "text": "Hi {{first_name}}, sale starts {{sale_start_date}}.",
        "example": { "body_text_named_params": [
          { "param_name": "first_name", "example": "Asha" },
          { "param_name": "sale_start_date", "example": "12 Oct" } ] } }
    ]
  }'
```

### Getting a `header_handle` (resumable upload)
```bash
# 1. open session
curl -s -X POST "https://graph.facebook.com/v26.0/<APP_ID>/uploads?file_name=banner.jpg&file_length=204800&file_type=image/jpeg" \
  -H "Authorization: Bearer <TOKEN>"
# -> {"id":"upload:<ID>"}

# 2. send bytes (note: OAuth scheme, not Bearer)
curl -s -X POST "https://graph.facebook.com/v26.0/upload:<ID>" \
  -H "Authorization: OAuth <TOKEN>" -H "file_offset: 0" \
  --data-binary @banner.jpg
# -> {"h":"<HANDLE>"}
```
Interrupted upload: `GET /upload:<ID>` returns the `file_offset` to resume from; resend with that offset. Documented file types: PDF, JPEG, JPG, PNG, MP4. Session and handle expiry are not documented (unverified 2026-10-04).

## Response
```json
{ "id": "<TEMPLATE_ID>", "status": "PENDING", "category": "UTILITY" }
```
| Field | Meaning |
|---|---|
| `id` | New template ID |
| `status` | Usually `PENDING`; may already be `APPROVED` or `REJECTED` |
| `category` | Final category. May differ from the request if `allow_category_change` was true |

Final outcome arrives via webhook `message_template_status_update` (fields `event`, `message_template_id`, `message_template_name`, `message_template_language`, `reason`, `message_template_category`).

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid parameter (bad name, missing field) | Fix payload | No |
| 190 | Invalid/expired token | Replace token | No |
| 200 | Missing permission | Grant `whatsapp_business_management` | No |
| 2 | Transient server error | Backoff | Yes |
| 2388039 | Status cannot be changed (pending / daily edit limit) | Wait for review | Later |
| 2388040 | Character limit exceeded | Shorten field | No |
| 2388047 | Invalid header format | Fix header | No |
| 2388072 | Invalid body format | Fix body | No |
| 2388073 | Invalid footer format | Fix footer | No |
| 2388293 | Too many variables for message length | Fewer variables or longer text | No |
| 2388299 | Variable at very start or end of text | Move variable inward | No |

## Quirks and gotchas
- Every variable needs an `example`; positional uses `body_text` / `header_text`, named uses `body_text_named_params` / `header_text_named_params` with `param_name` + `example`.
- Positional variables must be sequential (`{{1}}`, `{{2}}`); named variables may appear in any order.
- Deleting an approved template blocks reuse of that name for 30 days. Pick names you can live with.
- Marketing templates: WhatsApp does not currently deliver marketing templates to US (+1) numbers.
- If Meta thinks the category is wrong and `allow_category_change` is false it rejects with `INCORRECT_CATEGORY` or `TAG_CONTENT_MISMATCH`.
- Quick reply buttons must be grouped together, separate from URL/phone buttons.
- URL button variable must be at the end of the URL; percent-encode special characters.
- Review is automatic and can take up to 24 h; do not block a user flow on it.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management/
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/components
- https://developers.facebook.com/docs/whatsapp/message-templates/guidelines
- https://developers.facebook.com/docs/graph-api/guides/upload
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes

Empty or 404: none. Unverified: resumable upload handle expiry; exact creation-response behaviour when auto-approved.
