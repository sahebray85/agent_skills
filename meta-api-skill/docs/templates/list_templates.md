# List and Get Message Templates — Specification

> **When to load**: You need to read templates from a WABA (list, paginate, fetch one by ID, or check status/quality/category) before sending or syncing.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path (list)** | `/v26.0/<WABA_ID>/message_templates` |
| **Path (single)** | `/v26.0/<TEMPLATE_ID>` |
| **Auth** | `Authorization: Bearer <TOKEN>` (System User token) |
| **Permissions** | `whatsapp_business_management` (read); `business_management` for portfolio-owned assets |
| **Purpose** | Read template definitions, status, category, quality score and rejection reason |
| **Idempotency / retry** | Pure read, safe to retry. Retry 5xx / `is_transient: true` with backoff. Do not retry 100/190/200/803 |

## Request

Query parameters on the list endpoint (the reference page documents ONLY these four):

| Param | Type | Notes |
|---|---|---|
| `fields` | string | Comma-separated field list. Without it Graph returns a default subset |
| `limit` | integer (min 1) | Page size |
| `after` | string | Forward cursor from `paging.cursors.after` |
| `before` | string | Backward cursor from `paging.cursors.before` |

Single-template endpoint accepts `fields` only.

Filtering: the reference page does NOT document a `name=` filter. The template-management guide shows a `status=` filter in its examples ("swap `status=approved` with `status=rejected`") but the reference lists no such param. Treat both as undocumented: safest is to page through everything and filter client-side. If you use `name=` or `status=`, verify behaviour against your WABA first (unverified 2026-10-04).

Fields documented on the MessageTemplate object:

| Field | Meaning |
|---|---|
| `id` | Template ID (use as `<TEMPLATE_ID>`) |
| `name` | Template name |
| `language` | Language code, e.g. `en_US` |
| `status` | See statuses below |
| `category` | `AUTHENTICATION`, `MARKETING`, `UTILITY`, `FREE_SERVICE` |
| `sub_category` | Utility only: `BOOKING_STATUS`, `CALL_PERMISSIONS_REQUEST`, `FLIGHT_DELAY_AND_GATE_CHANGE_ALERT`, `FRAUD_ALERT`, `ORDER_DETAILS`, `ORDER_STATUS`, `RICH_ORDER_STATUS` |
| `components` | Array of header/body/footer/buttons objects |
| `parameter_format` | `NAMED` or `POSITIONAL` |
| `display_format` | `WhatsAppBusinessMessageDisplayFormat` |
| `quality_score` | `GREEN`, `YELLOW`, `RED`, `UNKNOWN` |
| `health_status` | Health summary object |
| `rejected_reason` | See rejection reasons below |
| `ad_account_id`, `ad_campaign_id` | Advertising linkage fields |

Statuses (WhatsAppBusinessHSMStatus): `APPROVED`, `PENDING`, `REJECTED`, `ARCHIVED`, `DISABLED`, `PAUSED`, `DELETED`, `PENDING_DELETION`, `LIMIT_EXCEEDED`, `IN_APPEAL`.

Rejection reasons: `ABUSIVE_CONTENT`, `CATEGORY_NOT_AVAILABLE`, `INCORRECT_CATEGORY`, `INVALID_FORMAT`, `NONE`, `PROMOTIONAL`, `SCAM`, `TAG_CONTENT_MISMATCH`.

## Example request
```bash
# First page, selected fields
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,name,language,status,category,quality_score,rejected_reason,components" \
  --data-urlencode "limit=100"

# Next page
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,name,language,status,category" \
  --data-urlencode "limit=100" \
  --data-urlencode "after=<CURSOR>"

# One template
curl -s -G "https://graph.facebook.com/v26.0/<TEMPLATE_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,name,status,category,quality_score,rejected_reason"
```

## Response
```json
{
  "data": [
    {
      "id": "<TEMPLATE_ID>",
      "name": "order_confirmation",
      "language": "en_US",
      "status": "APPROVED",
      "category": "UTILITY",
      "quality_score": { "score": "GREEN" },
      "components": [
        { "type": "BODY", "text": "Hi {{1}}, order {{2}} is confirmed." }
      ]
    }
  ],
  "paging": {
    "cursors": { "before": "<CURSOR>", "after": "<CURSOR>" },
    "next": "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates?...",
    "previous": "https://graph.facebook.com/v26.0/..."
  }
}
```

| Field | Meaning |
|---|---|
| `data[]` | MessageTemplate objects containing only the requested `fields` |
| `paging.cursors.after` | Pass as `after` for the next page |
| `paging.next` | Absent on the last page. Loop until it is missing |

The exact shape of `quality_score` (string vs object with `score`) is not shown on the reference page; code defensively for both (unverified 2026-10-04).

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid parameter (bad field name, bad cursor) | Fix request | No |
| 190 | Invalid or expired OAuth token | Replace token | No (after refresh yes) |
| 200 | Insufficient permissions / no token provided | Grant `whatsapp_business_management`, include token | No |
| 803 | Template or WABA not found | Check ID and that token can see the WABA | No |
| 2 | Transient internal error | Backoff and retry | Yes |
| 80008 | Rate limit on WABA-level Graph calls (seen on business edges) | Slow down | Yes, with backoff |

HTTP: 400 bad request, 401 bad token, 403 forbidden, 404 not found, 500 server error.

## Quirks and gotchas
- Always request `fields` explicitly. Default output omits `components`, `quality_score` and `rejected_reason`.
- A template is unique per (name, language). Listing returns one row per language, so a "template" with 3 languages is 3 rows with 3 different IDs.
- Use cursors from the response, never construct them. Cursors are opaque.
- `DELETED` and `PENDING_DELETION` rows may still appear; do not treat presence as sendable. Only `APPROVED` templates can be sent (a `PAUSED` template cannot be sent until restored).
- Quality state can change without a list call: subscribe to webhooks `message_template_status_update` and `message_template_quality_update` rather than polling aggressively.
- Large `limit` plus `components` can time out on WABAs with thousands of templates (up to 6,000 per verified portfolio). Use 50-100 and page.
- Per-WABA caps: 250 templates for unverified portfolios, 6,000 for verified (see create_template.md).

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management/
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-pacing
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update

Empty render or 404: none for this file. Shape of `quality_score` marked unverified above.
