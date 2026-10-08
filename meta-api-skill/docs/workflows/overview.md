# WhatsApp Cloud API — Overview, Terminology and Integration Order

> **Scope**: Orientation. Load this when the user needs to know what the Meta WhatsApp APIs are, how the pieces relate, and in which order to integrate them.

---

## 1. What Meta exposes

Everything is the **Graph API**: REST-style HTTPS calls with JSON bodies against `https://graph.facebook.com/{version}/…`, authenticated with a Bearer token. "WhatsApp Cloud API" (sending and receiving messages, media) and "WhatsApp Business Management API" (templates, phone numbers, WABA settings, analytics) are two permission families on the same host. Inbound events arrive by **webhooks** (HTTPS POST from Meta to your server). There is no SDK for Java; a typed HTTP client (OpenFeign, RestClient) is the normal integration.

Meta's separate "REST API" framework (OpenAPI-based, announced 2025 for new products such as the Llama API) does **not** carry WhatsApp. WhatsApp stays on Graph.

The self-hosted **On-Premises API** reached end of life in October 2025 (unverified exact date 2026-10-04). Cloud API is the only option.

---

## 2. Terminology

| Term | Meaning |
|---|---|
| **Meta Business Portfolio** (formerly Business Manager) | The company account that owns apps, WABAs and system users. `<BUSINESS_ID>`. |
| **App** | A Meta developer app with the WhatsApp product added. Owns the App ID, App Secret (webhook HMAC key) and the webhook subscription. |
| **WABA** | WhatsApp Business Account. Owns phone numbers, templates, billing currency. `<WABA_ID>`. |
| **Phone number id** | The Graph id of a registered business number (not the number itself). Every send and media call is scoped to it. `<PHONE_NUMBER_ID>`. |
| **System User** | A non-human user in the business portfolio; its token is the long-lived credential for servers. |
| **Access token** | Bearer token; System User tokens do not expire unless revoked, App Dashboard tokens last 24 h. |
| **Template (HSM)** | A pre-approved message with placeholders. Required outside the 24 h customer-service window and for all marketing. |
| **Customer-service window** | 24 h after a customer's last inbound message, during which free-form messages are allowed. |
| **wamid** | The WhatsApp message id returned on send and echoed in status webhooks. It encodes the recipient number: treat as PII. |
| **wa_id** | The customer's WhatsApp id (their number in E.164 digits). |
| **Quality rating / messaging tier** | Per-number health and the cap on unique recipients per 24 h (250 unverified, then 1k/10k/100k/unlimited). |
| **Per-message pricing** | Billing model since 2025: marketing, utility, authentication priced per delivered message; service messages free (verify on the pricing page). |

---

## 3. Lifecycle of one outbound template message

```
1. Template exists and is APPROVED (templates/list_templates.md)
2. Media header? Upload once → media id (media/upload.md); ids live 30 days
3. POST /{PHONE_NUMBER_ID}/messages with type=template (messaging/send_template.md)
   → 200 {messages:[{id: wamid}]}  = accepted, not delivered
   → 4xx {error:{code}}            = synchronous failure (common/errors.md)
4. Webhook statuses[]: sent → delivered → read   (webhooks/statuses.md)
   or failed with errors[].code                   (asynchronous failure)
5. Customer replies → webhook messages[] → opens the 24 h window (webhooks/inbound_messages.md)
```

---

## 4. Integration order

| Step | Name | Where | Notes |
|---|---|---|---|
| 1 | Business verification, WABA, phone number | Meta Business Suite (HITL) | Coexistence with the WhatsApp Business app is allowed on the same number |
| 2 | App + System User token | `account/access_tokens.md` | Permissions `whatsapp_business_messaging`, `whatsapp_business_management` |
| 3 | Register the number, two-step PIN | `account/phone_numbers.md` | Required before the first send |
| 4 | Business profile | `account/business_profile.md` | Optional, improves trust |
| 5 | Webhook endpoint + subscription | `webhooks/setup_verification.md`, `signature_validation.md` | Subscribe the app to the WABA or nothing arrives |
| 6 | Templates | `templates/create_template.md`, `components.md` | Approval takes minutes to a day |
| 7 | Media upload | `media/upload.md` | Cache the id per asset, re-upload before 30 days |
| 8 | Send | `messaging/send_template.md` and the other send docs | Honour the 24 h window and marketing limits |
| 9 | Receipts and inbound | `webhooks/statuses.md`, `inbound_messages.md` | Idempotent consumer |
| 10 | Errors, rate limits, logging | `common/errors.md`, `rate_limits.md`, `logging_privacy.md` | Bucket codes; never log numbers |
| 11 | Billing | `billing/pricing.md`, `analytics.md` | India: INR by 2026-12-31 |

---

## 5. Permission families

| Family | Permission | Typical calls |
|---|---|---|
| Messaging | `whatsapp_business_messaging` | `/messages`, `/media`, mark read |
| Management | `whatsapp_business_management` | `/message_templates`, `/phone_numbers`, WABA fields, analytics, `subscribed_apps` |
| Business | `business_management` | listing WABAs under a business (`/owned_whatsapp_business_accounts`) |

---

## 6. Where each dimension lives in this skill

| Folder | Business dimension |
|---|---|
| `docs/messaging/` | Sending: templates, text, media, interactive, read receipts and typing, messaging rules |
| `docs/media/` | Uploading, fetching and deleting media; resumable uploads for template samples |
| `docs/templates/` | Template CRUD, components, approval lifecycle, quality, marketing limits |
| `docs/account/` | WABA, phone numbers, registration, business profile, tokens, messaging tiers |
| `docs/webhooks/` | Setup, signature, envelope, inbound message types, statuses, template and account events |
| `docs/billing/` | Pricing model and INR migration, analytics endpoints |
| `docs/common/` | Auth, versioning, the full error table, rate limits, logging and privacy, config, checklist |
| `docs/workflows/` | This overview, onboarding, marketing campaign, inbound chat and opt-out |
