# Messaging Limits and Tiers — Specification

> **When to load**: You need to know how many unique users you can message per 24 hours, how to move up a tier, which field exposes the tier, and how throughput (mps) differs.

## Quick Reference
| Field | Value |
|---|---|
| **Read via** | `GET /v26.0/<PHONE_NUMBER_ID>?fields=whatsapp_business_manager_messaging_limit` |
| **Auth** | `Authorization: Bearer <TOKEN>` |
| **Permissions** | `whatsapp_business_management` |
| **Unit** | Unique WhatsApp user phone numbers delivered to, in a moving 24-hour window |
| **Scope** | Business portfolio level, shared by all numbers in the portfolio |
| **Tiers** | 250, 2,000, 10,000, 100,000, unlimited |

## Tiers
| Tier | Unique users / 24 h | Value shape |
|---|---|---|
| Default (unverified business) | 250 | `TIER_250` |
| 2 | 2,000 | `TIER_2K` (suffix pattern unverified 2026-10-04) |
| 3 | 10,000 | `TIER_10K` (unverified) |
| 4 | 100,000 | `TIER_100K` (unverified) |
| Unlimited | no cap | `TIER_UNLIMITED` (unverified) |

Only `TIER_250` appears verbatim on the page; the other literal values follow convention and are marked unverified.

Field note: `messaging_limit_tier` is deprecated; use `whatsapp_business_manager_messaging_limit`.

## Moving up
To reach 2,000, any one of:
1. Complete business verification with Meta.
2. Have a partner verify your business.
3. Deliver 2,000 messages outside customer service windows to unique users within a 30-day moving period using high-quality templates.

Beyond 2,000, increases are automatic when:
- Messaging quality stays consistently high across all numbers and templates.
- At least 50% of the current limit was used in the last 7 days.
Increases are applied within 6 hours once criteria are met.

Quality drops can stop upgrades or lower the tier (downgrade rules not on the page: unverified 2026-10-04).

## Example request
```bash
curl -s -G "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=id,display_phone_number,quality_rating,whatsapp_business_manager_messaging_limit,throughput"
```
Response:
```json
{ "id": "<PHONE_NUMBER_ID>", "quality_rating": "GREEN",
  "whatsapp_business_manager_messaging_limit": "TIER_250",
  "throughput": { "level": "STANDARD" } }
```
(`throughput.level` shape unverified 2026-10-04.)

## Throughput (separate from tiers)
| Item | Value |
|---|---|
| Default per number | 80 messages per second |
| Upgrade | 1,000 mps, free, automatic when eligible |
| Eligibility | Portfolio has unlimited messaging limit, number messaged 100K+ unique users outside service windows in 24 h, quality YELLOW or higher |
| Upgrade impact | Number unavailable up to ~1 minute |
| Business app + Cloud API coexistence | Fixed 20 mps |
| Limit hit | Error 130429 |
| Same recipient too fast | Pair rate limit (131056) |

Tip: send media by uploaded media id rather than external link to maximise throughput.

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 130429 | Cloud API throughput reached | Slow; queue with backoff | Yes |
| 131056 | Pair rate limit (too many to same recipient) | Wait | Later |
| 131048 | Blocked: spam flags / quality | Review quality | No |
| 131049 | Per-user marketing cap | Wait 24 h | Not within 24 h |
| 80007 | WABA rate limit on API calls | Reduce call rate | Yes |
Messaging-limit exhaustion error code (commonly 131026-adjacent / 130472) was not on the fetched page: unverified 2026-10-04.

## Quirks and gotchas
- The limit counts unique recipients, not messages; many messages to one user count once.
- Limits are at portfolio level; one noisy number can exhaust the whole portfolio.
- Service-window (user-initiated) replies do not count against the unique-user business-initiated limit (inferred from the upgrade path wording "outside customer service windows"; unverified for the limit itself).
- Higher tiers do not override per-user marketing caps (see templates/marketing_limits.md).
- Quality rating (GREEN/YELLOW/RED) and display-name approval interact with tier changes.
- Marketing templates are not delivered to US (+1) numbers regardless of tier.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits
- https://developers.facebook.com/documentation/business-messaging/whatsapp/throughput
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes
- https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-limits

Empty or 404: none. The tier literal values beyond `TIER_250`, the exhaustion error code and downgrade rules are unverified.

## Sender-side guard (pseudo-code)
```text
headroom = tier_cap - unique_recipients_last_24h
if headroom <= 0: queue until the oldest recipient ages out of the window
dedupe recipients before counting; one user = one unit regardless of message count
```
Track your own unique-recipient set per portfolio; Meta does not expose the live counter via the fields documented here.

## Upgrade playbook
| Goal | Steps |
|---|---|
| 250 to 2,000 fast | Complete business verification (or partner verification) |
| 250 to 2,000 organically | 2,000 delivered template messages outside service windows to unique users within 30 days, high-quality templates |
| 2,000 and above | Keep quality high on all numbers and templates, use at least 50% of the limit in 7 days; expect the change within 6 hours |
| 80 to 1,000 mps | Reach unlimited tier, message 100K+ unique users in 24 h outside service windows, hold YELLOW or better |

## Monitoring
- Poll `whatsapp_business_manager_messaging_limit` and `quality_rating` per number every few hours; alert on change.
- Alert when 24 h unique recipients exceed 80% of the tier cap.
- Alert on a spike of 131048 (spam/quality) because it precedes downgrades.

## Common mistakes
- Reading the deprecated `messaging_limit_tier`; it may return nothing or stale values.
- Assuming limits are per number; they are per portfolio.
- Counting messages instead of unique recipients.
- Treating 130429 (throughput) as a tier problem; it is a speed problem.
