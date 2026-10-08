# Marketing Template Limits — Specification

> **When to load**: You are sending marketing templates at volume and need per-user limits, the US restriction, error 131049 handling, and related tier and billing rules.

## Quick Reference
| Field | Value |
|---|---|
| **Applies to** | Template messages with `category: MARKETING` |
| **Send endpoint** | `POST /v26.0/<PHONE_NUMBER_ID>/messages` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Key error** | `131049` "not delivered to maintain ecosystem engagement" |
| **Key rule** | Per-user cap based on that user's recent marketing read rate |
| **US (+1)** | Marketing templates not delivered to US numbers (paused since 2025-04-01) |

## How per-user limits work
- WhatsApp applies a dynamic per-user cap derived from the individual's recent marketing-message read rate and inbox saturation. Lower engagement means fewer marketing messages reach that user; engaged users stay reachable.
- Each delivered marketing template counts toward the user's limit.
- If the recipient replies to a marketing message, a 24-hour customer service window opens; marketing messages sent during that window do not consume the allocation.
- The cap is not visible via API. You only learn of it through 131049 on a failed send.

## Geographic exemptions
Limits are not currently enforced for messages from businesses in, or sent to users in, the EEA, UK, Japan and South Korea.

US: "WhatsApp does not currently deliver marketing template messages to WhatsApp users with United States phone numbers." Pause start date 2025-04-01 (from brief; page excerpt confirms the restriction but not the date: unverified 2026-10-04 for the date on the page).

## Error 131049
Returned when a per-user limit is hit, or when you retry too aggressively. Documented behaviour: if the WABA attempts to resend marketing messages several times within 24 hours to users who already reached the limit, further delivery attempts to those users may be unavailable for up to 24 hours.

| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131049 | Not delivered to maintain healthy ecosystem engagement | Wait at least 24 hours for that recipient | Not within 24 h |
| 131050 | Recipient opted out of marketing | Never retry; honour opt-out | No |
| 131048 | Blocked for spam flags / quality | Check quality in WhatsApp Manager | No |
| 131056 | Pair rate limit: too many messages to same recipient quickly | Wait before same-recipient resend | Yes, later |
| 130429 | Throughput limit reached | Slow sending | Yes, backoff |
| 131042 | Payment method issue | Fix billing / credit line | After fix |
| 131055 | Marketing Messages API: only marketing templates supported | Use marketing template | No |
| 134100 | Non-marketing template sent via Marketing Messages API | Use marketing-categorised template | No |
| 134101 | Template syncing in progress | Wait up to 10 minutes | Yes |
| 134102 | Template unavailable or ineligible | Check onboarding status or contact support | No |

## Example: handling a send failure
```bash
curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{ "messaging_product": "whatsapp", "to": "<RECIPIENT_E164>", "type": "template",
        "template": { "name": "festive_sale", "language": { "code": "en_US" } } }'
```
The 131049 outcome normally appears in the `statuses` webhook as a `failed` status with `errors[0].code = 131049`, not necessarily in the synchronous response (unverified 2026-10-04).

## Guidance for senders
1. Record 131049 per recipient with a timestamp; suppress marketing to them for 24 h minimum.
2. Never loop-retry; repeated attempts extend the unavailability.
3. Prefer reaching users inside an open service window (they replied recently) for time-sensitive offers.
4. Keep marketing templates GREEN; see lifecycle_quality.md for pacing.
5. Respect tier capacity (see account/messaging_limits_tiers.md): 250 / 2,000 / 10,000 / 100,000 / unlimited unique users per rolling 24 h at portfolio level.
6. Marketing is always charged per delivered message (see billing/pricing.md).

## Quirks and gotchas
- Campaign delivery reporting accuracy is cited by Meta as a reason not to retry within 24 h.
- Meta exposes `send_type` (`campaign` / `direct`) on templates; its relation to limits is not documented (unverified 2026-10-04).
- Marketing Messages API (134100-134102) is a separate product; template analytics have `product_type` `MARKETING_MESSAGES_API_FOR_WHATSAPP`.
- A 131049 does not mean the template is bad; do not edit or delete the template in response.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/throughput
- https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing

Empty render: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/pricing-updates-on-whatsapp-business-platform (so the US pause date is unverified).

## Suppression table design
```text
marketing_suppression(
  recipient_hash   text primary key,
  reason           text not null,      -- LIMIT_131049 | OPT_OUT_131050 | SPAM_131048
  suppressed_until timestamptz,        -- now()+24h for 131049; null (forever) for opt-out
  last_error_at    timestamptz not null
)
```
Hash or tokenise the recipient number; do not store raw numbers in logs.

## Retry policy by error
```text
131049  -> schedule no earlier than +24h, max 1 retry per day per recipient
131050  -> never retry, mark opted out
131048  -> do not retry; alert on spike (quality issue)
131056  -> retry same recipient after short delay (minutes)
130429  -> exponential backoff, reduce send rate
134101  -> retry after up to 10 minutes
```
The 131056 and 134101 delays follow the documented actions ("wait before retrying", "wait up to 10 minutes"); numeric delays are conservative suggestions.

## Capacity planning
- Unique-user tier caps (250 up to unlimited per rolling 24 h) bound how many different people you can start a conversation with.
- Per-user caps bound how often one person can be messaged. Both must pass.
- Plan campaigns as: audience -> remove suppressed -> cap by tier headroom -> pace under throughput (80 mps default).
- Stagger large campaigns across hours; template pacing may hold messages from new or non-GREEN templates anyway.

## Reporting
Use `template_analytics` (`SENT`, `DELIVERED`, `READ`, `CLICKED`, `COST`) to watch read rates. Falling read rate predicts both quality downgrades and more 131049 outcomes. Template analytics keep read/click data for 7 days after send, so export promptly (see billing/analytics.md).

## Compliance notes
- Honour opt-outs immediately; WhatsApp can also signal opt-out (131050).
- Include a clear opt-out path (quick reply button) in marketing templates.
- Do not send marketing to US numbers; skip them upstream to avoid wasted attempts.

## FAQ
- Does a higher tier lift the per-user cap? No. Tiers bound unique recipients per 24 h; the per-user cap bounds frequency per person.
- Does a reply help? Yes. A reply opens a 24-hour service window and marketing messages inside it do not consume that user's allocation.
- Is 131049 billed? Undelivered messages are not charged (billing is per delivered message).
- Can I detect a capped user in advance? No documented API; infer from past 131049 results.
- Are EEA, UK, Japan or South Korea affected? Limits are not currently enforced there, but do not rely on that staying true.

## Quick triage
```text
Send failed with 131049?  -> suppress recipient 24h, do not edit template
Send failed with 131050?  -> permanent opt-out
Send failed with 130429?  -> you are too fast, back off
Many 131048 at once?      -> quality problem, inspect audience and wording
```
