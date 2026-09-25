# Orders toolset

> **When to load**: creating the order that Standard Checkout needs, finding which payment(s) paid an
> order, listing orders, or creating a UPI mandate (Autopay) order.

## Usage notes

- Orders are created **server-side** with the amount from your own DB. Never let the browser set it.
- Regular order: `amount`, `currency`, optional `receipt` (≤ 40 chars; docs say it "has to be
  unique" — still, don't rely on Razorpay rejecting a duplicate: enforce one order per checkout in
  your own DB), `notes`, `partial_payment` + `first_payment_min_amount`,
  `transfers` (Route split to linked accounts).
- Mandate order (UPI single-block-multiple-debit): **all of** `method: "upi"`, `customer_id`
  (`cust_…`), `token: {max_amount, frequency, type: "single_block_multiple_debit", expire_at?}`.
  `frequency` ∈ `as_presented|monthly|one_time|yearly|weekly|daily`.
- An order can have many attempts. `fetch_order_payments` lists every payment; the one that counts has
  `status: "captured"`. Order `status: "paid"` = fully paid.
- `fetch_all_orders`: `authorized` 0/1 filter; `expand`: `payments`, `payments.card`, `transfers`,
  `virtual_account`; `from`/`to` Unix seconds; page with `count` (≤ 100) + `skip`.
- `update_order` edits `notes` only.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `create_order`

**Write** · remote ✅ · `POST /v1/orders`

> Create a new order in Razorpay. Supports both regular orders and mandate orders. 
> >
> > For REGULAR ORDERS: Provide amount, currency, and optional receipt/notes. 
> >
> > For MANDATE ORDERS (recurring payments): You MUST provide ALL of these fields: amount, currency, method='upi', customer_id (starts with 'cust_'), and token object. 
> >
> > The token object is required for mandate orders and must contain: max_amount (positive number in paise - For INR: 100 paise = ₹1), frequency (as_presented/monthly/one_time/yearly/weekly/daily), type='single_block_multiple_debit', and optionally expire_at (defaults to today+60days). 
> >
> > IMPORTANT: When token.type is 'single_block_multiple_debit', the method MUST be 'upi'. 
> >
> > Example mandate order payload: {"amount": 100, "currency": "INR", "method": "upi", "customer_id": "cust_abc123", "token": {"max_amount": 100, "frequency": "as_presented", "type": "single_block_multiple_debit"}, "receipt": "Receipt No. 1", "notes": {"key": "value"}}

| Param | Type | Constraints | Description |
|---|---|---|---|
| `amount` | number | REQUIRED; Min=100 | Payment amount in paise (smallest currency sub-unit). For INR: 100 paise = ₹1. Example: for ₹295, use 29500 |
| `currency` | string | REQUIRED; Pattern="^[A-Z]{3}$" | ISO code for the currency (e.g., INR, USD, SGD) |
| `receipt` | string | Max=40 | Receipt number for internal reference (max 40 chars, must be unique) |
| `notes` | object | MaxProperties=15 | Key-value pairs for additional information (max 15 pairs, 256 chars each) |
| `partial_payment` | boolean | DefaultValue=false | Whether the customer can make partial payments |
| `first_payment_min_amount` | number | Min=100 | Minimum amount in paise for first partial payment (only if partial_payment is true). For INR: 100 paise = ₹1 |
| `transfers` | array | — | Array of transfer objects for distributing payment amounts among multiple linked accounts. Each transfer object should contain: account (linked account ID), amount (in currency subunits), currency (ISO code), and optional fields like notes, linked_account_notes, on_hold, on_hold_until |
| `method` | string | — | Payment method for mandate orders. REQUIRED for mandate orders. Must be 'upi' when using token.type='single_block_multiple_debit'. This field is used only for mandate/recurring payment orders. |
| `customer_id` | string | — | Customer ID for mandate orders. REQUIRED for mandate orders. Must start with 'cust_' followed by alphanumeric characters. Example: 'cust_xxx'. This identifies the customer for recurring payments. |
| `token` | object | — | Token object for mandate orders. REQUIRED for mandate orders. Must contain: max_amount (positive number in paise, maximum debit amount - For INR: 100 paise = ₹1), frequency (as_presented/monthly/one_time/yearly/weekly/daily), type='single_block_multiple_debit' (only supported type), and optionally expire_at (Unix timestamp, defaults to today+60days). Example: {"max_amount": 100, "frequency": "as_presented", "type": "single_block_multiple_debit"} |

## `fetch_order`

**Read** · remote ✅ · `GET /v1/orders/{id}`

> Fetch an order's details using its ID

| Param | Type | Constraints | Description |
|---|---|---|---|
| `order_id` | string | REQUIRED | Unique identifier of the order to be retrieved |

## `fetch_all_orders`

**Read** · remote ✅ · `GET /v1/orders`

> Fetch all orders with optional filtering and pagination

| Param | Type | Constraints | Description |
|---|---|---|---|
| `count` | number | Min=1; Max=100 | Number of orders to be fetched (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of orders to be skipped (default: 0) |
| `from` | number | Min=0 | Timestamp (in Unix format) from when the orders should be fetched |
| `to` | number | Min=0 | Timestamp (in Unix format) up till when orders are to be fetched |
| `authorized` | number | Min=0; Max=1 | Filter orders based on payment authorization status. Values: 0 (orders with unauthorized payments), 1 (orders with authorized payments) |
| `receipt` | string | — | Filter orders that contain the provided value for receipt |
| `expand` | array | — | Used to retrieve additional information. Supported values: payments, payments.card, transfers, virtual_account |

## `fetch_order_payments`

**Read** · remote ✅ · `GET /v1/orders/{id}/payments`

> Fetch all payments made for a specific order in Razorpay

| Param | Type | Constraints | Description |
|---|---|---|---|
| `order_id` | string | REQUIRED | Unique identifier of the order for which payments should be retrieved. Order id should start with `order_` |

## `update_order`

**Write** · remote ✅ · `PATCH /v1/orders/{id}` (notes only)

> Use this tool to update the notes for a specific order. Only the notes field can be modified.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `order_id` | string | REQUIRED | Unique identifier of the order which needs to be updated. ID should have an order_ prefix. |
| `notes` | object | REQUIRED | Key-value pairs used to store additional information about the order. A maximum of 15 key-value pairs can be included, with each value not exceeding 256 characters. |
