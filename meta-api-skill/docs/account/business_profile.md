# Business Profile — Specification

> **When to load**: You are reading or updating a phone number's public WhatsApp business profile (about, address, description, email, websites, vertical, profile picture).

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET`, `POST` |
| **Path** | `/v26.0/<PHONE_NUMBER_ID>/whatsapp_business_profile` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Permissions** | `whatsapp_business_management` |
| **Purpose** | Maintain the profile customers see |
| **Idempotency / retry** | POST sets fields to the given values, so repeating is safe. Retry 5xx and 429 with backoff; 422 on an expired picture handle needs a fresh upload |

## Request

| Field | Type | Notes |
|---|---|---|
| `messaging_product` | string | Required, value `"whatsapp"` |
| `about` | string | "About" text (commonly 139 chars; limit not on fetched page: unverified 2026-10-04) |
| `address` | string | Location text |
| `description` | string | Max 512 characters |
| `email` | string | Valid email format |
| `websites` | array of strings | Max 2 entries |
| `vertical` | enum | See below |
| `profile_picture_handle` | string | POST only; from the Resumable Upload API |

`vertical` values (21): `OTHER`, `AUTO`, `BEAUTY`, `APPAREL`, `EDU`, `ENTERTAIN`, `EVENT_PLAN`, `FINANCE`, `GROCERY`, `GOVT`, `HOTEL`, `HEALTH`, `NONPROFIT`, `PROF_SERVICES`, `RETAIL`, `TRAVEL`, `RESTAURANT`, `ALCOHOL`, `ONLINE_GAMBLING`, `PHYSICAL_GAMBLING`, `OTC_DRUGS`.

GET `fields`: the same names plus `profile_picture_url` (read-only URL; field name known from the Cloud API but not on the fetched page: unverified 2026-10-04).

## Example request
```bash
# Read
curl -s -G "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/whatsapp_business_profile" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=about,address,description,email,profile_picture_url,websites,vertical"

# Update
curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/whatsapp_business_profile" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "messaging_product": "whatsapp",
        "about": "Handcrafted festive wear",
        "description": "Boutique for sarees and lehengas.",
        "email": "care@example.com",
        "websites": ["https://example.com"],
        "vertical": "APPAREL",
        "profile_picture_handle": "<HANDLE>" }'
```

### Profile picture flow
```bash
curl -s -X POST "https://graph.facebook.com/v26.0/<APP_ID>/uploads?file_name=logo.jpg&file_length=51200&file_type=image/jpeg" \
  -H "Authorization: Bearer <TOKEN>"                 # -> {"id":"upload:<ID>"}
curl -s -X POST "https://graph.facebook.com/v26.0/upload:<ID>" \
  -H "Authorization: OAuth <TOKEN>" -H "file_offset: 0" --data-binary @logo.jpg   # -> {"h":"<HANDLE>"}
```

## Response
GET:
```json
{ "data": [ { "about": "Handcrafted festive wear", "address": "<ADDRESS>",
              "description": "Boutique for sarees and lehengas.", "email": "care@example.com",
              "profile_picture_url": "https://...", "websites": ["https://example.com"],
              "vertical": "APPAREL", "messaging_product": "whatsapp" } ] }
```
POST: `{ "success": true }`.

(The `data` array wrapper on GET is the Cloud API convention; exact shape unverified 2026-10-04.)

## Errors
| HTTP / code | Meaning | Action | Retry? |
|---|---|---|---|
| 400 | Invalid parameters (bad email, over 2 websites, over length) | Fix | No |
| 401 | Missing or invalid token | Replace | No |
| 403 | Insufficient permissions | Grant permission | No |
| 404 | Phone number ID not found | Verify id | No |
| 422 | Valid parameters but unprocessable, e.g. expired image handle | Re-upload picture | After fix |
| 429 | Rate limit | Backoff | Yes |
| 500 | Transient | Backoff | Yes |

## Quirks and gotchas
- `messaging_product: "whatsapp"` is mandatory on POST.
- POST only changes fields you send; omitted fields stay.
- The picture handle can expire; upload immediately before the POST.
- The upload step uses `Authorization: OAuth`, not `Bearer`.
- Documented upload types: PDF, JPEG, JPG, PNG, MP4; use JPEG or PNG for profile pictures.
- Display name (`verified_name`) is NOT edited here; it goes through name review (see phone_numbers.md `name_status`).
- `ALCOHOL`, `ONLINE_GAMBLING`, `PHYSICAL_GAMBLING`, `OTC_DRUGS` verticals are restricted commerce categories; expect policy review.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/whatsapp-business-profile-api
- https://developers.facebook.com/docs/graph-api/guides/upload

Empty or 404: none. Unverified: `about` length limit, `profile_picture_url` name and GET response wrapper.

## Validation rules to enforce client-side
| Field | Rule |
|---|---|
| `description` | 512 characters or fewer |
| `websites` | 2 entries or fewer, each a full https URL |
| `email` | Must parse as an email address |
| `vertical` | One of the 21 enum values, uppercase |
| `messaging_product` | Constant `whatsapp` |

## Update workflow
1. GET the current profile and keep a snapshot for rollback.
2. If the picture changes, run the two-step upload and capture the handle.
3. POST only changed fields plus `messaging_product`.
4. GET again and diff to confirm.
5. On 422 re-upload the picture and retry once; on 400 fix input and do not retry.

## Rollback example
```bash
curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/whatsapp_business_profile" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "messaging_product": "whatsapp", "description": "<PREVIOUS_DESCRIPTION>" }'
```

## Where this shows up
The profile is visible to customers when they open the chat. Keep it consistent with your verified business name and website; mismatches can slow business verification and tier upgrades (see messaging_limits_tiers.md).
