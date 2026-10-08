# Template, Phone Number and Account Webhooks — Specification

> **When to load**: You handle non-message webhook fields: template approval/quality/category changes, phone number tier or quality changes, account restrictions and alerts.

## Quick Reference
| Field (`changes[].field`) | Purpose | Key value fields |
|---|---|---|
| `message_template_status_update` | Template approval lifecycle | `event`, `message_template_id`, `message_template_name`, `message_template_language`, `reason`, `message_template_category`, `rejection_info` |
| `message_template_quality_update` | Quality rating change | `previous_quality_score`, `new_quality_score`, template id/name/language |
| `template_category_update` | Category recategorisation | `new_category`, `correct_category`, `category_update_timestamp`, `previous_category` |
| `phone_number_quality_update` | Messaging tier changes | `display_phone_number`, `event`, `current_limit` |
| `account_update` | WABA-level events | `event`, `waba_info`, `restriction_info`, `violation_type`... |
| `account_alerts` | Alerts | `entity_type`, `entity_id`, `alert_info{...}` |
All envelopes: `object: whatsapp_business_account`, `entry[].id` = WABA id, `entry[].time` = unix seconds (number).

## message_template_status_update
| Field | Notes |
|---|---|
| `event` | `APPROVED`, `ARCHIVED`, `UNARCHIVED`, `DELETED`, `DISABLED`, `FLAGGED`, `IN_APPEAL`, `LIMIT_EXCEEDED`, `LOCKED`, `PAUSED`, `PENDING`, `REINSTATED`, `PENDING_DELETION`, `REJECTED` |
| `reason` | `ABUSIVE_CONTENT`, `CATEGORY_NOT_AVAILABLE`, `INCORRECT_CATEGORY`, `INVALID_FORMAT`, `NONE`, `PROMOTIONAL`, `SCAM`, `TAG_CONTENT_MISMATCH` |
| `message_template_id` | number |
| `message_template_category` | e.g. `UTILITY`, `MARKETING` |
| `rejection_info.reason` / `.recommendation` | Present on rejection example |
`disable_info` and `other_info` appear on PAUSED/DISABLED events in some references; not shown on the fetched page (unverified 2026-10-04).
```json
{ "object": "whatsapp_business_account", "entry": [ { "id": "<WABA_ID>", "time": 1751247548, "changes": [ { "field": "message_template_status_update",
  "value": { "event": "REJECTED", "message_template_id": 1689556908129835, "message_template_name": "abandoned_cart", "message_template_language": "en",
    "reason": "INVALID_FORMAT", "message_template_category": "MARKETING",
    "rejection_info": { "reason": "Your template has parameters placed next to each other ...", "recommendation": "Separate parameters with descriptive text ..." } } } ] } ] }
```

## message_template_quality_update
`previous_quality_score`, `new_quality_score` in `GREEN` (high), `YELLOW` (medium), `RED` (low), `UNKNOWN` (pending). Example: GREEN -> YELLOW for `welcome_template`, language `en-US`. Template pausing on low quality is covered in `docs/templates/lifecycle_quality.md`.

## template_category_update
Two shapes: (1) 24 h notice with `new_category`, `correct_category`, `category_update_timestamp` (unix seconds of the planned change); (2) completed change with `previous_category`, `new_category`. Categories shown: `MARKETING`, `UTILITY`. A UTILITY template flipped to MARKETING changes billing and per-user marketing limits.

## phone_number_quality_update
`event`: `ONBOARDING`, `THROUGHPUT_UPGRADE`. `current_limit`: `TIER_50`, `TIER_250`, `TIER_2K`, `TIER_10K`, `TIER_100K`, `TIER_NOT_SET`, `TIER_UNLIMITED`. Page notes `current_limit` and `old_limit` "will be removed in February, 2026" in favour of `max_daily_conversations_per_business`. That date has passed (today 2026-10-04): prefer `max_daily_conversations_per_business`; whether the old fields are now gone is unverified 2026-10-04.
```json
{ "field": "phone_number_quality_update", "value": { "display_phone_number": "15550000000", "event": "THROUGHPUT_UPGRADE", "current_limit": "TIER_UNLIMITED" } }
```

## account_update
Events: `ACCOUNT_DELETED`, `ACCOUNT_RESTRICTION`, `ACCOUNT_VIOLATION`, `ACCOUNT_OFFBOARDED`, `ACCOUNT_RECONNECTED`, `AD_ACCOUNT_LINKED`, `AUTH_INTL_PRICE_ELIGIBILITY_UPDATE`, `BUSINESS_PRIMARY_LOCATION_COUNTRY_UPDATE`, `DISABLED_UPDATE`, `MM_LITE_TERMS_SIGNED`, `PARTNER_ADDED`, `PARTNER_REMOVED`, `PARTNER_APP_INSTALLED`, `PARTNER_APP_UNINSTALLED`, `PARTNER_CLIENT_CERTIFICATION_STATUS_UPDATE`, `VOLUME_BASED_PRICING_TIER_UPDATE`.
Other fields: `waba_info{waba_id, owner_business_id, solution_id, solution_partner_business_ids[]}`, `restriction_info[]{restriction_type (e.g. RESTRICTED_BIZ_INITIATED_MESSAGING), expiration}`, `violation_type` (e.g. ADULT), certification `status` (`APPROVED`, `FAILED`, `PENDING`, `DISCARDED`, `REVOKED`).
```json
{ "field": "account_update", "value": { "event": "ACCOUNT_RESTRICTION", "restriction_info": [ { "restriction_type": "RESTRICTED_BIZ_INITIATED_MESSAGING", "expiration": 1641330498 } ] } }
```

## account_alerts
`entity_type`: `BUSINESS`, `PHONE_NUMBER`, `CURRENT_STATUS_ID`. `alert_info`: `alert_severity` (`CRITICAL`, `WARNING`, `INFORMATIONAL`), `alert_status` (`ACTIVE`, `NONE`), `alert_type` (`INCREASED_CAPABILITIES_ELIGIBILITY_DEFERRED`, `..._FAILED`, `..._NEED_MORE_INFO`, `OBA_APPROVED`, `OBA_REJECTED`, `PROFILE_PICTURE_LOST`), `alert_description`.

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| `event=REJECTED` | Template rejected | Read `rejection_info`, fix text/category, resubmit | After fix |
| `event=PAUSED` / `DISABLED` | Quality-driven pause | Stop sending that template; see quality doc | After pause ends / new template |
| `ACCOUNT_RESTRICTION` | Messaging restricted until `expiration` | Stop business-initiated sends | After expiry |
| `RED` quality | Template at risk | Review content/targeting | n/a |

## Quirks and gotchas
- `message_template_id` is numeric here, string in many REST responses; normalise.
- Update your template table by `message_template_id`, not name (name+language is the Graph key but ids are stable).
- Events may repeat; handle idempotently.
- `entry[].id` is the WABA, not a phone number id.
- Phone-number-level events in this family carry `display_phone_number`, not `phone_number_id`.

## Sources (verified 2026-10-04)
Base `https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/` + `message_template_status_update`, `message_template_quality_update`, `template_category_update`, `phone_number_quality_update`, `account_update`, `account_alerts`.
Returned 404 (old path): `/docs/whatsapp/business-management-api/webhooks/reference/message_template_status_update`. Rendered empty: `.../webhooks/reference/message-template-status-update` (hyphen form) in an earlier run.
