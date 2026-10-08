---
name: meta-api-skill
description: Implement, integrate and debug the Meta WhatsApp Cloud API and WhatsApp Business Management API (Graph API v26.0) across every business dimension - sending template, text, media and interactive messages; media upload and download; template CRUD, components and approval lifecycle; WABA, phone number, registration, business profile and access tokens; webhooks for inbound messages, delivery statuses and template or account events; pricing, INR billing and analytics; the full error-code table with retry buckets. Use when the user mentions Meta, WhatsApp, Cloud API, Graph API, WABA, phone number id, wamid, message templates, HSM, webhooks, X-Hub-Signature-256, delivery receipts, opt-out or STOP handling, media ids, per-user marketing limits, error codes such as 131049 or 131026, or asks why a WhatsApp send or webhook fails.
---

# Meta WhatsApp API Skill

## Source of truth hierarchy

> Meta's developer documentation is public and is the **authoritative source**. The local `docs/` directory
> is a pre-fetched, dated cache. Read it directly with the `Read` tool by default; go to the live page when a
> fact is marked "(unverified <date>)", when the question is about something newer than the cache date, or
> when behaviour in production contradicts the cache.
>
> 1. **Live Meta docs** - `https://developers.facebook.com/documentation/business-messaging/whatsapp/` (new home)
>    and `https://developers.facebook.com/docs/whatsapp/cloud-api/` (older pages still live). See [SOURCES.md](SOURCES.md).
> 2. **Local `docs/`** (this skill) - one file per API or concept, organised by business dimension.
> 3. **WebFetch / WebSearch** - for pages the cache does not cover. Many old URLs 404 since the 2026 move;
>    try the new path first.
>
> Facts in `docs/` carry a "Sources (verified YYYY-MM-DD)" section. A fact marked unverified was not confirmed
> on the live page that day; verify before relying on it in code.

## Business dimensions and their APIs

| Folder | Dimension | Files |
|---|---|---|
| `docs/messaging/` | **Sending** | `send_template.md`, `send_text.md`, `send_media.md`, `send_interactive.md`, `mark_read_typing.md`, `messaging_rules.md` |
| `docs/media/` | **Media** | `upload.md`, `retrieve_url.md`, `download.md`, `delete.md`, `resumable_upload.md` |
| `docs/templates/` | **Templates** | `list_templates.md`, `create_template.md`, `edit_delete_template.md`, `components.md`, `lifecycle_quality.md`, `marketing_limits.md` |
| `docs/account/` | **Account and numbers** | `waba.md`, `phone_numbers.md`, `business_profile.md`, `access_tokens.md`, `messaging_limits_tiers.md` |
| `docs/webhooks/` | **Inbound events** | `setup_verification.md`, `signature_validation.md`, `payload_envelope.md`, `inbound_messages.md`, `statuses.md`, `template_and_account_webhooks.md` |
| `docs/billing/` | **Money** | `pricing.md`, `analytics.md` |
| `docs/common/` | **Cross-cutting** | `auth.md`, `versioning.md`, `errors.md` (full code table + buckets), `rate_limits.md`, `logging_privacy.md`, `config.md`, `checklist.md` |
| `docs/workflows/` | **End to end** | `overview.md`, `onboarding.md`, `marketing_campaign.md`, `inbound_chat_and_optout.md` |

All endpoint paths in one table: [REFERENCE.md](REFERENCE.md).

## Workflow: implementing an API call

```
1. Read docs/workflows/overview.md once if the user is new to the Meta model (WABA, phone number id, templates, window)
2. Read the one file for the call: docs/<dimension>/<api>.md      <- request, response, errors, quirks
3. Read docs/common/auth.md and docs/common/versioning.md         <- Bearer token, pinned version
4. Read docs/common/errors.md                                     <- bucket the codes you will handle
5. Read docs/common/logging_privacy.md                            <- never log numbers, wamids, bodies, tokens
6. Implement against docs/common/checklist.md
```

## Workflow: debugging a failure

```
1. Synchronous failure (4xx on the call): take error.code, error_subcode, fbtrace_id -> docs/common/errors.md
2. Asynchronous failure (webhook statuses[].status = failed): errors[0].code -> same table; see docs/webhooks/statuses.md
3. Nothing arrives at the webhook: docs/webhooks/setup_verification.md (subscribed_apps, GET handshake, TLS)
4. Signature mismatch: docs/webhooks/signature_validation.md (raw body, sha256= prefix, App Secret)
5. Template problems (132xxx): docs/templates/lifecycle_quality.md
6. Limits (130429, 131048, 131049, 131056, 80007): docs/common/rate_limits.md and docs/templates/marketing_limits.md
```

## Workflow: planning an integration

```
1. docs/workflows/onboarding.md            <- HITL steps and the API calls, in order
2. docs/workflows/marketing_campaign.md    <- bulk template sends, media header, receipts, buckets
3. docs/workflows/inbound_chat_and_optout.md <- webhook consumer, 24 h window, STOP handling
```

## Critical rules (always apply)

- **Everything is Graph**: `https://graph.facebook.com/{version}/...`, `Authorization: Bearer <System User token>`. Pin the version in config (`v26.0` today); never omit it.
- **200 on send means accepted, not delivered.** Delivery, read and failure arrive later on the `statuses` webhook keyed by the returned wamid.
- **Templates outside the 24 h window.** Free-form text, media and interactive messages only after the customer wrote to you within 24 h; otherwise an APPROVED template, or you get 131047.
- **Bucket error codes, do not blanket-retry.** AUTH/ACCOUNT/TEMPLATE/QUOTA are systemic (stop the channel); 131049 defer 24 h; 131056 defer 1 h; 131026 and friends fail that recipient only; transport and 5xx retry with backoff.
- **Webhooks**: verify `X-Hub-Signature-256` over the raw bytes, answer 200 fast, subscribe the app to the WABA, expect duplicates and out-of-order delivery, be idempotent on message id and `(wamid, status)`.
- **Media ids expire after 30 days** (7 days for ids received in webhooks); download URLs live 5 minutes; cache ids per asset and re-upload before expiry.
- **Never log** phone numbers, `wa_id`, wamids (they encode the number), message bodies, media URLs or tokens. Log `code`, `error_subcode`, `fbtrace_id`, HTTP status and counts.
- **Marketing**: per-user marketing limits apply, US (+1) marketing templates have been paused since 2025-04-01, and Indian WABAs must bill in INR by 2026-12-31.
- **Messaging tiers**: 250 unique recipients per 24 h before business verification, then 2,000 / 10,000 / 100,000 / unlimited as quality and volume grow. Mirror the tier in a daily cap.
- **Secrets from env** (`WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`); never in code or an image.

## Environments

| Env | Base URL | Notes |
|---|---|---|
| All | `https://graph.facebook.com/v26.0` | No separate sandbox host. Use the Meta **test number** from App Dashboard > WhatsApp > API Setup and a temporary 24 h token for experiments; a System User token for servers. |

See [REFERENCE.md](REFERENCE.md) for every endpoint path, auth per family, timeout defaults, retry strategy and the config catalogue.
