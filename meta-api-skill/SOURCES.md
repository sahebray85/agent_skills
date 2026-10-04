# Meta WhatsApp documentation — URL map and verification status

Meta's docs are public (no login), but in 2026 most WhatsApp pages moved from
`https://developers.facebook.com/docs/whatsapp/...` to
`https://developers.facebook.com/documentation/business-messaging/whatsapp/...`. Many old URLs now 404 or
render only a header. **Try the new path first, then the old one.** The fetcher used by this skill returns the
page as markdown; a result that is only "Meta for Developers" means the page did not render, not that the fact
is false.

Status key: **OK** = returned content on the date shown; **EMPTY** = rendered without content; **404** = not found.

## Core and Graph mechanics

| Topic | URL | Status |
|---|---|---|
| Graph API overview | https://developers.facebook.com/docs/graph-api | OK 2026-10-04 (landing page; names v26.0) |
| Changelog (versions, EOL dates) | https://developers.facebook.com/docs/graph-api/changelog | OK 2026-10-04 |
| Webhooks getting started (handshake, signature, retries 36 h) | https://developers.facebook.com/docs/graph-api/webhooks/getting-started | OK 2026-10-04 |
| Rate limiting (BUC, X-Business-Use-Case-Usage) | https://developers.facebook.com/docs/graph-api/overview/rate-limiting | see `docs/common/rate_limits.md` |
| Meta "REST API" framework (not WhatsApp) | https://developers.facebook.com/documentation/rest-api/overview | OK 2026-10-04 |

## Cloud API (messaging, media, errors)

| Topic | URL | Status |
|---|---|---|
| Messages reference | https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages | OK 2026-10-04 |
| Media reference (limits, 30-day ids, 5-min URLs) | https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media | OK 2026-10-04 |
| Error codes | https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes | OK 2026-10-04 |
| Phone numbers reference | https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers | see `docs/account/phone_numbers.md` |
| Business profiles | https://developers.facebook.com/docs/whatsapp/cloud-api/reference/business-profiles | see `docs/account/business_profile.md` |
| Registration | https://developers.facebook.com/docs/whatsapp/cloud-api/reference/registration | see `docs/account/phone_numbers.md` |
| Messaging limits | https://developers.facebook.com/docs/whatsapp/messaging-limits | see `docs/account/messaging_limits_tiers.md` |

## Templates

| Topic | URL | Status |
|---|---|---|
| Message Template API reference (`fields, limit, after, before`) | https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api | OK 2026-10-04 |
| Template management | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management/ | OK 2026-10-04 |
| Template components | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/components | OK 2026-10-04 |
| Per-user marketing limits | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-limits | OK 2026-10-04 |

## Webhooks (WhatsApp)

| Topic | URL | Status |
|---|---|---|
| Webhooks overview (fields, 7-day retries) | https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview | OK 2026-10-04 |
| Webhooks landing page | https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/ | EMPTY 2026-10-04 |
| Status webhook reference | https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/status | OK 2026-10-04 |
| Text message webhook reference | https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/text | OK 2026-10-04 |
| Template status update webhook | https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message-template-status-update | EMPTY 2026-10-04 |

## Billing

| Topic | URL | Status |
|---|---|---|
| Pricing (per-message model, INR dates) | https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing | OK 2026-10-04 |

## Standards referenced

| Topic | URL |
|---|---|
| RFC 8058 one-click unsubscribe | https://www.rfc-editor.org/rfc/rfc8058 |
| E.164 numbering | https://www.itu.int/rec/T-REC-E.164 |

## How to refresh this cache

1. Fetch the page; if it renders empty, try the other path family and the Wayback Machine.
2. Update the file in `docs/`, change its "Sources (verified …)" date, and remove the "(unverified …)" marks you confirmed.
3. Update the status column here.
