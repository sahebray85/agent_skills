---
name: razorpay-api
description: Reference for the official Razorpay MCP server (all 45 tools) and the Razorpay payment REST APIs behind it - orders, payments, capture, refunds, payment links, UPI QR codes, settlements, payouts, saved tokens, mandates/recurring, Standard Checkout, signature and webhook verification. Use when the user mentions Razorpay, the Razorpay MCP, rzp_test_/rzp_live_ keys, or IDs like pay_, order_, plink_, rfnd_, qr_, setl_; when integrating or debugging a Razorpay payment gateway (checkout, verify signature, webhooks, UPI Autopay, e-mandate); when running refunds or settlement reconciliation; or when a Razorpay MCP tool is missing, renamed or failing.
---

# Razorpay API Skill

## Source of truth

1. **Tool list your MCP client actually shows** — wins for tool *names* (docs and code disagree, see
   REFERENCE.md "Name drift").
2. **This skill's local docs** — default reference, read directly. `REFERENCE.md` and the tool
   sections of `docs/api/*.md` are generated from `razorpay-mcp-server` source
   (refresh: `scripts/refresh_tool_docs.py`).
3. **Official MCP tools list** `https://razorpay.com/docs/mcp-server/tools-reference.md` (39 tools; omits 6 — see REFERENCE.md) and **official raw-markdown docs** when a detail is missing: look the page up in the local
   [docs index](docs/index/README.md) (all pages of `https://razorpay.com/docs/llms.txt`, by family) and fetch
   its URL; any `razorpay.com/docs/api/<path>` page ↔ `razorpay.com/docs/build/llm-docs/api/<path>.md`.
   Refresh the index: `scripts/refresh_llms_index.py`.

Local docs are a snapshot. If they disagree with the official page, **the official page wins** —
say so to the user and suggest re-running `scripts/refresh_tool_docs.py`.

## First: is the MCP there, and which mode?

- No `razorpay` tools listed → [docs/common/setup.md](docs/common/setup.md).
- Mode = key prefix: `rzp_test_…` test, `rzp_live_…` **real money**. Same URL for both.
- Hosted server (`https://mcp.razorpay.com/mcp`) lacks `create_refund`, `close_qr_code`,
  `create_instant_settlement`, `create_registration_link` → local server, Dashboard, or REST.

## Toolsets (45 tools)

| Toolset | Read | Write | Doc |
|---|---|---|---|
| payments | fetch_payment, fetch_payment_card_details, fetch_all_payments | capture_payment, update_payment, initiate_payment, resend_otp, submit_otp, fetch_tokens, revoke_token | [payments](docs/api/payments.md) |
| orders | fetch_order, fetch_all_orders, fetch_order_payments | create_order, update_order | [orders](docs/api/orders.md) |
| payment_links | fetch_payment_link, fetch_all_payment_links | create_payment_link, payment_link_upi_create, payment_link_notify, update_payment_link | [payment_links](docs/api/payment_links.md) |
| refunds | fetch_refund, fetch_all_refunds, fetch_multiple_refunds_for_payment, fetch_specific_refund_for_payment | create_refund ✗, update_refund | [refunds](docs/api/refunds.md) |
| qr_codes | fetch_qr_code, fetch_all_qr_codes, fetch_qr_codes_by_customer_id, fetch_qr_codes_by_payment_id, fetch_payments_for_qr_code | create_qr_code, close_qr_code ✗ | [qr_codes](docs/api/qr_codes.md) |
| settlements | fetch_settlement_with_id, fetch_all_settlements, fetch_settlement_recon_details, fetch_all_instant_settlements, fetch_instant_settlement_with_id | create_instant_settlement ✗ | [settlements](docs/api/settlements.md) |
| payouts (RazorpayX) | fetch_payout_with_id, fetch_all_payouts | — | [payouts](docs/api/payouts.md) |
| registration_links | — | create_registration_link ✗ | [recurring](docs/api/recurring.md) |
| checkout_integration | detect_stack, integrate_razorpay_checkout | — | [checkout_integration](docs/api/checkout_integration.md) |

✗ = local server only. Every tool → REST endpoint, required args: [REFERENCE.md](REFERENCE.md).

## Task router

| Task | Read |
|---|---|
| Add "Pay with Razorpay" to a web/app backend | [workflows/standard_checkout.md](docs/workflows/standard_checkout.md) |
| Verify checkout / link callback / webhook signature | [common/signatures-and-webhooks.md](docs/common/signatures-and-webhooks.md) |
| Refund one payment or many | [workflows/refunds.md](docs/workflows/refunds.md) |
| "Charged but order unpaid", settlement mismatch | [workflows/reconciliation.md](docs/workflows/reconciliation.md) |
| UPI Autopay / e-mandate / NACH / saved-card charging | [workflows/recurring_mandate.md](docs/workflows/recurring_mandate.md) |
| Collect without a site: link or UPI QR | [api/payment_links.md](docs/api/payment_links.md), [api/qr_codes.md](docs/api/qr_codes.md) |
| Paise, limits, statuses, test cards | [common/conventions.md](docs/common/conventions.md) |
| A call failed / tool missing / 401 | [common/errors.md](docs/common/errors.md) |

## Critical rules

- **Amounts are integer paise** everywhere (₹499.50 → `49950`); convert with `BigDecimal`, never
  `double * 100`. Order/link/refund minimum 100, instant settlement 200.
- **Confirm before money-moving or customer-visible writes**, especially with `rzp_live_` keys:
  `capture_payment`, `create_refund`, `create_instant_settlement`, `initiate_payment`,
  `revoke_token`, `payment_link_notify` (sends SMS/email). Show ids, ₹ amounts and mode; resolve
  "everything"/"all" to an explicit list first.
- **Hidden side effects**: `fetch_tokens` with only `contact` creates a customer;
  `initiate_payment` auto-sends the OTP and, with `contact`, creates a customer.
- **Orders are created server-side** with the price from your DB; the browser sends an id, never an
  amount.
- **Checkout signature** = HMAC-SHA256(`order_id|razorpay_payment_id`, key secret), with `order_id`
  from your DB; constant-time compare. **Webhook** = HMAC of the raw body with the *webhook* secret,
  header `X-Razorpay-Signature`, dedupe on `x-razorpay-event-id`.
- **Webhooks are the source of truth** (`order.paid`); the browser callback can be lost. The MCP
  has no webhook tooling — add a handler.
- **`integrate_razorpay_checkout` output is a draft**: apply the fix list in
  [checkout_integration.md](docs/api/checkout_integration.md) before writing it to the project.
- **Authorized ≠ paid**: uncaptured payments auto-refund after 3 days; enable auto-capture or capture.
- **INR recurring debits** go through `POST /v1/payments/create/recurring` from the backend —
  `initiate_payment` only uses that endpoint for non-INR.
- **Secrets**: never print `key_secret` or the Basic token; build the token with
  `printf '%s:%s'` (not `echo`, which adds a newline).

## Not in the MCP — call REST/SDK directly

Official pages (fetch for params and samples; `B` = `https://razorpay.com/docs/build/llm-docs`):

| Resource | Endpoint | Page |
|---|---|---|
| Customers | `/v1/customers` | `B/api/customers.md` |
| Plans & Subscriptions | `/v1/plans`, `/v1/subscriptions` | `B/payments/subscriptions/apis.md` |
| Invoices | `/v1/invoices` | `B/payments/invoices/apis.md` |
| Route transfers | `/v1/transfers`, `/v1/payments/{id}/transfers` | `B/payments/route/apis.md` (direct: `B/api/payments/route/direct-transfers.md`) |
| Virtual accounts (Smart Collect) | `/v1/virtual_accounts` | `B/payments/smart-collect/va-vpa-qr/api/create.md` |
| Disputes | `/v1/disputes` | `B/api/disputes.md` |
| Cancel payment link | `POST /v1/payment_links/{id}/cancel` | `B/api/payments/payment-links/cancel-standard.md` (UPI: `cancel-upi.md`) |
| Downtimes | `GET /v1/payments/downtimes` | `B/api/payments/downtime.md` |
| Methods | `GET /v1/methods` | `B/payments/payment-gateway/s2s-integration/payment-methods/methods-api.md` |
| Create payouts (RazorpayX) | `/v1/payouts` | `B/api/x.md` |

Base URL `https://api.razorpay.com`, HTTP Basic `key_id:key_secret`.

## Full docs index (everything else on razorpay.com/docs)

[docs/index/README.md](docs/index/README.md) lists every page of llms.txt (title, URL, one line) — find the
page there, then fetch the URL. Start with the family:

| Need | Index |
|---|---|
| REST API reference (customers, disputes, orders, payments, QR, refunds, settlements, partners, X) | [index/api](docs/index/api/README.md) |
| Payment Gateway, Magic Checkout, Subscriptions, Route, Smart Collect, Payment Links/Pages/Button, Invoices, International, Optimizer, payment methods, dashboard | [index/payments](docs/index/payments/README.md) |
| Webhook events and payloads | [index/webhooks](docs/index/webhooks.md) |
| API error codes | [index/errors](docs/index/errors.md) |
| Official MCP server | [index/mcp-server](docs/index/mcp-server.md) |
| RazorpayX: payouts, vendor payments, payout links, current accounts | [index/x](docs/index/x/README.md) |
| Payroll · POS · Partners · Security · n8n node · App Store · Engage · Announcements · FAQs | [payroll](docs/index/payroll.md), [pos](docs/index/pos.md), [partners](docs/index/partners.md), [security](docs/index/security.md), [razorpay-n8n-node](docs/index/razorpay-n8n-node.md), [app-store](docs/index/app-store.md), [engage](docs/index/engage.md), [announcements](docs/index/announcements.md), [faqs](docs/index/faqs.md) |

## Guardrail for Claude Code users

Suggest (don't apply unasked) `permissions.ask` entries in `.claude/settings.json` for write tools,
e.g. `"mcp__razorpay__capture_payment"`, `"mcp__razorpay__create_refund"`,
`"mcp__razorpay__initiate_payment"`, `"mcp__razorpay__revoke_token"` — or run the local server with
`READ_ONLY=true` for analysis-only sessions.
