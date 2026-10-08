# WhatsApp Business Account (WABA) — Specification

> **When to load**: You need to read WABA metadata, list a business's WABAs (`owned_whatsapp_business_accounts`), or subscribe/unsubscribe an app to WABA webhooks (`subscribed_apps`).

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` WABA; `GET/POST/DELETE` `subscribed_apps`; `GET` business `owned_whatsapp_business_accounts` |
| **Path** | `/v26.0/<WABA_ID>`, `/v26.0/<WABA_ID>/subscribed_apps`, `/v26.0/<BUSINESS_ID>/owned_whatsapp_business_accounts` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Permissions** | `whatsapp_business_management`; business edge also `business_management`, `whatsapp_business_messaging`, `public_profile`, and an Admin System User token |
| **Purpose** | Inspect account, enumerate account IDs, control webhook subscription |
| **Idempotency / retry** | GETs safe. POST subscribed_apps is safe to repeat (re-subscribing the same app). DELETE repeatable (404 if already gone). Retry 5xx / `is_transient` |

## Request

### GET WABA
`fields` (comma-separated) accepts, per the reference page: `id`, `name`, `timezone_id`, `message_template_namespace`, `account_review_status`, `business_verification_status`, `country`, `ownership_type`, `primary_business_location`.
Fields such as `currency` and `marketing_messages_lite_api_status` were not on the page excerpt (unverified 2026-10-04); request them and handle error 100 if rejected.

### GET `owned_whatsapp_business_accounts`
No parameters. Cursor pagination (`paging.cursors.before/after`). Read-only (no create/update/delete).

### `subscribed_apps`
| Verb | Params | Notes |
|---|---|---|
| GET | `fields` = `id`, `name`, `link` | Lists apps subscribed to this WABA's webhooks |
| POST | `override_callback_uri` (string, HTTPS, replaces app default), `verify_token` (string) | Subscribes the calling app; both body fields optional |
| DELETE | none | Unsubscribes; notifications stop immediately |

## Example request
```bash
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,name,timezone_id,message_template_namespace,account_review_status,business_verification_status,ownership_type"

curl -s -G "https://graph.facebook.com/v26.0/<BUSINESS_ID>/owned_whatsapp_business_accounts" \
  -H "Authorization: Bearer <TOKEN>"

# subscribe this app (default callback)
curl -s -X POST "https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps" \
  -H "Authorization: Bearer <TOKEN>"

# subscribe with per-WABA callback override
curl -s -X POST "https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "override_callback_uri": "https://example.com/webhooks/whatsapp", "verify_token": "<VERIFY_TOKEN>" }'

curl -s "https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer <TOKEN>"
curl -s -X DELETE "https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer <TOKEN>"
```

## Response
```json
{ "id": "<WABA_ID>", "name": "Example Boutique", "timezone_id": "1",
  "message_template_namespace": "<NAMESPACE>" }
```
```json
{ "data": [ { "id": "<WABA_ID>", "name": "Example Boutique",
              "timezone_id": "1", "message_template_namespace": "<NAMESPACE>" } ],
  "paging": { "cursors": { "before": "<CURSOR>", "after": "<CURSOR>" } } }
```
```json
{ "success": true }
```
| Field | Meaning |
|---|---|
| `id` | WABA ID |
| `name` | Account name |
| `timezone_id` | Meta timezone id (also drives billing/analytics day boundaries) |
| `message_template_namespace` | Namespace for legacy template references |
| `account_review_status` | Review state of the account |
| `business_verification_status` | Business verification state |
| `ownership_type` | Own vs client-owned |

## Errors
| Code / HTTP | Meaning | Action | Retry? |
|---|---|---|---|
| 100 / 400 | Invalid parameter or bad WABA id format or bad callback URI | Fix | No |
| 190 / 401 | Invalid or expired token | Replace | No |
| 200 / 403 | Missing permission, or app cannot (un)subscribe | Grant permission | No |
| 803 / 404 | WABA not found, or no subscription to delete | Verify id | No |
| 422 | Fields unavailable; callback unreachable; cannot unsubscribe due to active integrations | Fix callback / fields | No |
| 80008 | Rate limit on business edge | Backoff | Yes |
| 2 / 500 | Transient | Backoff | Yes |

## Quirks and gotchas
- Webhooks only flow after `POST subscribed_apps`; a correctly configured app dashboard callback is not enough per WABA.
- `override_callback_uri` is per WABA override of the app-level callback; verify the endpoint answers the GET challenge with `verify_token` first, otherwise 422.
- `owned_whatsapp_business_accounts` lists WABAs the business owns; client-shared WABAs are a separate edge (`client_whatsapp_business_accounts`, mentioned but not verified: unverified 2026-10-04).
- The business edge requires an Admin System User token; employee system users get error 200.
- `GET` of the WABA node does not return phone numbers or templates; use `/phone_numbers` and `/message_templates` edges.
- Billing currency: every WABA of an eligible Indian customer must be INR by 2026-12-31 (see billing/pricing.md).

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/whatsapp-business-account-api
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/subscribed-apps-api
- https://developers.facebook.com/docs/graph-api/reference/business/owned_whatsapp_business_accounts/

Empty or 404: none for this file. The `client_whatsapp_business_accounts` edge and `currency` field are unverified.

## Onboarding sequence (WABA to first send)
```text
1. GET /<BUSINESS_ID>/owned_whatsapp_business_accounts      -> find <WABA_ID>
2. GET /<WABA_ID>/phone_numbers                              -> find <PHONE_NUMBER_ID>
3. POST /<PHONE_NUMBER_ID>/register   {pin}                  -> Cloud API ready
4. POST /<WABA_ID>/subscribed_apps                           -> webhooks flow
5. GET  /<WABA_ID>/message_templates                         -> confirm approved templates
6. POST /<PHONE_NUMBER_ID>/messages                          -> send
```

## Webhook subscription checks
- After POST, run GET `subscribed_apps` and confirm your app id appears.
- If events stop, GET again: a missing entry means the subscription was removed (for example by DELETE from another system).
- Use `override_callback_uri` for per-tenant endpoints; remember the override applies to this WABA only.

## Field reference by purpose
| Need | Field |
|---|---|
| Show the account name | `name` |
| Align reports to local days | `timezone_id` |
| Legacy template namespace | `message_template_namespace` |
| Gate features on verification | `business_verification_status` |
| Account standing | `account_review_status` |
