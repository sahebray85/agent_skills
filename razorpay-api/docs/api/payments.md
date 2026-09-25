# Payments toolset

> **When to load**: fetching or capturing a payment, card metadata, payment notes, server-to-server
> (S2S) payments with OTP, UPI collect/intent, or a customer's saved cards/UPI (tokens).

## Usage notes

- `fetch_payment` → `status` (see [lifecycle](../common/conventions.md#lifecycles)), `amount` in
  paise, `order_id`, `method`, `amount_refunded`, `error_*` fields on failures.
- `capture_payment`: only `authorized` payments; `amount` = the authorized amount; `currency`
  required. Accounts with auto-capture never need it — `fetch_payment` first. Uncaptured payments
  auto-refund after 3 days.
- `fetch_payment_card_details`: card payments only; masked metadata (last4, network, issuer, type) —
  treat as personal data.
- `initiate_payment` (S2S JSON, `POST /v1/payments/create/json`) needs an existing `order_id`.
  `token` + `customer_id` = saved method; `vpa` = UPI collect (6-min expiry); `upi_intent: true` =
  returns a UPI intent URL. **Side effects**: `contact` → creates/gets a customer; an OTP `next`
  action → the tool **sends the OTP immediately**, then use `submit_otp` / `resend_otp`. S2S usually
  needs enabling on the account; the tool never takes raw card numbers.
- `initiate_payment` with `recurring: true` hits `/v1/payments/create/recurring` **only for non-INR**.
  Razorpay documents INR subsequent debits (UPI Autopay, e-mandate) on `/create/recurring` — do those
  from your backend, not this tool. See [recurring_mandate.md](../workflows/recurring_mandate.md).
- `fetch_tokens` is registered as a **write** tool: with only `contact` it `POST /v1/customers`
  (creates the customer if missing; `9876543210` vs `+919876543210` can duplicate). Prefer
  `customer_id`. `revoke_token` is irreversible.
- Not in MCP (call REST/SDK directly): payment downtimes `GET /v1/payments/downtimes`, methods
  `GET /v1/methods`, Route transfers `POST /v1/payments/{id}/transfers`, customers CRUD
  `/v1/customers`.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `fetch_payment`

**Read** · remote ✅ · `GET /v1/payments/{id}`

> Use this tool to retrieve the details of a specific payment using its id. Amount returned is in paisa

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | payment_id is unique identifier of the payment to be retrieved. |

## `fetch_payment_card_details`

**Read** · remote ✅ · `GET /v1/payments/{id}/card`

> Use this tool to retrieve the details of the card used to make a payment. Only works for payments made using a card.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment for which you want to retrieve card details. Must start with 'pay_' |

## `update_payment`

**Write** · remote ✅ · `PATCH /v1/payments/{id}` (notes only)

> Use this tool to update the notes field of a payment. Notes are key-value pairs that can be used to store additional information.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment to be updated. Must start with 'pay_' |
| `notes` | object | REQUIRED | Key-value pairs that can be used to store additional information about the payment. Values must be strings or integers. |

## `capture_payment`

**Write** · remote ✅ · `POST /v1/payments/{id}/capture`

> Use this tool to capture a previously authorized payment. Only payments with 'authorized' status can be captured

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment to be captured. Should start with 'pay_' |
| `amount` | number | REQUIRED | The amount to be captured in paise. For INR: 100 paise = ₹1. Should be equal to the authorized amount |
| `currency` | string | REQUIRED | ISO code of the currency in which the payment was made (e.g., INR) |

## `fetch_all_payments`

**Read** · remote ✅ · `GET /v1/payments`

> Fetch all payments with optional filtering and pagination

| Param | Type | Constraints | Description |
|---|---|---|---|
| `count` | number | Min=1; Max=100 | Number of payments to fetch (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of payments to skip (default: 0) |
| `from` | number | Min=0 | Unix timestamp (in seconds) from when payments are to be fetched |
| `to` | number | Min=0 | Unix timestamp (in seconds) up till when payments are to be fetched |

## `initiate_payment`

**Write** · remote ✅ · `POST /v1/payments/create/json` ¹

> Initiate a payment using the S2S JSON v1 flow. Required parameters: amount and order_id. For saved payment methods, provide token. For UPI collect flow, provide 'vpa' parameter which automatically sets UPI with flow='collect' and expiry_time='6'. For UPI intent flow, set 'upi_intent=true' parameter which automatically sets UPI with flow='intent' and API returns UPI URL. Supports additional parameters like customer_id, email, contact, save, and recurring. Returns payment details including next action steps if required.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `amount` | number | REQUIRED; Min=100 | Payment amount in paise (smallest currency sub-unit). For INR: 100 paise = ₹1. Example: for ₹100, use 10000 |
| `currency` | string | — | Currency code for the payment. Default is 'INR' |
| `token` | string | — | Token ID of the saved payment method. Must start with 'token_' |
| `order_id` | string | REQUIRED | Order ID for which the payment is being initiated. Must start with 'order_' |
| `email` | string | — | Customer's email address (optional) |
| `contact` | string | — | Customer's phone number |
| `customer_id` | string | — | Customer ID for the payment. Must start with 'cust_' |
| `save` | boolean | — | Whether to save the payment method for future use |
| `vpa` | string | — | Virtual Payment Address (VPA) for UPI payment. When provided, automatically sets method='upi' and UPI parameters with flow='collect' and expiry_time='6' (e.g., '9876543210@ptsbi') |
| `upi_intent` | boolean | — | Enable UPI intent flow. When set to true, automatically sets method='upi' and UPI parameters with flow='intent'. The API will return a UPI URL in the response. |
| `recurring` | boolean | — | Set this to true for recurring payments like single block multiple debit. |
| `force_terminal_id` | string | — | Terminal ID to be passed in case of single block multiple debit order. |

## `resend_otp`

**Write** · remote ✅ · `POST /v1/payments/{id}/otp/resend`

> Resend OTP to the customer's registered mobile number if the previous OTP was not received or has expired.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | REQUIRED | Unique identifier of the payment for which OTP needs to be generated. Must start with 'pay_' |

## `submit_otp`

**Write** · remote ✅ · `POST /v1/payments/{id}/otp/submit`

> Verify and submit the OTP received by the customer to complete the payment authentication process.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `otp_string` | string | REQUIRED | OTP string received from the user |
| `payment_id` | string | REQUIRED | Unique identifier of the payment for which OTP needs to be submitted. Must start with 'pay_' |

## `fetch_tokens`

**Write** · remote ✅ · `GET /v1/customers/{id}/tokens` ³

> Get all saved payment methods (cards, UPI) for a customer. Accepts either a customer_id (preferred) or a contact number. When customer_id is provided it is used directly to fetch tokens; otherwise the contact number is used to find or create the customer first. Returns saved payment tokens including credit/debit cards, UPI IDs, digital wallets, and other tokenized payment instruments.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `customer_id` | string | — | Razorpay customer ID to fetch saved payment methods for. Must start with 'cust_' followed by alphanumeric characters. Example: 'cust_xxx'. When provided, this takes priority over the contact parameter. |
| `contact` | string | — | Contact number of the customer to fetch all saved payment methods for. For example, 9876543210 or +919876543210. Used only when customer_id is not provided. |

## `revoke_token`

**Write** · remote ✅ · `PUT /v1/customers/{c}/tokens/{t}/cancel`

> Revoke a saved payment method (token) for a customer. This tool revokes the specified token associated with the given customer ID. Once revoked, the token cannot be used for future payments.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `customer_id` | string | REQUIRED | Customer ID for which the token should be revoked. Must start with 'cust_' followed by alphanumeric characters. Example: 'cust_xxx' |
| `token_id` | string | REQUIRED | Token ID of the saved payment method to be revoked. Must start with 'token_' followed by alphanumeric characters. Example: 'token_xxx' |
