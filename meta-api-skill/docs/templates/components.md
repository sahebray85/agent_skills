# Template Components — Specification

> **When to load**: You are composing the `components` array of a template (header, body, footer, buttons) and need limits, formats and example-field rules.

## Quick Reference
| Field | Value |
|---|---|
| **Applies to** | `POST /v26.0/<WABA_ID>/message_templates` and `POST /v26.0/<TEMPLATE_ID>` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Component types** | `HEADER` (optional), `BODY` (required), `FOOTER` (optional), `BUTTONS` (optional), limited-time-offer (promotional) |
| **Variable styles** | Positional `{{1}}` or named `{{first_name}}` (`parameter_format` NAMED / POSITIONAL) |
| **Rule of thumb** | Every variable needs a sample value in `example` |

## Character limits
| Element | Max |
|---|---|
| Header text | 60 |
| Body text | 1024 |
| Footer text | 60 |
| Button label | 25 |
| Copy-code button value | 20 |
| Phone number (button) | 20 |
| URL (button) | 2000 |
| Template name | 512 chars, `^[a-z0-9_]+$` |

## HEADER
| Format | Notes |
|---|---|
| `TEXT` | Supports 1 variable; no Markdown special characters |
| `IMAGE` | Requires uploaded asset handle in `example.header_handle` |
| `VIDEO` | Same as image |
| `GIF` | Listed by the components page as a media header option |
| `DOCUMENT` | Same handle mechanism |
| `LOCATION` | For order tracking / delivery updates; real-time locations unsupported |

Handle comes from the resumable upload API (see create_template.md). Documented upload file types: PDF, JPEG, JPG, PNG, MP4.

```json
{ "type": "HEADER", "format": "TEXT", "text": "Order {{1}}",
  "example": { "header_text": ["ORD-1001"] } }
{ "type": "HEADER", "format": "TEXT", "text": "Hello {{name}}",
  "example": { "header_text_named_params": [ { "param_name": "name", "example": "Asha" } ] } }
{ "type": "HEADER", "format": "IMAGE",
  "example": { "header_handle": ["<HANDLE>"] } }
```

## BODY
- Required, text only, multiple variables allowed.
- Example keys: `body_text` (positional, array of arrays) or `body_text_named_params` (array of `{param_name, example}`).
```json
{ "type": "BODY",
  "text": "Thank you, {{first_name}}! Order #{{order_number}}.",
  "example": { "body_text_named_params": [
    { "param_name": "first_name", "example": "Pablo" },
    { "param_name": "order_number", "example": "860198-230332" } ] } }
```
Creation errors related to body: 2388072 invalid body format, 2388293 too many variables for the length, 2388299 variable at start or end of the text.

## FOOTER
```json
{ "type": "FOOTER", "text": "Reply STOP to opt out" }
```
Text only, no variables.

## BUTTONS
Container: `{ "type": "BUTTONS", "buttons": [ ... ] }`.

| Button `type` | Limit | Notes |
|---|---|---|
| `QUICK_REPLY` | up to 10 | Group quick replies together |
| `URL` | 2 | One variable, appended at the end of the URL, `example: ["sample"]`; percent-encode special chars |
| `PHONE_NUMBER` | 1 | `phone_number` up to 20 chars |
| Copy code | 1 | Max 20 chars; used with offers/authentication |
| Voice call, Multi-product (MPM), Single-product (SPM), One-time password | per feature | Feature specific |
| Total | 10 button components | |

```json
{ "type": "BUTTONS", "buttons": [
  { "type": "QUICK_REPLY", "text": "Stop promotions" },
  { "type": "URL", "text": "Track", "url": "https://example.com/t/{{1}}", "example": ["ORD-1001"] },
  { "type": "PHONE_NUMBER", "text": "Call us", "phone_number": "<PHONE_E164>" } ] }
```

Ordering rule: buttons must be organised in two groups, quick-reply buttons and non-quick-reply buttons. Valid: all quick replies; quick replies grouped with URL/phone; non-quick-reply only.

## Display constraints
- 4 or more buttons, or a quick reply plus one or more other-type buttons, cannot be viewed on WhatsApp desktop.
- With more than 3 buttons, two are shown and the rest collapse into a "See all options" button.

## Parameter formats
| | Positional | Named |
|---|---|---|
| Syntax | `{{1}}`, `{{2}}` | `{{first_name}}` |
| Order | Sequential, no gaps | Any order |
| `parameter_format` | `POSITIONAL` | `NAMED` |
| Example keys | `header_text`, `body_text` | `header_text_named_params`, `body_text_named_params` |
| Send-time parameter | by position | `parameter_name` (see message send docs) |

Name charset for named params: lowercase letters, digits, underscore (inferred; unverified 2026-10-04).

## Quirks and gotchas
- Header supports at most 1 variable; body many; URL button 1.
- Media header requires a handle at creation AND a media id/link at send time.
- Do not start or end the body with a variable (2388299).
- Limited-time-offer component is only for promotional (marketing) templates; its field schema is not on the components page excerpt (unverified 2026-10-04).
- Carousel components exist in the platform but were not on the fetched page; not specified here (unverified 2026-10-04).

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/components
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api
- https://developers.facebook.com/docs/graph-api/guides/upload
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes

Empty or 404: none.

## Full worked example
A marketing template exercising every common component:
```json
{
  "name": "festive_sale_v1",
  "language": "en_US",
  "category": "MARKETING",
  "parameter_format": "NAMED",
  "components": [
    { "type": "HEADER", "format": "IMAGE",
      "example": { "header_handle": ["<HANDLE>"] } },
    { "type": "BODY",
      "text": "Hi {{first_name}}, our festive sale starts {{sale_start_date}}.",
      "example": { "body_text_named_params": [
        { "param_name": "first_name", "example": "Asha" },
        { "param_name": "sale_start_date", "example": "12 Oct" } ] } },
    { "type": "FOOTER", "text": "Reply STOP to opt out" },
    { "type": "BUTTONS", "buttons": [
      { "type": "QUICK_REPLY", "text": "Stop promotions" },
      { "type": "URL", "text": "Shop now",
        "url": "https://example.com/sale/{{1}}", "example": ["festive"] } ] }
  ]
}
```

## Pre-flight checklist
1. Name matches `^[a-z0-9_]+$` and is not one you deleted in the last 30 days.
2. Body is 1024 characters or fewer and neither starts nor ends with a variable.
3. Header text is 60 characters or fewer with at most one variable.
4. Footer is 60 characters or fewer with no variable.
5. Every variable has an example, using the key set matching `parameter_format`.
6. Positional variables are sequential from 1 with no gaps.
7. At most 10 buttons, at most 2 URL, at most 1 phone, at most 1 copy code.
8. Quick replies grouped apart from other button types.
9. Media header handle is fresh; re-upload if the handle may have expired.
10. Marketing content is not placed in a UTILITY template (INCORRECT_CATEGORY risk).
