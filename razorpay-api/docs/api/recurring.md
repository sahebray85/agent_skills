# Recurring: registration links

> **When to load**: sending a customer an authorisation link for a mandate (card, e-mandate, NACH,
> UPI). For the full recurring picture (mandate orders, tokens, subsequent debits) read
> [recurring_mandate.md](../workflows/recurring_mandate.md).

## Usage notes

- `create_registration_link` is **local-server only**. It calls
  `POST /v1/subscription_registration/auth_links` with `type: "link"`.
- `subscription_registration` must include `method` (`card` | `emandate` | `nach` | `upi`); optional
  `max_amount` (paise), `expire_at` (Unix s), `frequency`
  (`as_presented|monthly|weekly|yearly|daily`).
- `amount` here is the authorisation-transaction amount (paise); customer fields are flat args mapped
  into `customer{}`; `email_notify` / `sms_notify` send the link.
- After the customer authorises, their token appears in `fetch_tokens` (payments toolset).

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `create_registration_link`

**Write** · remote ❌ · `POST /v1/subscription_registration/auth_links`

> Create a registration link (auth link) for subscription registration in Razorpay to set up recurring payments via card, emandate, NACH, or UPI.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `type` | string | REQUIRED | Type of registration link. Use 'link'. |
| `amount` | number | REQUIRED | Amount in the smallest currency unit (e.g., paise for INR). |
| `currency` | string | REQUIRED | Three-letter ISO currency code (e.g., INR, MYR). |
| `description` | string | REQUIRED | Brief description of the registration link. |
| `subscription_registration` | object | REQUIRED | Subscription registration details. Must include 'method' (card, emandate, nach, upi). May include 'max_amount', 'expire_at' (Unix timestamp), and 'frequency' (as_presented, monthly, weekly, yearly, daily). |
| `customer_name` | string | — | Name of the customer. |
| `customer_email` | string | — | Email address of the customer. |
| `customer_contact` | string | — | Contact number of the customer. |
| `receipt` | string | — | Unique receipt identifier provided by the merchant. |
| `email_notify` | boolean | — | Send email notification. Default: true |
| `sms_notify` | boolean | — | Send SMS notification. Default: true |
| `expire_by` | number | — | Unix timestamp when the registration link expires. |
| `notes` | object | — | Key-value pairs for additional info. Max 15 pairs, each up to 256 characters. |
