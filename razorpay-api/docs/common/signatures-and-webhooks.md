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
Other families (subscriptions, disputes, settlements, invoices, Route, Smart Collect, payouts) and
sample payloads: [index/webhooks.md](../index/webhooks.md) → `webhooks/all.md`.

Delivery rules (Razorpay webhook best-practices doc):
- **At-least-once**: duplicates are normal → dedupe on `x-razorpay-event-id`.
- **5-second timeout**: no 2xx within 5 s counts as failed and is resent → ack fast, process async.
  Any non-2xx answer also counts as failed.
- **Retries** with exponential backoff for 24 h after event creation; still failing → the webhook is
  **disabled** (alert email) and must be re-enabled in Dashboard.
- **Out of order** is possible (e.g. `payment.captured` after `order.paid`) → make state transitions
  monotonic (never move `PAID` back to `CREATED`).
- **`payment.failed` is not final**: `payment.failed` followed by `payment.captured` for the same
  payment is documented as expected behaviour (late authorisation, or the payer retrying inside
  the UPI app). A later `captured` must win over an earlier `failed`.
- After rotating the webhook secret, verify retries of older events with the old secret.
- Razorpay Support can replay a single event for up to 15 days; there is no bulk replay.
- Port 80/443 only; separate webhook URLs for test and live mode.

If a user-facing screen needs the result before the webhook lands, call `fetch_order` /
`fetch_payment` — don't trust the client. Backstop: a scheduled job that re-checks orders still
unpaid after N minutes via `GET /v1/orders/{id}/payments`.

## Payload shapes (official samples)

Envelope: `entity: "event"`, `account_id`, `event`, `contains[]`, `payload`, `created_at`.
`contains[]` names the keys present under `payload`; each key holds one `entity` object. A payload
is a snapshot of the entity when the event occurred, not its current state.

| Event | `contains[]` | Fields to read |
|---|---|---|
| `order.paid` | `payment`, `order` | `order.entity`: `id` (`order_…`), `amount_paid`, `amount_due`, `status: "paid"`; payment as in the next row |
| `payment.authorized`, `payment.captured`, `payment.failed` | `payment` | `id`, `status`, `order_id`, `amount`, `method`, `error_*`; on `payment.captured` also `base_amount`, `fee`, `tax` (paise) and `acquirer_data` |
| `payment_link.paid`, `payment_link.partially_paid` | `payment_link`, `order`, `payment` | `payment_link.entity`: `id`, `status`, `amount`, `amount_paid`, `reference_id`, `order_id`, `upi_link`, `notes`; `payment.entity`: `id`, `status`, `order_id`, `base_amount`, `fee`, `tax`, `acquirer_data` |
| `payment_link.cancelled`, `payment_link.expired` | `payment_link` | `id`, `status`, `reference_id`, `cancelled_at` / `expired_at` |
| `qr_code.credited` | `payment`, `qr_code` | `payment.entity`: `id`, `status: "captured"`, `amount`, `order_id: null`, `vpa`, `acquirer_data.rrn`; `qr_code.entity.id` |
| `qr_code.created`, `qr_code.closed` | `qr_code` | `id`, `status`, `close_by`, `closed_at`, `close_reason` |
| `refund.created`, `refund.processed`, `refund.failed`, `refund.speed_changed` | `refund`, `payment` | `refund.entity`: `id`, `payment_id`, `amount`, `status`, `speed_requested`, `speed_processed`, `receipt`, `acquirer_data.arn`; `payment.entity`: `amount_refunded`, `refund_status` |

`acquirer_data` depends on the method: `rrn` (UPI), `bank_transaction_id` (netbanking),
`auth_code` + `rrn` (card), `transaction_id` (wallet), `arn` (refund).

Traps, each one visible in the official sample payloads:
- **`notes` is not reliably an object.** It arrives as `[]` when empty (payment, order and refund
  samples), as `null` (payment-link samples), as `{}` (refund API response) or as an object.
  `acquirer_data` can be `{}`. Parse both leniently.
- **Order id without prefix.** In `payment_link.*` events `payload.order.entity.id` has no
  `order_` prefix (`"QflczVVaNJciLq"`), while `payment.entity.order_id` and
  `payment_link.entity.order_id` carry it (`"order_QflczVVaNJciLq"`). In `order.paid` the order id
  has the prefix. Normalise before comparing.
- **Stale QR snapshot.** The `qr_code.credited` sample carries a `qr_code` entity with
  `status: "active"`, `payments_amount_received: 0` and `payments_count_received: 0` although the
  payment beside it is `captured`. Take the money facts from `payload.payment.entity`.
- **`qr_code.closed` fires only on a manual close**, not when the QR auto-expires. The
  `qr_code.created` sample shows `close_by` as a string; the other QR samples show an integer.
- **`refund.speed_changed` has no top-level `created_at`**: in the sample it sits inside `payload`.
  Its refund entity shows `notes: []`, `acquirer_data: {}` and no `batch_id`. The `refund.created`
  sample already shows `status: "processed"`.
- **Map by the `status` word, never by `captured` alone.** The Card samples of `payment.failed` and
  `payment.authorized` both show `captured: true`, and their `error_code` is `""`, not `null`.
- **`fee`, `tax` and `base_amount` are optional.** The Card sample of `payment.captured` has
  `fee: null`, `tax: null` and no `base_amount`; the netbanking, wallet and UPI samples have all
  three.
- Key order differs between samples (the Card samples are alphabetical), and the payments page
  says the sequence "is not fixed in the JSON payload". Never depend on it.

## Staff-generated links and QR codes: webhook → queue + status poller

No browser returns to your server in this flow, so confirmation rests on two paths that end in the
same idempotent state transition:

1. **Webhook → queue.** The endpoint verifies the HMAC on the raw body, puts the raw event and its
   `x-razorpay-event-id` on a queue (for example SQS) and answers 2xx within 5 seconds. A consumer
   dedupes on the event id and applies the change. Events: `payment_link.paid`,
   `payment_link.partially_paid`, `payment_link.expired`, `payment_link.cancelled`,
   `qr_code.credited`, `qr_code.closed`.
2. **REST status poller.** A scheduled job re-reads every link or QR that your DB still shows as
   open after N minutes: `GET /v1/payment_links/{id}` (`status`, `amount_paid`, `payments[]`),
   `GET /v1/payments/qr_codes/{id}/payments` and `GET /v1/payments/qr_codes/{id}` (`status`,
   `close_reason`). The poller is required, not optional: an auto-expired QR sends no webhook, a
   webhook disabled after 24 hours of failures sends nothing, and events can arrive late or out of
   order.

Match a link event by `payment_link.entity.id` or your `reference_id`. Match a QR payment by
`qr_code.entity.id`, because its `order_id` is `null`. Field limits:
[payment_links.md](../api/payment_links.md), [qr_codes.md](../api/qr_codes.md).

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
