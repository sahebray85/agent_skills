# Analytics (analytics, conversation_analytics, pricing_analytics, template_analytics) — Specification

> **When to load**: You are pulling send/delivery counts, cost, pricing breakdowns or template performance from a WABA via the Graph API analytics fields.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/v26.0/<WABA_ID>?fields=<FIELD>.<FILTERS>` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Permissions** | `whatsapp_business_management` |
| **Purpose** | Reporting on volume, cost and template engagement |
| **Idempotency / retry** | Read-only, safe to retry; 5xx/transient with backoff; 80007 means slow down |

Fields and lookback:
| Field | Lookback |
|---|---|
| `analytics` | 1 year (from 2025-12-01; was 10 years) |
| `conversation_analytics` | 1 year |
| `pricing_analytics` | 1 year |
| `template_analytics` | 90 days |
| `template_group_analytics` | 90 days |
| `group_analytics` | 90 days |
| `call_analytics` | not specified |

## Request

Filters are chained into the field expression: `pricing_analytics.start(<TS>).end(<TS>).granularity(DAILY)...`.

Common filters:
| Filter | Notes |
|---|---|
| `start`, `end` | UNIX timestamps (template analytics may use `YYYY-MM-DD` with `use_waba_timezone=true`) |
| `granularity` | `HALF_HOUR`, `DAY` / `DAILY`, `MONTH` / `MONTHLY` (not every value is valid for every field; `DAILY`/`MONTHLY` spelling for conversation/pricing; unverified per field 2026-10-04) |
| `phone_numbers` | Array of business numbers; empty = all |
| `country_codes` | 2-letter codes |
| `dimensions` | Per field, below |
| `metric_types` | Per field, below |

Per field:
| Field | Specific filters |
|---|---|
| `analytics` | `product_types`: `0` templates, `2` non-templates, `100` incoming |
| `conversation_analytics` | `metric_types` `COST`, `CONVERSATION`; `conversation_categories` `AUTHENTICATION`, `MARKETING`, `SERVICE`, `UTILITY`; `conversation_types` `FREE_ENTRY_POINT`, `FREE_TIER`, `REGULAR`; `conversation_directions` `BUSINESS_INITIATED`, `USER_INITIATED`, `UNKNOWN`; `dimensions` `CONVERSATION_CATEGORY`, `CONVERSATION_DIRECTION`, `CONVERSATION_TYPE`, `COUNTRY`, `PHONE` |
| `pricing_analytics` | `metric_types` `COST`, `VOLUME`; `pricing_categories` `AUTHENTICATION`, `AUTHENTICATION_INTERNATIONAL`, `MARKETING`, `MARKETING_LITE`, `SERVICE`, `UTILITY`, `REFERRAL_CONVERSION`; `pricing_types` `FREE_CUSTOMER_SERVICE`, `FREE_ENTRY_POINT`, `REGULAR`; `dimensions` `COUNTRY`, `PHONE`, `PRICING_CATEGORY`, `PRICING_TYPE`, `TIER` |
| `template_analytics` | `template_ids` required, max 10; `metric_types` `COST`, `CLICKED`, `DELIVERED`, `READ`, `SENT` (plus Marketing Messages API conversion metrics); `product_type` `CLOUD_API` or `MARKETING_MESSAGES_API_FOR_WHATSAPP`; `use_waba_timezone` boolean (default UTC) |
| `template_group_analytics` | `template_group_ids` required, max 10 |
| `call_analytics` | `directions`, `metric_types` `COUNT`, `COST`, `AVERAGE_DURATION` |

Maximum single-request time range was not documented (unverified 2026-10-04); chunk by month to be safe.

## Example request
```bash
# Messages sent/delivered per day
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=analytics.start(1759276800).end(1761955200).granularity(DAY).phone_numbers([]).product_types([0,2])"

# Cost by category
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=pricing_analytics.start(1759276800).end(1761955200).granularity(MONTHLY).metric_types([\"COST\",\"VOLUME\"]).dimensions([\"PRICING_CATEGORY\",\"PRICING_TYPE\"])"

# Template performance
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=template_analytics.start(1759276800).end(1761955200).granularity(DAILY).template_ids([<TEMPLATE_ID>]).metric_types([\"SENT\",\"DELIVERED\",\"READ\",\"CLICKED\",\"COST\"])"
```

## Response
```json
{ "pricing_analytics": {
    "data": [ { "data_points": [
      { "start": 1759276800, "end": 1759363200,
        "volume": 120, "cost": 85.2,
        "pricing_category": "MARKETING", "pricing_type": "REGULAR" } ] } ],
    "granularity": "DAILY" },
  "id": "<WABA_ID>" }
```
Response structure from the docs: `<field>.data[].data_points[]` (or `data_points` directly), plus `phone_numbers`, `country_codes`, `granularity`, and the WABA `id`.

| Data point field | Meaning |
|---|---|
| `start`, `end` | Bucket boundaries (unix time) |
| `sent`, `delivered`, `read` | Message counts (`analytics`, template analytics) |
| `cost` | Cost in WABA currency |
| `conversation` | Conversation counts |
| dimension keys | `country`, `phone_number`, `pricing_category`, etc. (exact key spelling unverified 2026-10-04) |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid filter syntax or value | Fix expression | No |
| 190 | Token invalid | Replace | No |
| 200 | Permission missing | Grant `whatsapp_business_management` | No |
| 80007 | WABA rate limit | Reduce frequency | Yes |
| 2 / 500 | Transient | Backoff | Yes |

## Quirks and gotchas
- Analytics are approximate and may differ from invoices.
- COST metrics are unavailable for WABAs on a Solution Partner's credit line.
- Template read/click data is available only 7 days after send, then resets.
- Template and template group analytics are unsupported for EU and Japan WABAs or numbers.
- `product_types` numeric codes are strings of integers inside an array; `0` templates, `2` non-templates, `100` incoming.
- `pricing_analytics` replaces conversation-based reasoning after per-message pricing (2025-07-01); `conversation_analytics` remains for historical conversation counts.
- Escape parentheses and brackets in `--data-urlencode` and quote string arrays.
- Day boundaries default to UTC; use `use_waba_timezone` for template analytics to match billing.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/analytics
- https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes

Empty or 404: none. Unverified: maximum time range, per-field granularity validity, exact data point key names, example numbers shown above are illustrative.

## Reporting recipes
| Question | Field and settings |
|---|---|
| How many template messages did we send each day? | `analytics`, `granularity(DAY)`, `product_types([0])` |
| What did we spend by category this month? | `pricing_analytics`, `granularity(MONTHLY)`, `metric_types(["COST"])`, `dimensions(["PRICING_CATEGORY"])` |
| How much was free vs regular? | `pricing_analytics`, `dimensions(["PRICING_TYPE"])` |
| Which template drives clicks? | `template_analytics`, `metric_types(["CLICKED","SENT"])`, up to 10 template ids |
| Which country costs most? | `pricing_analytics`, `dimensions(["COUNTRY"])` |

## Operational advice
- Export daily snapshots; the 90-day template lookback and 7-day read/click availability mean older engagement data is lost.
- Reconcile against invoices monthly and expect small differences.
- Chunk requests (a month at a time) and respect error 80007.
- Page through `data` arrays; large dimension combinations can produce many data points.
