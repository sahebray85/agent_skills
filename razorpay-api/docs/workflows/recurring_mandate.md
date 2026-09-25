# Workflow: recurring payments (UPI Autopay, e-mandate, NACH, cards)

> **When to load**: subscriptions, auto-debit, mandates, saved-token charging, "charge the customer
> every month".

## Choose the route

| Goal | MCP route | Notes |
|---|---|---|
| UPI Autopay mandate authorised in Checkout | `create_order` with `method:"upi"`, `customer_id`, `token{max_amount, frequency, type:"single_block_multiple_debit"}` | all three fields mandatory together; customer must exist (`cust_…`) |
| Mandate authorised via hosted link (card / emandate / NACH / UPI) | `create_registration_link` | **local server only** |
| See / cancel a customer's saved mandate or card | `fetch_tokens(customer_id)` → `revoke_token` | revoke is irreversible |
| Charge a saved mandate (subsequent debit, INR) | **not via MCP** — backend | MCP's `initiate_payment` routes to `/create/recurring` only for non-INR |
| Plans + Subscriptions product | **not in MCP** — REST `/v1/plans`, `/v1/subscriptions` | subscription checkout signature: `payment_id\|subscription_id` |

## Subsequent debit from your backend (INR)

1. Create a new order for this cycle **from the backend** — the MCP's `create_order` has no
   `payment_capture` / `notification` params:
   ```json
   POST /v1/orders
   { "amount": 29900, "currency": "INR", "receipt": "sub_42_2026_09", "payment_capture": true,
     "notification": { "token_id": "token_…", "payment_after": 1790500000 } }
   ```
   `amount` ≤ the mandate's `max_amount`. `notification` is optional: without it Razorpay debits
   ~25 h after the pre-debit notification is delivered; `payment_after` (Unix s) sets the earliest
   debit time.
2. Charge the token:
   ```java
   Payment p = razorpay.payments.createRecurringPayment(new JSONObject()
       .put("email", c.email()).put("contact", c.contact())
       .put("amount", cyclePaise).put("currency", "INR")
       .put("order_id", cycleOrderId).put("customer_id", c.razorpayCustomerId())
       .put("token", c.razorpayTokenId()).put("recurring", true)
       .put("description", "Plan renewal " + period));
   ```
   (`POST /v1/payments/create/recurring`; `recurring` is the boolean `true` and
   `payments.createRecurringPayment` is the razorpay-java method — both from Razorpay's official
   sample.) Guard against double debits yourself: one cycle order per period in your DB, and on a
   timeout check `fetch_order_payments` before charging again.
3. Result arrives asynchronously: rely on `payment.captured` / `payment.failed` / `order.paid`
   webhooks, not the synchronous response.

UPI timing rules (Razorpay subsequent-payments doc): notify the customer ~24 h before the debit;
a UPI debit can take **24–36 h** to show; **never create the debit on the last day of the mandate
cycle** (it fails); `mandate_current_cycle_allowed_debit_exceeds` → wait for the next cycle.

Not in this skill — fetch the official page for: token entity fields (mandate status,
`max_amount`, expiry), exact pre-debit notification behaviour, cycle boundaries, and the full
mandate error-code list. Official detail (raw markdown): `https://razorpay.com/docs/build/llm-docs/api/payments/recurring-payments.md`
and `.../recurring-payments/upi/create-subsequent-payments.md`.
