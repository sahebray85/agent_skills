# Refunds toolset

> **When to load**: full or partial refunds, instant refunds, refund status, listing refunds.

## Usage notes

- `create_refund` is **local-server only** — the hosted MCP does not expose it. Options: local MCP
  (Docker), Dashboard, or your backend calling `POST /v1/payments/{id}/refund`.
- Only `captured` payments refund. Multiple partial refunds are allowed up to the captured amount;
  check `fetch_multiple_refunds_for_payment` / `amount_refunded` first. The MCP requires `amount`
  (full refund = pass the remaining captured amount).
- `speed`: `normal` (default) or `optimum` (instant where possible).
- `receipt` is your reference, not an idempotency key — re-running a refund call creates another
  refund. Guard retries in your own code (e.g. unique `(payment_id, reason)` row before calling).
- Money moves and can't be undone: follow the confirmation rule in
  [refunds workflow](../workflows/refunds.md).
- Status via `fetch_refund` (`pending` → `processed` | `failed`) or webhooks `refund.processed` /
  `refund.failed`. `update_refund` edits `notes` only.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `create_refund`

**Write** · remote ❌ · `POST /v1/payments/{id}/refund`

> Use this tool to create a normal refund for a payment. Amount should be in paise (smallest currency unit). For INR: 100 paise = ₹1. Example: for ₹295, use 29500

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment which needs to be refunded. ID should have a pay_ prefix. |
| `amount` | number | REQUIRED; Min=100 | Payment amount in paise (smallest currency unit). For INR: 100 paise = ₹1. Example: for ₹295, use 29500 |
| `speed` | string | — | The speed at which the refund is to be processed. Default is 'normal'. For instant refunds, speed is set as 'optimum'. |
| `notes` | object | — | Key-value pairs used to store additional information. A maximum of 15 key-value pairs can be included. |
| `receipt` | string | — | A unique identifier provided by you for your internal reference. |

## `fetch_refund`

**Read** · remote ✅ · `GET /v1/refunds/{id}`

> Use this tool to retrieve the details of a specific refund using its id.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `refund_id` | string | REQUIRED | Unique identifier of the refund which is to be retrieved. ID should have a rfnd_ prefix. |

## `update_refund`

**Write** · remote ✅ · `PATCH /v1/refunds/{id}` (notes only)

> Use this tool to update the notes for a specific refund. Only the notes field can be modified.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `refund_id` | string | REQUIRED | Unique identifier of the refund which needs to be updated. ID should have a rfnd_ prefix. |
| `notes` | object | REQUIRED | Key-value pairs used to store additional information. A maximum of 15 key-value pairs can be included, with each value not exceeding 256 characters. |

## `fetch_multiple_refunds_for_payment`

**Read** · remote ✅ · `GET /v1/payments/{id}/refunds`

> Use this tool to retrieve multiple refunds for a payment. By default, only the last 10 refunds are returned.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment for which refunds are to be retrieved. ID should have a pay_ prefix. |
| `from` | number | — | Unix timestamp at which the refunds were created. |
| `to` | number | — | Unix timestamp till which the refunds were created. |
| `count` | number | — | The number of refunds to fetch for the payment. |
| `skip` | number | — | The number of refunds to be skipped for the payment. |

## `fetch_specific_refund_for_payment`

**Read** · remote ✅ · `GET /v1/payments/{id}/refunds/{rfnd}`

> Use this tool to retrieve details of a specific refund made for a payment.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment for which the refund has been made. ID should have a pay_ prefix. |
| `refund_id` | string | REQUIRED | Unique identifier of the refund to be retrieved. ID should have a rfnd_ prefix. |

## `fetch_all_refunds`

**Read** · remote ✅ · `GET /v1/refunds`

> Use this tool to retrieve details of all refunds. By default, only the last 10 refunds are returned.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `from` | number | — | Unix timestamp at which the refunds were created |
| `to` | number | — | Unix timestamp till which the refunds were created |
| `count` | number | — | The number of refunds to fetch. You can fetch a maximum of 100 refunds |
| `skip` | number | — | The number of refunds to be skipped |
