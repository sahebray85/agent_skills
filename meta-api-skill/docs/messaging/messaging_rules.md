# Messaging Rules — Specification

> **When to load**: Deciding whether a message may be sent (24 h window, template vs free-form, opt-in), or diagnosing limits: per-user marketing limits, US marketing pause, throughput, messaging tiers and `message_status` values.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | n/a (policy and limits reference for `POST /{version}/{phone-number-id}/messages`) |
| **Path** | `/{version}/{phone-number-id}/messages` |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging`; `whatsapp_business_management` to read limits and quality |
| **Purpose** | Single place for the rules that decide delivery: window, template category, opt-in, limits |
| **Idempotency / retry** | Retry policy depends on the error bucket: back off on 130429 and 131056; never loop on 131049, 131026, 131047 |

## Request

Rule set (not a request body). Inputs that matter on every send:

| Input | Type | Required | Description | Constraints |
|---|---|---|---|---|
| Customer service window | state | n/a | 24 h timer started by the user's message or call, reset by each new one | "A 24-hour timer called a customer service window starts" when a user messages or calls |
| Message type | choice | yes | Free-form (service) inside the window; template outside | Templates "are the only type of message that can be sent ... outside of a customer service window" |
| Template status | state | yes | Must be `APPROVED` | Pending, rejected, paused or disabled templates fail |
| Opt-in | consent | yes | "You can only send messages to WhatsApp users who have opted in to receiving messages from you" | Record source and time per user |
| Category | enum | yes (templates) | marketing, utility, authentication | Marketing is subject to per-user limits and pauses |

### Window and message type
- Inside the window: text, media, interactive, reaction, location, contacts and templates are all allowed. Service messages "do not require pre-approval".
- Outside the window: only approved templates. A free-form send returns 131047 (re-engagement).
- Each new inbound message or call resets the timer to 24 h. Outbound messages, read receipts and typing indicators do not.

### Opt-in
Meta requires prior opt-in from each recipient. Meta's dedicated opt-in policy page rendered empty in this run, so only the one-line rule above is verified from the send-messages page; detailed wording (how consent may be collected, off-WhatsApp opt-in, opt-out handling) is unverified 2026-10-04. Practical guidance: honour STOP-style replies immediately, store consent timestamp and channel, and do not send marketing to users who opted out.

### Per-user marketing template limits (error 131049)
Meta limits how many marketing templates one WhatsApp user receives across all businesses; when a user has recently received many, delivery of your marketing template can be withheld with error 131049 even when your own account limits are fine. Utility and authentication templates and free-form service messages in the window are not marketing sends. The dedicated limits page returned empty in this run, so the exact thresholds, the time windows and any exceptions are unverified 2026-10-04. Treat 131049 as "do not retry now".

### US pause
Marketing templates to US phone numbers (+1) have been paused since 2025-04-01, as stated by Meta's per-user-limits and marketing pages in the earlier research run (kept as stated; the pages re-fetched this run were empty, so current status is unverified 2026-10-04). Utility and authentication templates to +1 numbers are not part of that pause. Expect `message_status: paused` or a failure for +1 marketing sends.

### Throughput (messages per second)
- Default: "up to 80 messages per second (mps) by default".
- Automatic upgrade: "up to 1,000 mps". Eligibility: the business portfolio has an unlimited messaging limit; the number messaged 100K or more unique users, outside a customer service window, within a moving 24 h period; the number's `quality_score` is YELLOW or higher.
- Exceeding throughput returns 130429. During the upgrade, 131057 may be returned.
- Sending too many messages to the same user triggers a pair rate limit (131056).

### Messaging limits (tiers, unique users per rolling 24 h, outside the window)
```
Tier        Unique business-initiated users per 24 h
TIER_250    250
TIER_2K     2,000
TIER_10K    10,000
TIER_100K   100,000
UNLIMITED   unlimited
```
Read the current tier through the field `whatsapp_business_manager_messaging_limit` on the phone number. The older field `messaging_limit_tier` is deprecated in favour of it. The 2,000 tier exists (this differs from the 250 / 1K / 10K ladder quoted in older material). The exact enum spellings (`TIER_2K` etc.) are from general Cloud API knowledge (unverified 2026-10-04); the numbers are verified.

### `message_status` values (send response, per message)
```
accepted                       Normal: message accepted for delivery processing
held_for_quality_assessment    Marketing message held while Meta assesses quality; delivered or dropped after
paused                         Sending paused (for example the number or category is paused)
```
The field may be absent for non-marketing messages. Final outcome always comes from `statuses` webhooks.

## Example request
```bash
# Read the messaging limit and quality for a number
curl -G "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=quality_score,whatsapp_business_manager_messaging_limit,throughput"
```
(The exact field list, including `throughput`, is an assumption to confirm against the phone-number node reference, unverified 2026-10-04.)

## Response
```json
{
  "id": "<PHONE_NUMBER_ID>",
  "quality_score": {"score": "GREEN"},
  "whatsapp_business_manager_messaging_limit": "TIER_10K"
}
```

| Field | Type | Description |
|---|---|---|
| `quality_score.score` | string | `GREEN`, `YELLOW`, `RED`, `UNKNOWN` (value set unverified 2026-10-04) |
| `whatsapp_business_manager_messaging_limit` | string | Current tier; replaces deprecated `messaging_limit_tier` |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131049 | Per-user marketing limit: withheld for ecosystem health | Wait; do not hammer; consider utility content or another channel | Later only |
| 131056 | Pair rate limit (same recipient) | Slow per-recipient sends | Yes, backoff |
| 131026 | Recipient not a WhatsApp user or cannot receive | Mark undeliverable | No |
| 131047 | Outside 24 h window | Use template | No (switch type) |
| 131053 | Media upload error | Fix media | After fixing |
| 130429 | Throughput exceeded | Reduce rate | Yes, backoff |
| 131057 | Account maintenance or throughput upgrade in progress | Wait | Yes |
| 131048 | Spam rate limit hit (unverified 2026-10-04) | Improve quality, pause | After cool-down |
| 131050 | User opted out of marketing from this business (unverified 2026-10-04) | Stop marketing to this user | No |

## Quirks and gotchas
- Limits count unique recipients per rolling 24 h of business-initiated (template, outside window) conversations, not messages.
- 131049 can hit one user while others succeed; it is per-recipient, not an account fault.
- A 200 response with `message_status: held_for_quality_assessment` or `paused` is not a delivery guarantee.
- Delivery order of multiple messages is not guaranteed; do not chain dependent sends without waiting for `sent` or `delivered`.
- US (+1) marketing is paused; route such users to utility templates or other channels.
- Raising tier needs quality and volume; throughput upgrade to 1,000 mps needs unlimited tier and 100K unique users in 24 h.
- Always record opt-in; Meta can restrict accounts for sending to non-opted-in users.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages (24 h window, free-form vs template, opt-in sentence, link caching)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/throughput (80 / 1,000 mps, eligibility, 130429, 131057)
- Earlier run: messaging-limits page (tiers, deprecated field), reference/messages (`message_status`)

Rendered empty (facts marked unverified):
- https://developers.facebook.com/documentation/business-messaging/whatsapp/marketing-messages/per-user-marketing-template-message-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-marketing-template-message-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement/opt-in
