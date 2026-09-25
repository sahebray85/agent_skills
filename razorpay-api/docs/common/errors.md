# Errors and troubleshooting

> **When to load**: a Razorpay MCP tool or REST call failed, a tool is "missing", or a signature
> doesn't verify.

## Shape

Success is HTTP 200 (some creates return 201/202). Failures return:

```json
{ "error": { "code": "BAD_REQUEST_ERROR", "description": "…", "field": null,
             "source": "customer", "step": "payment_authentication", "reason": "invalid_otp",
             "metadata": { "payment_id": "pay_…", "order_id": "order_…" } } }
```

`code` ∈ `BAD_REQUEST_ERROR` (fix the request — do not retry as-is), `GATEWAY_ERROR`,
`SERVER_ERROR` (retry with backoff). Branch on `reason` programmatically; show `description` to
operators, not customers. HTTP 429 = throttled → exponential backoff.

The MCP server wraps failures as a tool **error result** with text like
`creating order failed: <razorpay description>` or `missing required parameter: amount` — schema
violations (paise minimums, ID patterns, enums) are rejected before any API call.

## Symptom → cause → fix

| Symptom | Likely cause | Fix |
|---|---|---|
| 401 / "Authentication failed" on remote | token built with `echo` (trailing `\n`), wrong pair, or key/secret from different modes | rebuild with `printf '%s:%s'` — see [setup.md](setup.md) |
| "The id provided does not exist" | object from the other mode (test vs live), or wrong prefix | check key prefix `rzp_test_`/`rzp_live_` against where the object was created |
| Tool not listed | remote lacks it (`create_refund`, `close_qr_code`, `create_instant_settlement`, `create_registration_link`), `READ_ONLY`/OAuth `read_only`, `TOOLSETS` filter, or you used a README name | see [REFERENCE.md](../../REFERENCE.md) name-drift table; use local server |
| Capture rejected | payment not `authorized` (already captured / failed / auto-refunded after 3 days) or amount ≠ authorized amount | `fetch_payment` first; capture exactly `amount` from it |
| Refund rejected | payment not `captured`, or sum of refunds > captured amount | `fetch_multiple_refunds_for_payment` to see what's already refunded |
| Signature mismatch (checkout) | used `payment_id\|order_id` order, client-sent order id, or key secret from other mode | message is `order_id\|payment_id`, key = API key secret of the same mode |
| Signature mismatch (webhook) | body parsed/re-serialized, or used API key secret | HMAC the raw bytes with the **webhook** secret |
| UPI link/QR rejected | non-INR currency | INR only |
| `initiate_payment` sent an OTP unexpectedly | the tool auto-triggers the OTP URL returned in `next` | expected; follow with `submit_otp` / `resend_otp` |
| New customer appeared after `fetch_tokens` | called with `contact` only → tool does `POST /v1/customers` | pass `customer_id` when you have it |
