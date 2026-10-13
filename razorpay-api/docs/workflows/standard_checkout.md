# Workflow: Standard Checkout (web/app)

> **When to load**: integrating "Pay with Razorpay" into a website or app, or reviewing such an
> integration.

## Sequence

```
Browser ──(cart id)──▶ Your server ──create order (amount from DB)──▶ Razorpay  → order_id
Browser ◀──(order_id, key_id, amount)── Your server
Browser ──Checkout.js(order_id)──▶ Razorpay ──handler(payment_id, order_id, signature)──▶ Browser
Browser ──(3 fields)──▶ Your server /verify  → HMAC check → mark order paid (idempotent)
Razorpay ──webhook order.paid──▶ Your server /webhook  → source of truth (covers lost callbacks)
```

## Checklist

1. **Keys**: `rzp_test_…` for dev. Secret only on the server (env var / secret manager).
2. **Create order server-side**: `amount` in paise from *your* DB; persist `order_id` against your
   order before returning it. (MCP: `create_order` for manual tests only.)
   To pass Razorpay's processing fee to the payer (for example on card payments), add
   `convenience_fee_config` to this REST call: Dynamic Convenience Fees in
   [orders.md](../api/orders.md#dynamic-convenience-fees-rest-only). Razorpay Support must enable
   the feature first, it is INR only, and it is not available for Smart Collect (QR codes
   included), Route or Subscriptions. When the payer bears a fee, the total charged is the order
   amount plus that fee. The official pages show no payment sample for that case, so check in test
   mode how `amount`, `base_amount` and `fee` come back before you write the amount assertion of
   step 4.
3. **Frontend**:
   ```html
   <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
   <script>
     const rzp = new Razorpay({
       key: keyId, order_id: orderId, amount, currency: "INR", name: "Shop",
       handler: (r) => fetch("/api/payments/verify", { method: "POST",
         headers: { "Content-Type": "application/json" }, body: JSON.stringify(r) }),
       modal: { ondismiss: () => { /* show "payment not completed" */ } }
     });
     rzp.on("payment.failed", (e) => console.warn(e.error.reason));
     rzp.open();
   </script>
   ```
   `checkout.js` is served unversioned and updated in place by Razorpay, so a pinned `integrity`
   (SRI) hash will break; constrain it with a CSP (`script-src` / `frame-src` allowing
   `https://checkout.razorpay.com` and `https://api.razorpay.com`) instead.
4. **Verify** (`/verify`): find your order **by the returned `razorpay_order_id`**, HMAC
   `order_id|payment_id` with the key secret, constant-time compare, mark paid idempotently.
   Hardening: `fetch_payment` / `payments.fetch` and assert `order_id`, `amount`, `currency` match and
   `status` is `captured` (or `authorized` if you capture manually).
5. **Webhook**: subscribe to `order.paid`, `payment.captured`, `payment.failed` (+ `refund.*`);
   raw-body HMAC with the webhook secret; dedupe on `x-razorpay-event-id`; ack within 5 s.
6. **Capture**: enable auto-capture in Dashboard, or call `capture_payment` / `payments.capture` —
   authorized payments auto-refund after 3 days.
7. **Backstop**: scheduled job re-checks orders unpaid after N minutes via
   `fetch_order_payments` / `GET /v1/orders/{id}/payments`.
8. **Test**: official test cards Visa `4100 2800 0000 1007`, Mastercard `5500 6700 0000 1002`,
   RuPay `6527 6589 0000 1005` (any CVV, any future expiry); UPI `success@razorpay` to succeed and
   `failure@razorpay` to fail. Full list and notes: [conventions.md](../common/conventions.md#test-mode).
   Then switch to live keys and a live-mode webhook URL.

Code for steps 2, 4 and 5 (Spring Boot): [signatures-and-webhooks.md](../common/signatures-and-webhooks.md).
Scaffolding via MCP: `detect_stack` → `integrate_razorpay_checkout`, then apply the fixes in
[checkout_integration.md](../api/checkout_integration.md).
