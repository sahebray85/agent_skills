# Conventions: money, IDs, limits, lifecycles

> **When to load**: converting amounts, validating args before a tool call, interpreting a status.

## Money

- Every `amount` is an **integer in the smallest currency unit** (paise for INR): ₹499.50 → `49950`.
- Convert once, at the edge, with decimal math — never `(int)(rupees * 100)` on a `double`
  (`19.99 * 100 = 1998.9999…` → `1998`). Better: carry paise as `long` end-to-end.
  ```java
  long paise = new BigDecimal("499.50").movePointRight(2).longValueExact(); // 49950
  ```
- `currency`: 3 uppercase letters (`^[A-Z]{3}$`). UPI links and UPI QR are INR only.
- Minimums enforced by the MCP schema: order / payment link / refund / `initiate_payment` = **100**;
  instant settlement = **200**; QR `payment_amount` = **1**. `capture_payment.amount` must equal the
  authorized amount.
- Responses are also in paise — divide by 100 only for display.

## Common field limits

| Field | Limit |
|---|---|
| `notes` | ≤ 15 keys, each value ≤ 256 chars; string/int values |
| `receipt` (orders) | ≤ 40 chars, unique per order |
| `receipt` (refunds) | idempotency key per payment: a repeat is rejected ("Duplicate receipt found for this refund request.") |
| `reference_id` (payment links) | ≤ 40 chars, unique per link |
| `expire_by` (payment links) | ≥ 15 minutes ahead, ≤ 6 months after creation |
| `close_by` (QR codes) | 2 or 15 minutes ahead depending on the source: see [qr_codes.md](../api/qr_codes.md) |
| instant settlement `description` | ≤ 30 chars, `^[a-zA-Z0-9 ]*$` |
| list `count` / `skip` | count 1–100 (default 10), skip ≥ 0 |
| `from` / `to` / `expire_by` / `close_by` | Unix **seconds** |

Only `notes` can be updated on orders, payments and refunds (`update_*` tools).

Reading `notes`: official samples return an empty `notes` as `[]` (payments, orders, refunds), and
payment-link payloads return `null`. A field typed as a map fails on `[]`; in Jackson enable
`ACCEPT_EMPTY_ARRAY_AS_NULL_OBJECT` or write a custom deserializer.

## Lifecycles

**Payment**: `created → authorized → captured → refunded`, or `failed`.
- `authorized` = bank approved, money **not** yours yet. Razorpay auto-refunds an authorized payment
  not captured within **3 days of creation** (per Razorpay docs). Either enable auto-capture
  (Dashboard → capture settings) or call `capture_payment`.
- Only `captured` payments can be refunded.

**Order**: `created → attempted → paid`. An order can have several failed payments before one
succeeds — use `fetch_order_payments`, not "the" payment. `attempted` lasts until a payment is
**captured**; the order stays `paid` even if that payment is later refunded.

**Refund**: `pending → processed` or `failed`. `speed: "normal"` (default) takes 5–7 working days;
`speed: "optimum"` requests instant where possible, and `speed_processed` (`instant` | `normal`)
in the response says which route was used. A normal refund **fails for payments older than
6 months**; instant refunds can also fail on customer-account or bank issues.

**Payment link**: `created`, `partially_paid`, `paid`, `expired`, `cancelled`. UPI links take no
partial payments, so they never reach `partially_paid`.
**QR code**: `active` → `closed`, with `close_reason` `on_demand` or `paid` (one official page also
lists `expired`).

## Test mode

Key IDs `rzp_test_…`. Test objects are invisible to live keys.

Official test cards for Indian payments. Use any CVV and any future expiry; on the mock bank page
an OTP of 4 to 10 digits makes the payment succeed and a shorter one makes it fail.

| Network | Card number | Listed on |
|---|---|---|
| Visa | `4100 2800 0000 1007` | all three pages below |
| Mastercard | `5500 6700 0000 1002` | Standard Checkout integration steps; international test-card page |
| Mastercard | `5555 5100 0008 1006` (credit), `5180 2872 0009 1001` (prepaid) | `payments/payments/test-card-details.md` |
| RuPay | `6527 6589 0000 1005` | all three pages below |

Pages: `payments/payments/test-card-details.md` (also the error-scenario cards),
`payments/payment-gateway/web-integration/standard/integration-steps.md`,
`payments/international-payments/accept-international-payments-from-indian-customers/s2s-integration/test-card-details.md`,
all under `https://razorpay.com/docs/build/llm-docs/`. The pages disagree on the Mastercard
number, so try the other one if the first is refused. Used with live keys, a test card fails with
`card issuer is invalid` or `invalid card input`.

Test UPI IDs: `success@razorpay` (payment succeeds), `failure@razorpay` (payment fails). In test
mode a cancelled UPI payment is recorded as successful; test cancellation in live mode. UPI Payment
Links do not work in test mode at all.

`4111 1111 1111 1111`, which the MCP checkout templates print in their test instructions, is not on
any of these pages. Use the cards above.
