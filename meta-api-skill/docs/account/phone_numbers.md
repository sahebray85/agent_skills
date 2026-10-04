# Phone Numbers — Specification

> **When to load**: You need to list or inspect business phone numbers, verify a number by SMS/voice code, register or deregister it on Cloud API, or manage its two-step PIN.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` (list/get), `POST` (request_code, verify_code, register, deregister) |
| **Path** | `/v26.0/<WABA_ID>/phone_numbers`, `/v26.0/<PHONE_NUMBER_ID>`, `/v26.0/<PHONE_NUMBER_ID>/{request_code,verify_code,register,deregister}` |
| **Auth** | `Authorization: Bearer <TOKEN>` (System User token) |
| **Permissions** | `whatsapp_business_management` |
| **Purpose** | Onboard a number and keep it registered with 2FA |
| **Idempotency / retry** | GETs safe. `register` with the same pin is safe to repeat. `request_code` is rate limited; do not loop. `verify_code` on an already-verified number returns 136024 |

## Request

### List and get
| Endpoint | Notes |
|---|---|
| `GET /<WABA_ID>/phone_numbers` | Default fields `verified_name`, `display_phone_number`, `id`, `quality_rating` |
| `GET /<PHONE_NUMBER_ID>` | Single number |

Optional `fields`: `name_status` (beta), `throughput`, `code_verification_status`, `status` (e.g. `CONNECTED`), and (per messaging-limits page) `whatsapp_business_manager_messaging_limit` (replaces deprecated `messaging_limit_tier`).
Sorting: `last_onboarded_time_ascending` (most recent last); default descending.
Beta filtering: `filtering` on `account_mode` with operator `EQUAL`, value `SANDBOX` or `LIVE` (parameter shape beyond `field`/`operator`/`value` unverified 2026-10-04).
`quality_rating` values seen: `GREEN`, `UNKNOWN`, `NA` ("etc.").

### request_code
| Param | Notes |
|---|---|
| `code_method` | `SMS` or `VOICE` |
| `language` | Locale, e.g. `en_US` |

### verify_code
| Param | Notes |
|---|---|
| `code` | Numeric string from request_code |

### register
| Param | Required | Notes |
|---|---|---|
| `messaging_product` | per example `whatsapp` | |
| `pin` | for 2FA | Exactly 6 digits you create and memorise. "Setting up two-factor authentication is a requirement to use the Cloud API" |
| `backup.data`, `backup.password` | no | Restore from backup |
| `data_localization_region` | no | Not on the fetched page (unverified 2026-10-04) |

### deregister
No body needed.

### Two-step PIN
Changing the PIN independently of register is done with `POST /<PHONE_NUMBER_ID>` body `{"pin":"<6_DIGITS>"}`; this form was not on any fetched page (unverified 2026-10-04). Registration itself sets the PIN.

## Example request
```bash
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>/phone_numbers" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,display_phone_number,verified_name,quality_rating,code_verification_status,name_status,throughput,status"

curl -s -G "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>" -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,display_phone_number,verified_name,quality_rating"

curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/request_code" \
  -H "Authorization: Bearer <TOKEN>" -d "code_method=SMS" -d "language=en_US"

curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/verify_code" \
  -H "Authorization: Bearer <TOKEN>" -d "code=<CODE>"

curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/register" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "messaging_product": "whatsapp", "pin": "<6_DIGIT_PIN>" }'

curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/deregister" \
  -H "Authorization: Bearer <TOKEN>"
```

## Response
```json
{ "data": [ { "verified_name": "Example Boutique", "display_phone_number": "<DISPLAY_NUMBER>",
              "id": "<PHONE_NUMBER_ID>", "quality_rating": "GREEN" } ],
  "paging": { "cursors": { "before": "<CURSOR>", "after": "<CURSOR>" } } }
```
Action endpoints return `{ "success": true }`.

| Field | Meaning |
|---|---|
| `id` | `<PHONE_NUMBER_ID>` used in `/messages` |
| `verified_name` | Approved display name |
| `quality_rating` | Number quality |
| `name_status` | Display-name approval state (beta) |
| `code_verification_status` | Verification state |
| `throughput` | Current throughput level (default 80 mps, upgradeable to 1,000) |
| `status` | Connection status |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 136024 (HTTP 400) | Number already verified (verify_code) | Skip to register | No |
| 133010 | Phone not registered on platform | Call register | After register |
| 133016 | Too many registration attempts | Wait for unblock | Later |
| 131045 | Registration error on send | Register the number first | After register |
| 131037 | 555 number lacks approved display name | Fix and approve name | After approval |
| 131031 | Account restricted or verification data mismatch | Check policy / health | No |
| 100 | Invalid parameter | Fix | No |
| 190 / 200 | Token invalid / permission | Fix token | No |

## Quirks and gotchas
- Numbers coming from Embedded Signup must be registered within 14 days or the flow restarts.
- PIN is exactly 6 digits; keep it in a secret store. Forgetting it blocks re-registration (use the Manager reset flow).
- Numbers shared with the WhatsApp Business app and Cloud API are fixed at 20 mps.
- Throughput upgrade to 1,000 mps: unlimited messaging limit, 100K+ unique users outside service windows in 24 h, quality YELLOW or higher; the number is unavailable for up to a minute during upgrade.
- `deregister` makes the number unusable on Cloud API until registered again.
- Never log real numbers; use placeholders in docs and fixtures.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/register-api
- https://developers.facebook.com/documentation/business-messaging/whatsapp/throughput
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes

Empty render (header only): .../reference/whatsapp-business-phone-number/whatsapp-business-phone-number-api and .../request-verification-code-api (request_code/verify_code facts came from the /docs/ page instead). Unverified: standalone two-step PIN update call, `data_localization_region`, `filtering` param shape.
