# QR Codes toolset

> **When to load**: UPI QR codes for a counter, invoice or customer; fixed vs any amount; single vs
> multiple use; listing payments received on a QR; closing a QR.

## Usage notes

- `type` must be `upi_qr` (INR). The official pages mark it as an on-demand feature: Razorpay
  Support activates it on the account. `usage`: `single_use` (accepts one payment, then closes
  automatically) or `multiple_use`.
- `single_use` **requires** `fixed_amount: true` — creation fails otherwise.
- `fixed_amount: true` requires `payment_amount` (paise, min 1); otherwise payer enters any amount.
- `close_by`: Unix seconds. The official Create page allows it on `single_use` QR codes only and
  says it errors on `multiple_use`. **The sources disagree on its limits:**
  - MCP `create_qr_code` schema: "min 2 mins after current time".
  - Official Create page, request parameter (`api/qr-codes/create.md`): "at least 2 minutes after
    the current time" and at most 2 hours; `null` becomes 2 hours and a later value is cut to
    2 hours.
  - Official Entity, Close, Update and image-content Create pages: "at least 15 minutes after the
    current time", up to `2147483647`. The Close page adds that a `single_use` QR can run for at
    most 45 days (also its default) and that a `multiple_use` QR never expires.

  A value 15 minutes ahead satisfies every reading. Store the `close_by` that the response
  returns, not the one you sent.
- `customer_id` ties the QR to a customer (`fetch_qr_codes_by_customer_id`).
- `fetch_payments_for_qr_code` is how you see money received; webhook `qr_code.credited` for
  real-time. A QR payment has **`order_id: null`** in both, so match it by the QR id
  (`payload.qr_code.entity.id`), never by an order.
- `close_reason`: `on_demand` (closed through the API or Dashboard), `paid` (a single-use QR that
  closed after its payment), `null` (still open). The Update page also lists `expired` (closed
  automatically after `close_by`).
- Webhook `qr_code.closed` fires **only on a manual close**, not when the QR auto-expires. Detect
  expiry by polling `fetch_qr_code` (`status`, `closed_at`, `close_reason`). Payload shapes and
  traps: [signatures-and-webhooks.md](../common/signatures-and-webhooks.md).
- `payments_amount_received` / `payments_count_received` count captured payments only.
- `close_qr_code` is **local-server only**; status becomes `closed` (with `closed_at`). To accept
  payments again, create a new QR.
- Dynamic Convenience Fees do not cover QR payments: the official page lists "Smart Collect (via
  VA, VPA and QR Codes)" as not available ([orders.md](orders.md)).

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `create_qr_code`

**Write** · remote ✅ · `POST /v1/payments/qr_codes`

> Create a new QR code in Razorpay that can be used to accept UPI payments

| Param | Type | Constraints | Description |
|---|---|---|---|
| `type` | string | REQUIRED; Pattern="^upi_qr$" | The type of the QR Code. Currently only supports 'upi_qr' |
| `name` | string | — | Label to identify the QR Code (e.g., 'Store Front Display') |
| `usage` | string | REQUIRED; Enum="single_use", "multiple_use" | Whether QR should accept single or multiple payments. Possible values: 'single_use', 'multiple_use' |
| `fixed_amount` | boolean | DefaultValue=false | Whether QR should accept only specific amount (true) or any amount (false) |
| `payment_amount` | number | Min=1 | The specific amount allowed for transaction in smallest currency unit |
| `description` | string | — | A brief description about the QR Code |
| `customer_id` | string | — | The unique identifier of the customer to link with the QR Code |
| `close_by` | number | — | Unix timestamp at which QR Code should be automatically closed (min 2 mins after current time) |
| `notes` | object | MaxProperties=15 | Key-value pairs for additional information (max 15 pairs, 256 chars each) |

## `fetch_qr_code`

**Read** · remote ✅ · `GET /v1/payments/qr_codes/{id}`

> Fetch a QR code's details using it's ID

| Param | Type | Constraints | Description |
|---|---|---|---|
| `qr_code_id` | string | REQUIRED | Unique identifier of the QR Code to be retrievedThe QR code id should start with 'qr_' |

## `fetch_all_qr_codes`

**Read** · remote ✅ · `GET /v1/payments/qr_codes`

> Fetch all QR codes with optional filtering and pagination

| Param | Type | Constraints | Description |
|---|---|---|---|
| `from` | number | Min=0 | Unix timestamp, in seconds, from when QR Codes are to be retrieved |
| `to` | number | Min=0 | Unix timestamp, in seconds, till when QR Codes are to be retrieved |
| `count` | number | Min=1; Max=100 | Number of QR Codes to be retrieved (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of QR Codes to be skipped (default: 0) |

## `fetch_qr_codes_by_customer_id`

**Read** · remote ✅ · `GET /v1/payments/qr_codes?customer_id=`

> Fetch all QR codes for a specific customer

| Param | Type | Constraints | Description |
|---|---|---|---|
| `customer_id` | string | REQUIRED | The unique identifier of the customer |

## `fetch_qr_codes_by_payment_id`

**Read** · remote ✅ · `GET /v1/payments/qr_codes?payment_id=`

> Fetch all QR codes for a specific payment

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | The unique identifier of the paymentThe payment id always should start with 'pay_' |

## `fetch_payments_for_qr_code`

**Read** · remote ✅ · `GET /v1/payments/qr_codes/{id}/payments`

> Fetch all payments made on a QR code

| Param | Type | Constraints | Description |
|---|---|---|---|
| `qr_code_id` | string | REQUIRED | The unique identifier of the QR Code to fetch payments forThe QR code id should start with 'qr_' |
| `from` | number | Min=0 | Unix timestamp, in seconds, from when payments are to be retrieved |
| `to` | number | Min=0 | Unix timestamp, in seconds, till when payments are to be fetched |
| `count` | number | Min=1; Max=100 | Number of payments to be fetched (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of records to be skipped while fetching the payments |

## `close_qr_code`

**Write** · remote ❌ · `POST /v1/payments/qr_codes/{id}/close`

> Close a QR Code that's no longer needed

| Param | Type | Constraints | Description |
|---|---|---|---|
| `qr_code_id` | string | REQUIRED | Unique identifier of the QR Code to be closedThe QR code id should start with 'qr_' |
