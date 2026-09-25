# Workflow: refunds (single and bulk)

> **When to load**: any request to refund — one payment, a partial amount, or "refund everything
> from X".

## Before any refund call (live or test)

1. **Resolve the targets read-only**: `fetch_payment` (one) or `fetch_all_payments` with `from`/`to`
   (Unix seconds; state the timezone you assumed) paged with `count: 100` + `skip` until empty.
2. **Filter**: keep `status == "captured"` and `amount_refunded < amount`. Skip `authorized` (they
   auto-refund) and `failed`.
3. **Show the user** the list: payment id, ₹ amount (and paise), already refunded, what will be
   refunded, total, `speed`. If key is `rzp_live_`, say so explicitly.
4. **Get explicit confirmation of that exact list.** Ambiguous scope ("everything") → stop at the
   report.

## Executing

- Hosted MCP has no `create_refund`. Use the local MCP, the Dashboard, or backend
  `POST /v1/payments/{id}/refund` (`payments.refund(id, {amount, speed, notes})`).
- One call per payment; record each result before the next. A retry after a timeout can double-refund:
  check `fetch_multiple_refunds_for_payment` before retrying. `receipt` is not an idempotency key.
- `speed: "optimum"` for instant (where supported), else `normal`.

## After

Track `refund.processed` / `refund.failed` webhooks or `fetch_refund`. Report: succeeded, failed
(with `error.description`), total refunded.
