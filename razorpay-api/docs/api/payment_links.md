# Payment Links toolset

> **When to load**: collecting money without a checkout page (send a link by SMS/email), UPI-only
> links, reminders, link expiry, partial payments, or a link's callback.

## Usage notes

- Standard link: `create_payment_link`. UPI-only link: `payment_link_upi_create` (docs call it
  `create_payment_link_upi`), which sets `upi_link`.
- **UPI links** (`upi_link: true`) are INR only, work **only on Android devices** and **only in
  Live mode** (a test key gets "UPI Payment Links is not supported in Test Mode. Please experience
  the product in Live Mode."), and take **no partial payments** ("partial payment not supported in
  upi link"), so they never reach `partially_paid`.
- **The MCP schema is not the REST body.** The tools take flat args (`customer_name`,
  `customer_email`, `customer_contact`, `notify_sms`, `notify_email`); `POST /v1/payment_links`
  takes nested `customer {name, email, contact}` and `notify {sms, email}`. `upi_link` is a JSON
  boolean in the parameter table and in webhook payloads, but the official curl and entity samples
  show the string `"true"`: accept both when reading.
- `notify_sms` / `notify_email` make Razorpay send the link; `reminder_enable` for reminders. The
  customer's contact and email are not prefilled at checkout; the payer types them again.
- `expire_by`: Unix seconds, **at least 15 minutes ahead** ("timestamp must be atleast 15 minutes
  in future") and **at most 6 months** after creation. Omitted = valid for 6 months.
- `reference_id`: **at most 40 characters** ("reference_id: the length must be no more than 40.")
  and **unique per link**. A reused value is rejected with "payment link creation with reference ID
  already attempted"; find the earlier link with `fetch_all_payment_links(reference_id)`.
- Instalments: `accept_partial: true` + `first_min_partial_amount`, which must be `<= amount`
  ("first_min_partial_amount must be less than or equal to amount.") and at least 100 for INR.
  The official error list says it is also rejected when `accept_partial` is `false`.
- Payment methods shown on the link page (REST only, no MCP arg):
  `options.checkout.method {netbanking, card, upi, wallet}`, one boolean each, default `true`;
  `false` hides that method.
- `callback_url` needs `callback_method: "get"`. Verify the callback's `razorpay_signature` —
  formula in [signatures-and-webhooks.md](../common/signatures-and-webhooks.md).
- `payment_link_notify` (docs: `send_payment_link`) — `medium` `sms` | `email`; sends a real message
  in live mode; fails for paid/expired/cancelled links.
- `status`: `created`, `partially_paid`, `paid`, `cancelled`, `expired`. The official states page
  calls the first state `issued` in its prose; the API value is `created`. A link can be cancelled
  only before any payment, not in `partially_paid` or `paid`.
- Track payment via webhook `payment_link.paid` (also `partially_paid`, `expired`, `cancelled`) or
  `fetch_payment_link`, whose `payments[]` lists captured payments only (`payment_id`, `amount`,
  `method`, `status`) and is `null` or empty until the first one.
- Razorpay creates an order behind the link. Webhook payloads expose it as
  `payment_link.entity.order_id` (`order_…`), equal to `payment.entity.order_id`; the REST entity
  page does not list the field. Payload shapes and traps:
  [signatures-and-webhooks.md](../common/signatures-and-webhooks.md).
- Test mode allows at most 30 links per business.
- Dynamic Convenience Fees are an Orders API feature; the Payment Links API pages document no
  `convenience_fee_config` field ([orders.md](orders.md)).
- Not in MCP: cancel a link — `POST /v1/payment_links/{id}/cancel`.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `create_payment_link`

**Write** · remote ✅ · `POST /v1/payment_links`

> Create a new standard payment link in Razorpay with a specified amount

| Param | Type | Constraints | Description |
|---|---|---|---|
| `amount` | number | REQUIRED; Min=100 | Amount to be paid using the link in paise (smallest currency unit). For INR: 100 paise = ₹1. Example: for ₹300, use 30000 |
| `currency` | string | REQUIRED | Three-letter ISO code for the currency (e.g., INR) |
| `description` | string | — | A brief description of the Payment Link explaining the intent of the payment. |
| `accept_partial` | boolean | — | Indicates whether customers can make partial payments using the Payment Link. Default: false |
| `first_min_partial_amount` | number | — | Minimum amount in paise that must be paid by the customer as the first partial payment. For INR: 100 paise = ₹1. Default value is 100. |
| `expire_by` | number | — | Timestamp, in Unix, when the Payment Link will expire. By default, a Payment Link will be valid for six months. |
| `reference_id` | string | — | Reference number tagged to a Payment Link. Must be unique for each Payment Link. Max 40 characters. |
| `customer_name` | string | — | Name of the customer. |
| `customer_email` | string | — | Email address of the customer. |
| `customer_contact` | string | — | Contact number of the customer. |
| `notify_sms` | boolean | — | Send SMS notifications for the Payment Link. |
| `notify_email` | boolean | — | Send email notifications for the Payment Link. |
| `reminder_enable` | boolean | — | Enable payment reminders for the Payment Link. |
| `notes` | object | — | Key-value pairs that can be used to store additional information. Maximum 15 pairs, each value limited to 256 characters. |
| `callback_url` | string | — | If specified, adds a redirect URL to the Payment Link. Customer will be redirected here after payment. |
| `callback_method` | string | — | HTTP method for callback redirection. Must be 'get' if callback_url is set. |

## `payment_link_upi_create`

**Write** · remote ✅ · `POST /v1/payment_links` (+`upi_link:true`)

> Create a new UPI payment link in Razorpay with a specified amount and additional options.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `amount` | number | REQUIRED; Min=100 | Amount to be paid using the link in paise (smallest currency unit). For INR: 100 paise = ₹1. Example: for ₹300, use 30000. Only accepted currency is INR |
| `currency` | string | REQUIRED | Three-letter ISO code for the currency (e.g., INR). UPI links are only supported in INR |
| `description` | string | — | A brief description of the Payment Link explaining the intent of the payment. |
| `accept_partial` | boolean | — | Indicates whether customers can make partial payments using the Payment Link. Default: false |
| `first_min_partial_amount` | number | — | Minimum amount in paise that must be paid by the customer as the first partial payment. For INR: 100 paise = ₹1. Default value is 100. |
| `expire_by` | number | — | Timestamp, in Unix, when the Payment Link will expire. By default, a Payment Link will be valid for six months. |
| `reference_id` | string | — | Reference number tagged to a Payment Link. Must be unique for each Payment Link. Max 40 characters. |
| `customer_name` | string | — | Name of the customer. |
| `customer_email` | string | — | Email address of the customer. |
| `customer_contact` | string | — | Contact number of the customer. |
| `notify_sms` | boolean | — | Send SMS notifications for the Payment Link. |
| `notify_email` | boolean | — | Send email notifications for the Payment Link. |
| `reminder_enable` | boolean | — | Enable payment reminders for the Payment Link. |
| `notes` | object | — | Key-value pairs that can be used to store additional information. Maximum 15 pairs, each value limited to 256 characters. |
| `callback_url` | string | — | If specified, adds a redirect URL to the Payment Link. Customer will be redirected here after payment. |
| `callback_method` | string | — | HTTP method for callback redirection. Must be 'get' if callback_url is set. |

## `fetch_payment_link`

**Read** · remote ✅ · `GET /v1/payment_links/{id}`

> Fetch payment link details using it's ID. Response contains the basic details like amount, status etc. The link could be of any type(standard or UPI)

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_link_id` | string | REQUIRED | ID of the payment link to be fetched(ID should have a plink_ prefix). |

## `payment_link_notify`

**Write** · remote ✅ · `POST /v1/payment_links/{id}/notify_by/{medium}`

> Send or resend notification for a payment link via SMS or email.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_link_id` | string | REQUIRED | ID of the payment link for which to send notification (ID should have a plink_ prefix). |
| `medium` | string | REQUIRED; Enum="sms", "email" | Medium through which to send the notification. Must be either 'sms' or 'email'. |

## `update_payment_link`

**Write** · remote ✅ · `PATCH /v1/payment_links/{id}`

> Update any existing standard or UPI payment link with new details such as reference ID, expiry date, or notes.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_link_id` | string | REQUIRED | ID of the payment link to update (ID should have a plink_ prefix). |
| `reference_id` | string | — | Adds a unique reference number to the payment link. |
| `expire_by` | number | — | Timestamp, in Unix format, when the payment link should expire. |
| `reminder_enable` | boolean | — | Enable or disable reminders for the payment link. |
| `accept_partial` | boolean | — | Allow customers to make partial payments. Not allowed with UPI payment links. |
| `notes` | object | — | Key-value pairs for additional information. Maximum 15 pairs, each value limited to 256 characters. |

## `fetch_all_payment_links`

**Read** · remote ✅ · `GET /v1/payment_links`

> Fetch all payment links with optional filtering by payment ID or reference ID.You can specify the upi_link parameter to filter by link type.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | string | — | Optional: Filter by payment ID associated with payment links |
| `reference_id` | string | — | Optional: Filter by reference ID used when creating payment links |
| `upi_link` | number | — | Optional: Filter only upi links. Value should be 1 if you want only upi links, 0 for only standard linksIf not provided, all types of links will be returned |
