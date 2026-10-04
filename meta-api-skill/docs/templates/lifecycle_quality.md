# Template Lifecycle, Quality and Pausing — Specification

> **When to load**: You need to reason about template statuses, quality scores, pausing/pacing, disable events, or the webhooks and send errors they produce.

## Quick Reference
| Field | Value |
|---|---|
| **Read via** | `GET /v26.0/<WABA_ID>/message_templates?fields=status,quality_score,rejected_reason` |
| **Push via webhooks** | `message_template_status_update`, `message_template_quality_update` (and category updates) |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Sendable only when** | `status == APPROVED` |
| **Quality values** | `GREEN`, `YELLOW`, `RED`, `UNKNOWN` |

## Status lifecycle
| Status | Meaning |
|---|---|
| `PENDING` | In automatic review (up to 24 hours) |
| `APPROVED` | Sendable |
| `REJECTED` | Review failed; see `rejected_reason`; editable, unlimited edits |
| `PAUSED` | Recurring negative feedback or low read rates; cannot be sent; editable |
| `DISABLED` | Sustained poor feedback; cannot be sent |
| `IN_APPEAL` | Appeal submitted ("Appeal Requested" in Manager) |
| `LIMIT_EXCEEDED` | Template count cap reached |
| `ARCHIVED` | Auto-archived after 12+ months of inactivity (28-day deletion window per guide) |
| `PENDING_DELETION` | Delete requested while messages pending; 30 days then removed |
| `DELETED` | Gone; name locked 30 days if it was approved |

Webhook `event` values for `message_template_status_update`: `APPROVED`, `ARCHIVED`, `UNARCHIVED`, `DELETED`, `DISABLED`, `FLAGGED`, `IN_APPEAL`, `LIMIT_EXCEEDED`, `LOCKED`, `PAUSED`, `PENDING`, `REINSTATED`, `PENDING_DELETION`, `REJECTED`.

Payload fields: `event`, `message_template_id`, `message_template_name`, `message_template_language`, `reason`, `message_template_category`; conditional `disable_info.disable_date` (Unix timestamp), `other_info.title` / `other_info.description` (locked/unlocked), `rejection_info.reason` / `rejection_info.recommendation` (INVALID_FORMAT).

Reasons: `ABUSIVE_CONTENT`, `INCORRECT_CATEGORY`, `INVALID_FORMAT`, `NONE`, `PROMOTIONAL`, `SCAM`, `TAG_CONTENT_MISMATCH` (the API object also lists `CATEGORY_NOT_AVAILABLE`).

```json
{ "entry": [ { "id": "<WABA_ID>", "changes": [ { "field": "message_template_status_update",
  "value": { "event": "PAUSED", "message_template_id": 0,
             "message_template_name": "festive_sale",
             "message_template_language": "en_US", "reason": "NONE" } } ] } ] }
```
(The numeric id is a placeholder.)

## Quality rating
| Score | Meaning |
|---|---|
| `GREEN` | High quality, safe to send |
| `YELLOW` | Medium, at risk |
| `RED` | Low, may be paused |
| `UNKNOWN` | Pending feedback |
All of High/Medium/Low remain sendable until the template is actually paused. Change notifications arrive on `message_template_quality_update`.

## Pacing and pausing
- Pacing applies to marketing and utility templates that are newly created, unpaused, or lack a GREEN rating.
- During pacing, messages go through until an unspecified threshold, then are held to wait for customer feedback. Improving signals release them; worsening signals cause them to be dropped.
- Utility templates are paced for 7 days after a pause event.
- A template becomes `PAUSED` when feedback is negative and drops quality to low.
- Messages API responses can carry `message_status` of `accepted` or `held_for_quality_assessment`.
- Pause durations (commonly cited 3 h / 6 h / disabled on third pause) were NOT on any fetched page: (unverified 2026-10-04). Do not hard-code them; react to webhooks.

## Send-time errors tied to lifecycle
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 132001 | Template missing or not approved in that language | Check name, language, status | No |
| 132015 | Template paused for low quality | Edit template to improve quality, wait for REINSTATED | No (until restored) |
| 132016 | Template permanently disabled | Create new template with different content | No |
| 132000 | Parameter count mismatch | Send all variables | No |
| 132005 | Hydrated text too long | Shorten variable values | No |
| 132007 | Content violates format/character policy | Review policy | No |
| 132012 | Parameter format mismatch | Fix parameter type/format | No |
| 132018 | Parameter issue in template (400) | Review and fix template parameters | No |
| 132068 / 132069 | Flow blocked / throttled | See Flows docs; not on the fetched error page (unverified 2026-10-04) | 132069 later |

## Operational guidance
1. Subscribe to the WABA (`POST /<WABA_ID>/subscribed_apps`) so status/quality webhooks arrive.
2. Persist `status` and `quality_score` per (name, language); gate sends on `APPROVED`.
3. On `PAUSED`/`FLAGGED`, stop campaigns using that template; edit it (unlimited edits while paused).
4. On `DISABLED`, create a replacement with new wording and a new name.
5. Treat `ARCHIVED` templates as unsendable until `UNARCHIVED`.

## Quirks and gotchas
- A rejected template has `rejected_reason` NONE when it is not rejected; do not branch on presence of the field.
- `FLAGGED` and `LOCKED` events exist but their exact semantics are only described by `other_info` text; surface the title/description to humans.
- `template_category_update` and `message_template_quality_update` payload schemas were not on the fetched webhook page (unverified 2026-10-04).
- Per-user marketing limits (131049) are unrelated to quality; see marketing_limits.md.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-pacing
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-quality
- https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update
- https://developers.facebook.com/docs/whatsapp/message-templates/guidelines
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management/
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes

Empty render: https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-pacing-and-quality (header only). Pause durations and review SLA beyond "up to 24 hours" unverified.

## State diagram (informal)
```text
create -> PENDING -> APPROVED -> (negative feedback) -> PAUSED -> edit -> REINSTATED/APPROVED
                 \-> REJECTED -> edit -> PENDING
APPROVED -> (sustained poor quality) -> DISABLED  (terminal, create new template)
APPROVED -> (12+ months unused) -> ARCHIVED -> UNARCHIVED
any -> delete -> PENDING_DELETION (30 days, if messages pending) -> DELETED
REJECTED -> appeal -> IN_APPEAL -> APPROVED or REJECTED
```
This diagram is a synthesis of the documented statuses and events; the exact transitions between FLAGGED, LOCKED and REINSTATED are unverified 2026-10-04.

## Monitoring checklist
| Signal | Where | Suggested reaction |
|---|---|---|
| status `PAUSED` | webhook or list | Halt campaigns, edit template |
| status `DISABLED` | webhook (`disable_info.disable_date`) | Replace template |
| quality `RED` | quality webhook / list | Reduce volume, review wording and audience |
| `held_for_quality_assessment` | send response `message_status` | Expect delayed or dropped messages; do not resend |
| 132015 on send | send failure webhook | Stop sending that template |
| 132001 on send | send failure webhook | Check name/language mismatch before blaming Meta |

## Storing state
Keep a table keyed by (waba_id, name, language) with: template_id, status, category, quality_score, rejected_reason, last_event_at, last_synced_at. Update from webhooks first and reconcile with a periodic list call (daily is enough).

## Webhook handler skeleton
```text
on message_template_status_update(value):
    key = (waba_id, value.message_template_name, value.message_template_language)
    upsert template_state(key, status=value.event, reason=value.reason,
                          category=value.message_template_category, updated_at=now)
    if value.event in (PAUSED, DISABLED, FLAGGED, LOCKED): pause_campaigns(key)
    if value.event in (APPROVED, REINSTATED, UNARCHIVED):  resume_campaigns(key)
    if value.rejection_info: store(value.rejection_info.reason, value.rejection_info.recommendation)
```
Make the handler idempotent: webhooks can be delivered more than once and out of order, so compare timestamps before overwriting newer state.
