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
8. **Test**: card `4111 1111 1111 1111`, UPI `success@razorpay`; then switch to live keys and a
   live-mode webhook URL.

Code for steps 2, 4 and 5 (Spring Boot): [signatures-and-webhooks.md](../common/signatures-and-webhooks.md).
Scaffolding via MCP: `detect_stack` → `integrate_razorpay_checkout`, then apply the fixes in
[checkout_integration.md](../api/checkout_integration.md).
