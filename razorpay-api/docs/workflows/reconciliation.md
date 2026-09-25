# Workflow: "charged but not paid" triage and settlement reconciliation

> **When to load**: customer says money was debited but the order shows unpaid; daily/monthly
> reconciliation; "where is my money"; settlement amount doesn't match sales.

## Customer charged, order unpaid

1. `fetch_order(order_id)` → `status`, `amount_paid`, `attempts`.
2. `fetch_order_payments(order_id)` → every attempt. Classify:
   - `captured` → Razorpay has it. Your system missed the callback/webhook → mark paid, then fix the
     webhook (check it isn't **disabled** after 24 h of failures).
   - `authorized` → not captured. Capture now (`capture_payment` with the exact amount) or let it
     auto-refund (3 days). Enable auto-capture to stop recurrences.
   - `failed` → no money taken by Razorpay; bank reversal is the bank's timeline. Show
     `error_description` / `error_reason`.
   - nothing listed → the debit wasn't for this order; search `fetch_all_payments` by time window
     and filter yourself on `contact` / `email` / `amount` (the tool has no such filters) — a retry
     may have created a second order.
   - To match the customer's bank statement, use the payment's `acquirer_data`: `rrn` (bank
     reference number), `bank_transaction_id` (netbanking), `auth_code` (cards).
3. Two `captured` payments on one order → refund the duplicate (see [refunds.md](refunds.md)).

## Settlement reconciliation

1. `fetch_all_settlements(from, to)` → settlements with `amount`, `fees`, `tax`, `utr`.
2. `fetch_settlement_recon_details(year, month[, day])` → row-level: each payment / refund /
   adjustment with its `settlement_id`, fee and tax.
3. Match rows to your orders via `order_id` / payment `notes` (put your own order id in `notes` at
   order creation to make this trivial).
4. Differences are usually fees + GST, refunds deducted, disputes/adjustments, or payments captured
   after the settlement cut-off (next cycle).

Instant settlement (`create_instant_settlement`, local only) moves money — confirm with the user.
