# Edit and Delete Message Templates — Specification

> **When to load**: You must change an existing template's content or category rules, or remove templates by name or ID.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` (edit), `DELETE` (delete) |
| **Path (edit)** | `/v26.0/<TEMPLATE_ID>` |
| **Path (delete)** | `/v26.0/<WABA_ID>/message_templates` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Permissions** | `whatsapp_business_management` |
| **Purpose** | Edit components/category/TTL of an eligible template; delete one language, all languages of a name, or up to 100 IDs |
| **Idempotency / retry** | Delete is effectively idempotent (second call returns not found). Edit consumes edit quota, so never blind-retry; GET the template first. Retry only 5xx / transient |

## Request

### Edit: `POST /<TEMPLATE_ID>`
| Field | Type | Notes |
|---|---|---|
| `components` | array | Replacement components |
| `category` | enum | Editable only for non-approved templates; an approved template's category cannot be edited |
| `message_send_ttl_seconds` | integer | Time to live |
| `parameter_format`, `sub_category`, `display_format` | per create | Same enums as create_template.md |

Edit eligibility and limits:
| Rule | Value |
|---|---|
| Editable statuses | `APPROVED`, `REJECTED`, `PAUSED` only |
| Approved template quota | 10 edits per 30 days OR 1 edit per 24 hours (the page words it as "OR"; plan for both) |
| Rejected / paused templates | Unlimited edits |
| After edit | Re-reviewed automatically; stays/returns to approved unless it fails review |
| Name and language | Cannot be changed. Create a new template instead |

### Delete: `DELETE /<WABA_ID>/message_templates`
| Param | Type | Notes |
|---|---|---|
| `name` | string | Deletes ALL languages of that name unless `hsm_id` is also given |
| `hsm_id` | string | Delete one specific language variant (pair with `name`) |
| `hsm_ids` | string (JSON array) | Up to 100 template IDs in one call |

## Example request
```bash
# Edit body
curl -s -X POST "https://graph.facebook.com/v26.0/<TEMPLATE_ID>" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "components": [
    { "type": "BODY", "text": "Hi {{1}}, order {{2}} has shipped.",
      "example": { "body_text": [["Asha","ORD-1001"]] } } ] }'

# Delete all languages by name
curl -s -X DELETE -G "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "name=order_confirmation"

# Delete one language by ID
curl -s -X DELETE -G "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "hsm_id=<TEMPLATE_ID>" --data-urlencode "name=order_confirmation"

# Batch delete
curl -s -X DELETE -G "https://graph.facebook.com/v26.0/<WABA_ID>/message_templates" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode 'hsm_ids=["<TEMPLATE_ID>","<TEMPLATE_ID>"]'
```

## Response
```json
{ "success": true }
```
| Field | Meaning |
|---|---|
| `success` | `true` when the edit was accepted for review or the delete was accepted |

Errors use the standard Graph shape: `error.message`, `error.type` (`OAuthException` / `GraphMethodException`), `error.code`, `fbtrace_id`, `is_transient`.

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid parameter (e.g. editing a non-editable field) | Fix payload | No |
| 190 | Invalid token | Replace | No |
| 200 | Insufficient permissions | Grant permission | No |
| 803 | Template not found | Verify ID, language | No |
| 2 | Transient server error | Backoff | Yes |
| 2388039 | Status cannot be changed (edit quota exceeded or status not editable) | Wait for 24 h / 30-day window or review | Later |
| 2388040 / 2388047 / 2388072 / 2388073 | Length or header/body/footer format problems | Fix content | No |

HTTP: 400, 401, 403, 404, 500.

## Quirks and gotchas
- Name reuse lock: "If you delete an approved template, you cannot create a new template with the same name for 30 days." Prefer editing over delete+recreate.
- Templates with messages pending delivery go to `PENDING_DELETION` for 30 days before removal (webhook event `PENDING_DELETION`, later `DELETED`).
- Templates unused for 12+ months can be auto-archived (`ARCHIVED`) with a 28-day deletion window per the management guide; `UNARCHIVED` exists as a webhook event.
- Deleting by `name` alone wipes every language. Always supply `hsm_id` when you mean one language.
- `hsm_ids` is a JSON-encoded string, not a repeated query key.
- Edited approved templates keep sending with the previous version until the edit is approved (behaviour not explicitly documented; unverified 2026-10-04).
- An edit that changes only the quality-relevant text of a `PAUSED` template is the documented way to try to restore it (error 132015 action: "edit template to improve quality").

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management/
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update

Empty or 404: none for this file. Unverified: behaviour of the live version while an edit is pending.

## Decision guide
```text
Need to change wording of an APPROVED template?
  -> edit (counts against 1/24h or 10/30d) -> wait for re-review
Template REJECTED or PAUSED?
  -> edit freely (unlimited) -> resubmitted automatically
Need a different category on an APPROVED template?
  -> cannot edit category; create a NEW template with a new name
Need to retire one language only?
  -> DELETE with name + hsm_id
Need to retire everything under a name?
  -> DELETE with name only (all languages)
Need to purge many?
  -> DELETE with hsm_ids (max 100 per call), loop for more
```

## Safe client pattern
1. GET the template (`fields=id,name,status,category`) and confirm status is editable.
2. Track your own edit counter per template (timestamps) to avoid hitting 2388039.
3. POST the edit once; do not auto-retry on timeouts, re-GET and compare components.
4. Wait for the `message_template_status_update` webhook before declaring success.
5. For deletes, record the deletion date and block recreating the same name for 30 days.
