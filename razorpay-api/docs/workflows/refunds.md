# Workflow: refunds (single and bulk)

> **When to load**: any request to refund — one payment, a partial amount, or "refund everything
> from X".

## Before any refund call (live or test)

1. **Resolve the targets read-only**: `fetch_payment` (one) or `fetch_all_payments` with `from`/`to`
   (Unix seconds; state the timezone you assumed) paged with `count: 100` + `skip` until empty.
2. **Filter**: keep `status == "captured"` and `amount_refunded < amount`. Skip `authorized` (they
   auto-refund) and `failed`: Razorpay refunds only `captured` payments. Flag payments created more
   than 6 months ago, because a `normal` refund on them fails.
3. **Show the user** the list: payment id, ₹ amount (and paise), already refunded, what will be
   refunded, total, `speed`. If key is `rzp_live_`, say so explicitly.
4. **Get explicit confirmation of that exact list.** Ambiguous scope ("everything") → stop at the
   report.

## Executing

- Hosted MCP has no `create_refund`. Use the local MCP, the Dashboard, or backend
  `POST /v1/payments/{id}/refund` (`payments.refund(id, {amount, speed, notes, receipt})`).
- One call per payment; record each result before the next. Write your own refund row first, then
  call with a stable `receipt` taken from that row. `receipt` is a per-payment idempotency key:
  Razorpay rejects a second refund with the same `receipt` on the same payment ("Duplicate receipt
  found for this refund request."). That answer to a retry means an earlier call went through, so
  look the refund up instead of reporting a failure. From REST, also send `X-Refund-Idempotency`
  with the same key on every retry (details in [api/refunds.md](../api/refunds.md)).
- A retry after a timeout can still double-refund when the first call carried no `receipt`: check
  `fetch_multiple_refunds_for_payment` before retrying, and keep the guard row in your own DB.
- `speed: "optimum"` for instant (where supported), else `normal`. Check `speed_processed` in the
  response: `normal` there means instant was not available and the customer waits 5-7 working
  days.

## After

Track `refund.processed` / `refund.failed` webhooks or `fetch_refund`. Both events carry the refund
and its payment (`contains: ["refund", "payment"]`). Report: succeeded, failed (with
`error.description`), total refunded.
