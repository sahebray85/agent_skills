# Signatures and webhooks

> **When to load**: writing/reviewing checkout verification, a payment-link callback, or a webhook
> endpoint; debugging "signature mismatch"; deciding how the backend learns a payment succeeded.

The MCP server has **no webhook tools** and its generated checkout code has **no webhook handler**.
You must add one — the browser callback is not guaranteed to reach your server (tab closed,
network drop, UPI app switch).

## Signature formulas (all HMAC-SHA256, lowercase hex)

| Flow | Message | Key |
|---|---|---|
| Standard Checkout handler | `order_id + "\|" + razorpay_payment_id` — `order_id` from **your DB**, not the request | API key secret |
| Payment Link callback | `payment_link_id\|payment_link_reference_id\|payment_link_status\|razorpay_payment_id` | API key secret |
| Subscription checkout | `razorpay_payment_id\|subscription_id` | API key secret |
| Webhook | the **raw request body**, byte-for-byte | **Webhook secret** (set per webhook in Dashboard — not the key secret) |

Webhook headers: `X-Razorpay-Signature` (signature), `x-razorpay-event-id` (unique per event — dedupe
on it; deliveries can repeat). Never parse/re-serialize the body before verifying.

## Events worth subscribing to

`order.paid` (fulfil on this) · `payment.authorized` · `payment.captured` · `payment.failed` ·
`refund.created` · `refund.processed` · `refund.failed` · `refund.speed_changed` ·
`payment_link.paid` · `payment_link.partially_paid` · `payment_link.expired` ·
`payment_link.cancelled` · `qr_code.created` · `qr_code.credited` · `qr_code.closed`.

Delivery rules (Razorpay webhook best-practices doc):
- **At-least-once**: duplicates are normal → dedupe on `x-razorpay-event-id`.
- **5-second timeout**: no 2xx within 5 s counts as failed and is resent → ack fast, process async.
- **Retries** with exponential backoff for 24 h after event creation; still failing → the webhook is
  **disabled** (alert email) and must be re-enabled in Dashboard.
- **Out of order** is possible (e.g. `payment.captured` after `order.paid`) → make state transitions
  monotonic (never move `PAID` back to `CREATED`).
- Port 80/443 only; separate webhook URLs for test and live mode.

If a user-facing screen needs the result before the webhook lands, call `fetch_order` /
`fetch_payment` — don't trust the client. Backstop: a scheduled job that re-checks orders still
unpaid after N minutes via `GET /v1/orders/{id}/payments`.

## Spring Boot reference implementation

```java
@RestController
@RequestMapping("/api/payments")
@RequiredArgsConstructor
class RazorpayController {
    private final RazorpayClient razorpay;             // new RazorpayClient(keyId, keySecret) bean
    private final ShopOrderRepository orders;          // your persistence
    private final WebhookEventRepository seenEvents;   // unique index on event_id
    @Value("${razorpay.key-id}") String keyId;
    @Value("${razorpay.key-secret}") String keySecret;
    @Value("${razorpay.webhook-secret}") String webhookSecret;

    /** Client sends only its cart/order id. The price comes from the server. */
    @PostMapping("/orders")
    Map<String, Object> createOrder(@RequestBody CreatePaymentRequest req) throws RazorpayException {
        ShopOrder order = orders.findPayableById(req.shopOrderId()).orElseThrow();
        long paise = order.totalPaise();                           // long paise, never double rupees
        Order rzp = razorpay.orders.create(new JSONObject()
                .put("amount", paise).put("currency", "INR")
                .put("receipt", order.id())                        // ≤ 40 chars, unique
                .put("notes", new JSONObject().put("shop_order_id", order.id())));
        order.attachRazorpayOrderId(rzp.get("id"));
        orders.save(order);
        return Map.of("orderId", rzp.get("id"), "amount", paise, "currency", "INR", "keyId", keyId);
    }

    /** Fast path for the UI. The webhook below is the source of truth. */
    @PostMapping("/verify")
    ResponseEntity<Void> verify(@RequestBody CheckoutResult r) {
        ShopOrder order = orders.findByRazorpayOrderId(r.razorpayOrderId()).orElse(null);
        if (order == null || !Hmac.matches(
                (order.razorpayOrderId() + "|" + r.razorpayPaymentId()).getBytes(UTF_8),
                r.razorpaySignature(), keySecret)) {
            return ResponseEntity.badRequest().build();
        }
        order.markPaid(r.razorpayPaymentId());                     // idempotent state transition
        orders.save(order);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/webhook")
    ResponseEntity<Void> webhook(@RequestBody byte[] rawBody,       // raw bytes, not a DTO
                                 @RequestHeader("X-Razorpay-Signature") String signature,
                                 @RequestHeader("x-razorpay-event-id") String eventId) {
        if (!Hmac.matches(rawBody, signature, webhookSecret)) return ResponseEntity.badRequest().build();
        if (!seenEvents.insertIfAbsent(eventId)) return ResponseEntity.ok().build();  // duplicate
        JSONObject event = new JSONObject(new String(rawBody, UTF_8));
        JSONObject payload = event.getJSONObject("payload");
        switch (event.getString("event")) {
            case "order.paid" -> {
                String orderId = payload.getJSONObject("order").getJSONObject("entity").getString("id");
                String paymentId = payload.getJSONObject("payment").getJSONObject("entity").getString("id");
                orders.findByRazorpayOrderId(orderId).ifPresent(o -> { o.markPaid(paymentId); orders.save(o); });
            }
            case "payment.failed" -> { /* record failure; customer may retry on same order */ }
            case "refund.processed", "refund.failed" -> { /* update refund row by payload.refund.entity.id */ }
            default -> { }
        }
        return ResponseEntity.ok().build();                        // 2xx quickly; heavy work async
    }
}

final class Hmac {
    static boolean matches(byte[] message, String signatureHex, String secret) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(UTF_8), "HmacSHA256"));
            byte[] expected = mac.doFinal(message);
            return MessageDigest.isEqual(expected, HexFormat.of().parseHex(signatureHex)); // constant-time
        } catch (IllegalArgumentException | NullPointerException e) {
            return false;                                          // missing or non-hex signature
        } catch (GeneralSecurityException e) {
            throw new IllegalStateException(e);
        }
    }
}
```

Why each line matters: the amount is looked up server-side (a client-supplied amount lets a user pay
₹1 for anything); the order marked paid is the one found **by the signed `order_id`** — never a
separately supplied shop-order id, or a genuine signature from a cheap order unlocks an expensive one; `MessageDigest.isEqual` avoids timing leaks (`String.equals` does not);
`byte[]` keeps the body exactly as signed; `x-razorpay-event-id` makes retries harmless.
