# Meta WhatsApp API — Reference

## Official documentation

| Source | URL | Notes |
|---|---|---|
| **WhatsApp Business Platform docs (new home)** | `https://developers.facebook.com/documentation/business-messaging/whatsapp/` | Authoritative. Templates, webhooks, pricing, reference pages moved here in 2026 |
| Cloud API reference (older pages, still live) | `https://developers.facebook.com/docs/whatsapp/cloud-api/` | Messages, media, error codes, phone numbers, business profiles |
| Business Management API | `https://developers.facebook.com/docs/whatsapp/business-management-api/` | WABA, analytics, templates (older pages) |
| Graph API core | `https://developers.facebook.com/docs/graph-api/` | Versioning, changelog, webhooks mechanics, rate limiting, debug_token |

Per-page URLs with their verification status: [SOURCES.md](SOURCES.md). Every file in `docs/` ends with a dated Sources section.

---

## All endpoint paths

Base: `https://graph.facebook.com/{version}` with `{version}` = `v26.0`. Auth on every call: `Authorization: Bearer <TOKEN>` unless noted.

| Dimension | Operation | Method | Path | Doc |
|---|---|---|---|---|
| Messaging | Send any message (template, text, media, interactive, location, contacts, reaction, sticker) | POST | `/{PHONE_NUMBER_ID}/messages` | `docs/messaging/send_*.md` |
| Messaging | Mark as read, typing indicator | POST | `/{PHONE_NUMBER_ID}/messages` with `status: "read"` | `docs/messaging/mark_read_typing.md` |
| Media | Upload | POST (multipart) | `/{PHONE_NUMBER_ID}/media` | `docs/media/upload.md` |
| Media | Get URL and metadata | GET | `/{MEDIA_ID}?phone_number_id=` | `docs/media/retrieve_url.md` |
| Media | Download | GET | `<url from previous call>` (Bearer token required; URL valid 5 min) | `docs/media/download.md` |
| Media | Delete | DELETE | `/{MEDIA_ID}?phone_number_id=` | `docs/media/delete.md` |
| Media | Resumable upload (template header samples) | POST | `/{APP_ID}/uploads` then `/upload:<ID>` (header `Authorization: OAuth <TOKEN>`) | `docs/media/resumable_upload.md` |
| Templates | List (cursor paged) | GET | `/{WABA_ID}/message_templates?fields=&limit=&after=` | `docs/templates/list_templates.md` |
| Templates | Create | POST | `/{WABA_ID}/message_templates` | `docs/templates/create_template.md` |
| Templates | Edit | POST | `/{TEMPLATE_ID}` | `docs/templates/edit_delete_template.md` |
| Templates | Delete (by name, all languages; or by id) | DELETE | `/{WABA_ID}/message_templates?name=` (+ `&hsm_id=`) | `docs/templates/edit_delete_template.md` |
| Account | WABA fields | GET | `/{WABA_ID}?fields=` | `docs/account/waba.md` |
| Account | WABAs owned by a business | GET | `/{BUSINESS_ID}/owned_whatsapp_business_accounts` | `docs/account/waba.md` |
| Account | Subscribe app to WABA webhooks (required) | POST / GET / DELETE | `/{WABA_ID}/subscribed_apps` | `docs/account/waba.md` |
| Account | Phone numbers of a WABA | GET | `/{WABA_ID}/phone_numbers?fields=` | `docs/account/phone_numbers.md` |
| Account | One phone number | GET | `/{PHONE_NUMBER_ID}?fields=` | `docs/account/phone_numbers.md` |
| Account | Request / verify OTP for a number | POST | `/{PHONE_NUMBER_ID}/request_code`, `/verify_code` | `docs/account/phone_numbers.md` |
| Account | Register / deregister, two-step PIN | POST | `/{PHONE_NUMBER_ID}/register`, `/deregister`, `/{PHONE_NUMBER_ID}` (pin) | `docs/account/phone_numbers.md` |
| Account | Business profile | GET / POST | `/{PHONE_NUMBER_ID}/whatsapp_business_profile` | `docs/account/business_profile.md` |
| Account | Inspect a token | GET | `/debug_token?input_token=` | `docs/common/auth.md` |
| Billing | Analytics (messages, conversations, pricing, templates) | GET | `/{WABA_ID}?fields=analytics.start().end().granularity()` and siblings | `docs/billing/analytics.md` |
| Webhooks | Verification handshake (Meta → you) | GET | `<your callback>?hub.mode=subscribe&hub.verify_token=&hub.challenge=` | `docs/webhooks/setup_verification.md` |
| Webhooks | Event delivery (Meta → you) | POST | `<your callback>` with `X-Hub-Signature-256` | `docs/webhooks/*.md` |

---

## Authentication summary

| Family | Permission on the token | Credential | Doc |
|---|---|---|---|
| Messaging and media | `whatsapp_business_messaging` | System User token (permanent) | `docs/common/auth.md` |
| Templates, numbers, WABA, analytics | `whatsapp_business_management` | same token | `docs/account/access_tokens.md` |
| Listing WABAs under a business | `business_management` | same token | `docs/account/waba.md` |
| Webhook signature | none (HMAC) | **App Secret** | `docs/webhooks/signature_validation.md` |
| Resumable upload session | `whatsapp_business_management` | header `Authorization: OAuth <TOKEN>` | `docs/media/resumable_upload.md` |

```
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

---

## Versioning

| Fact | Value |
|---|---|
| Current | `v26.0` (released 2026-07-29) |
| Oldest still served | `v21.0`, ends 2027-01-21 |
| Cadence | New version roughly quarterly; each lives about two years |
| Rule | Pin in config, bump deliberately after reading the changelog; a URL without a version resolves to the oldest live one |

Details: `docs/common/versioning.md`.

---

## Timeout defaults

| Category | Calls | Connect / read |
|---|---|---|
| Send and mark read | `/messages` | 5 s / 30 s |
| Media upload | `/media` (multipart up to 100 MB) | 5 s / 60 s |
| Media download | signed URL | 5 s / 60 s |
| Management reads | templates, numbers, WABA, analytics | 5 s / 30 s |
| Webhook handler | your side | answer 200 in well under a second; do the work after |

---

## Retry strategy

| Signal | Retry? | Action |
|---|---|---|
| 200 on send | No | Accepted. Track the wamid; outcome comes by webhook |
| 4xx with `code` in AUTH / ACCOUNT / TEMPLATE / QUOTA bucket | No | Systemic. Stop the channel, fix config or template, resume by hand |
| `131049` | After 24 h | Per-user marketing limit for that recipient |
| `131056` | After about 1 h | Rapid messaging to one recipient |
| `130429`, `131048`, `80007/80008`, `4` | After backoff | Rate or throughput limit; slow down |
| `131026`, `131047`, `131051`, `131052`, `131053` | No | Per-recipient or per-message failure; fail the row, keep the channel |
| 5xx, `1`, `2`, `131000`, `131016`, `131045` | Yes, backoff 1 s → 2 s → 4 s, 3 attempts | Transient on Meta's side |
| Transport error / timeout | Yes, same backoff | Mark CONNECT if persistent |
| Webhook POST failed on your side | Meta retries | Graph docs: decreasing frequency over 36 h; WhatsApp overview: up to 7 days. Make the consumer idempotent |

The full code table with Meta's own recommendations and the bucket per code: `docs/common/errors.md`.

---

## Error bucket taxonomy

| Bucket | Meaning | Examples | Channel effect |
|---|---|---|---|
| AUTH | token or permission | 190, 10, 0, 3, 131005, 200-299 | pause channel |
| ACCOUNT | WABA or number not usable | 33, 131031, 131037, 131042, 131057, 133xxx registration | pause channel |
| TEMPLATE | template missing, paused, mismatched | 132000-132069, 134100-134102 | pause channel |
| QUOTA | rate, throughput, spend | 4, 80007, 130429, 131048, 131064, 133016 | pause or slow |
| DEFERRED | try this recipient later | 131049 (24 h), 131056 (1 h) | row waits |
| REJECTED | this recipient or message cannot be sent | 131026, 131047, 131051, 131052, 131053 | row fails |
| RETRY | transient | 1, 2, 131000, 131016, 131045, unknown codes | row retries |

---

## Config variables (.env.example)

```bash
# Graph API
WHATSAPP_API_BASE_URL=https://graph.facebook.com
WHATSAPP_API_VERSION=v26.0

# Identity (System User token with whatsapp_business_messaging + whatsapp_business_management)
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_APP_ID=            # only for resumable uploads (template header samples)

# Webhooks
WHATSAPP_APP_SECRET=        # HMAC key for X-Hub-Signature-256
WHATSAPP_VERIFY_TOKEN=      # echoed in the GET handshake

# Client behaviour
WHATSAPP_TIMEOUT_CONNECT_SECONDS=5
WHATSAPP_TIMEOUT_READ_SECONDS=30
WHATSAPP_DAILY_CAP=250      # mirror the messaging tier
WHATSAPP_TEST_PHONE=        # non-prod: every send is redirected here
```

Full catalogue and the blank-means-off conventions: `docs/common/config.md`.

---

## Known implementation in this workspace

sor-service (sharanaya-boutique) talks to Meta through `client-api/.../clientapi/feign/engagement/meta/MetaWhatsAppApiClient` (OpenFeign; `sendMessage`, `uploadMedia`, `listTemplates`), with `MetaErrorDecoder` → `MetaApiException` and the bucket enum `MetaErrorCode` in `service/.../services/engagement/meta/`. Inbound events reach it through SQS from `message-ingestion-service`, never directly. PR #1068 and PRDs message-ingestion-service#13, infrastructure_pipeline#180, sharanaya-ui#501 describe the design.
