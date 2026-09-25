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
| instant settlement `description` | ≤ 30 chars, `^[a-zA-Z0-9 ]*$` |
| list `count` / `skip` | count 1–100 (default 10), skip ≥ 0 |
| `from` / `to` / `expire_by` / `close_by` | Unix **seconds** |

Only `notes` can be updated on orders, payments and refunds (`update_*` tools).

## Lifecycles

**Payment**: `created → authorized → captured → refunded`, or `failed`.
- `authorized` = bank approved, money **not** yours yet. Razorpay auto-refunds an authorized payment
  not captured within **3 days of creation** (per Razorpay docs). Either enable auto-capture
  (Dashboard → capture settings) or call `capture_payment`.
- Only `captured` payments can be refunded.

**Order**: `created → attempted → paid`. An order can have several failed payments before one
succeeds — use `fetch_order_payments`, not "the" payment.

**Refund**: `pending → processed` or `failed`. `speed: "optimum"` requests instant where possible.

**Payment link**: `created`, `partially_paid`, `paid`, `expired`, `cancelled`.
**QR code**: `active` → `closed`.

## Test mode

Key IDs `rzp_test_…`. Test card `4111 1111 1111 1111` (any future expiry, any CVV); test UPI VPA
`success@razorpay` (from the MCP's own checkout templates). Test objects are invisible to live keys.
