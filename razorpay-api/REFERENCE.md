# Razorpay MCP — Tool ↔ REST Reference

All 45 tools registered by the official server (`github.com/razorpay/razorpay-mcp-server`,
`pkg/razorpay/tools.go`). Base URL for every REST path: `https://api.razorpay.com` (test and live
share it; the key decides the mode). Auth: HTTP Basic `key_id:key_secret`.

**R/W** = how the server registers the tool. `READ_ONLY=true` (or remote OAuth, whose only scope is
`read_only`) hides every **W** tool. **Remote** = available on hosted `https://mcp.razorpay.com/mcp`.

## Tool map

| Tool (name registered in code) | Toolset | R/W | Remote | REST call | Required args |
|---|---|---|---|---|---|
| `fetch_payment` | payments | R | ✅ | `GET /v1/payments/{id}` | `payment_id` |
| `fetch_payment_card_details` | payments | R | ✅ | `GET /v1/payments/{id}/card` | `payment_id` |
| `fetch_all_payments` | payments | R | ✅ | `GET /v1/payments` | — |
| `capture_payment` | payments | W | ✅ | `POST /v1/payments/{id}/capture` | `payment_id`, `amount`, `currency` |
| `update_payment` | payments | W | ✅ | `PATCH /v1/payments/{id}` (notes only) | `payment_id`, `notes` |
| `initiate_payment` | payments | W | ✅ | `POST /v1/payments/create/json` ¹ | `amount`, `order_id` |
| `resend_otp` | payments | W | ✅ | `POST /v1/payments/{id}/otp/resend` | `payment_id` |
| `submit_otp` | payments | W | ✅ | `POST /v1/payments/{id}/otp/submit` | `payment_id`, `otp_string` |
| `fetch_tokens` | payments | W ² | ✅ | `GET /v1/customers/{id}/tokens` ³ | `customer_id` **or** `contact` |
| `revoke_token` | payments | W | ✅ | `PUT /v1/customers/{c}/tokens/{t}/cancel` | `customer_id`, `token_id` |
| `create_order` | orders | W | ✅ | `POST /v1/orders` | `amount`, `currency` |
| `fetch_order` | orders | R | ✅ | `GET /v1/orders/{id}` | `order_id` |
| `fetch_all_orders` | orders | R | ✅ | `GET /v1/orders` | — |
| `fetch_order_payments` | orders | R | ✅ | `GET /v1/orders/{id}/payments` | `order_id` |
| `update_order` | orders | W | ✅ | `PATCH /v1/orders/{id}` (notes only) | `order_id`, `notes` |
| `create_payment_link` | payment_links | W | ✅ | `POST /v1/payment_links` | `amount`, `currency` |
| `payment_link_upi_create` | payment_links | W | ✅ | `POST /v1/payment_links` (+`upi_link:true`) | `amount`, `currency` (INR) |
| `fetch_payment_link` | payment_links | R | ✅ | `GET /v1/payment_links/{id}` | `payment_link_id` |
| `fetch_all_payment_links` | payment_links | R | ✅ | `GET /v1/payment_links` | — |
| `payment_link_notify` | payment_links | W | ✅ | `POST /v1/payment_links/{id}/notify_by/{medium}` | `payment_link_id`, `medium` (sms/email) |
| `update_payment_link` | payment_links | W | ✅ | `PATCH /v1/payment_links/{id}` | `payment_link_id` |
| `create_refund` | refunds | W | ❌ | `POST /v1/payments/{id}/refund` | `payment_id`, `amount` |
| `fetch_refund` | refunds | R | ✅ | `GET /v1/refunds/{id}` | `refund_id` |
| `fetch_all_refunds` | refunds | R | ✅ | `GET /v1/refunds` | — |
| `update_refund` | refunds | W | ✅ | `PATCH /v1/refunds/{id}` (notes only) | `refund_id`, `notes` |
| `fetch_multiple_refunds_for_payment` | refunds | R | ✅ | `GET /v1/payments/{id}/refunds` | `payment_id` |
| `fetch_specific_refund_for_payment` | refunds | R | ✅ | `GET /v1/payments/{id}/refunds/{rfnd}` | `payment_id`, `refund_id` |
| `create_qr_code` | qr_codes | W | ✅ | `POST /v1/payments/qr_codes` | `type` (=`upi_qr`), `usage` |
| `fetch_qr_code` | qr_codes | R | ✅ | `GET /v1/payments/qr_codes/{id}` | `qr_code_id` |
| `fetch_all_qr_codes` | qr_codes | R | ✅ | `GET /v1/payments/qr_codes` | — |
| `fetch_qr_codes_by_customer_id` | qr_codes | R | ✅ | `GET /v1/payments/qr_codes?customer_id=` | `customer_id` |
| `fetch_qr_codes_by_payment_id` | qr_codes | R | ✅ | `GET /v1/payments/qr_codes?payment_id=` | `payment_id` |
| `fetch_payments_for_qr_code` | qr_codes | R | ✅ | `GET /v1/payments/qr_codes/{id}/payments` | `qr_code_id` |
| `close_qr_code` | qr_codes | W | ❌ | `POST /v1/payments/qr_codes/{id}/close` | `qr_code_id` |
| `fetch_settlement_with_id` | settlements | R | ✅ | `GET /v1/settlements/{id}` | `settlement_id` |
| `fetch_all_settlements` | settlements | R | ✅ | `GET /v1/settlements` | — |
| `fetch_settlement_recon_details` | settlements | R | ✅ | `GET /v1/settlements/recon/combined` | `year`, `month` |
| `create_instant_settlement` | settlements | W | ❌ | `POST /v1/settlements/ondemand` | `amount` |
| `fetch_all_instant_settlements` | settlements | R | ✅ | `GET /v1/settlements/ondemand` | — |
| `fetch_instant_settlement_with_id` | settlements | R | ✅ | `GET /v1/settlements/ondemand/{id}` | `settlement_id` |
| `fetch_payout_with_id` | payouts | R | ✅ | `GET /v1/payouts/{id}` (RazorpayX) | `payout_id` |
| `fetch_all_payouts` | payouts | R | ✅ | `GET /v1/payouts?account_number=` (RazorpayX) | `account_number` |
| `create_registration_link` | registration_links | W | ❌ | `POST /v1/subscription_registration/auth_links` | `type`, `amount`, `currency`, `description`, `subscription_registration` |
| `detect_stack` | checkout_integration | R | ✅ | none — inspects the file list you pass | `files` |
| `integrate_razorpay_checkout` | checkout_integration | R | ✅ | none — returns code templates | `language`, `backendFramework`, `frontendFramework` |

¹ Switches to `POST /v1/payments/create/recurring` only when `recurring=true` **and** `token` is set
**and** currency ≠ INR. If the response has an OTP `next` action, the tool **immediately calls the OTP
URL itself** (sends the SMS). If `contact` is passed, it first runs `POST /v1/customers` with
`fail_existing:"0"` (creates the customer if absent).
² Registered as a write tool, so `READ_ONLY` hides it even though it mostly reads.
³ With only `contact`: `POST /v1/customers` (`fail_existing:"0"`) first — **creates a customer record**
as a side effect — then fetches tokens.

## Name drift: README / official docs vs code

The README and `razorpay.com/docs/.../mcp-server/tools-reference` list three tools under different
names from what `tools.go` registers. The name the client actually lists (`tools/list`) wins; the
code names are:

| Docs say | Code registers |
|---|---|
| `create_payment_link_upi` | `payment_link_upi_create` |
| `send_payment_link` | `payment_link_notify` |
| `fetch_payout_by_id` | `fetch_payout_with_id` |

In Claude Code the tools appear as `mcp__<server-name>__<tool>`, e.g. `mcp__razorpay__create_order`.

## ID prefixes

`pay_` payment · `order_` order · `plink_` payment link · `rfnd_` refund · `qr_` QR code ·
`setl_` settlement · `setlod_` instant settlement · `pout_` payout · `cust_` customer ·
`token_` saved method · `rzp_test_` / `rzp_live_` key IDs.

## Official docs (raw markdown, fetchable)

- Index for LLMs: `https://razorpay.com/docs/llms.txt`
- Any API page `https://razorpay.com/docs/api/<path>` has a raw markdown twin at
  `https://razorpay.com/docs/build/llm-docs/api/<path>.md`
  (e.g. `.../llm-docs/api/payments/capture.md`, `.../llm-docs/api/refunds/create-instant.md`).
- Errors: `https://razorpay.com/docs/build/llm-docs/errors.md`
- Webhooks: `https://razorpay.com/docs/build/llm-docs/webhooks.md`,
  `.../llm-docs/webhooks/validate-test.md`
- MCP server: `https://razorpay.com/docs/build/llm-docs/mcp-server.md` (+ `/remote.md`, `/local.md`,
  `/oauth.md`, `/configuration.md`, `/tools-reference.md`)
