# Rate Limits and Throughput — Specification

> **When to load**: You are sizing send rates, handling 4/80007/80008/130429/131048/131056 errors, or reading usage headers.

## Quick Reference
| Limit | Value |
|---|---|
| Platform (Graph) limit | 200 x number of users, per rolling hour (rate-limiting page) |
| Usage header | `X-Business-Use-Case-Usage` |
| Header fields | `call_count`, `total_cputime`, `total_time`, `estimated_time_to_regain_access` (minutes) |
| Messaging tiers (unique users / 24 h) | 250, 2,000, 10,000, 100,000, unlimited |
| Tier webhook values | `TIER_50`, `TIER_250`, `TIER_2K`, `TIER_10K`, `TIER_100K`, `TIER_NOT_SET`, `TIER_UNLIMITED` |
| Throughput | Default 80 mps; upgrade to 1000 mps under conditions (throughput page text did not state numbers; unverified 2026-10-04) |
| Pair rate limit | Per business-recipient pair, error 131056 |
| Per-user marketing cap | Error 131049, see `docs/templates/marketing_limits.md` |

## Layers
| Layer | Error | Handling |
|---|---|---|
| Graph platform call count | 4 (also 17, 80001 per rate-limit page) | Back off until `estimated_time_to_regain_access` |
| WABA / Business Management API | 80007 (error page, "WABA Rate Limit") and 80008 (rate-limit page) | Back off; both documented, treat equal |
| Phone number throughput | 130429 | Slow producer; token-bucket per `<PHONE_NUMBER_ID>` |
| Spam/quality | 131048 | Improve content/targeting; wait |
| Pair limit | 131056 | Defer that recipient 1 h |
| Marketing per user | 131049 | Defer 24 h |
| Messaging tier (daily unique users) | tier exhaustion, error code unverified 2026-10-04 | Spread campaign over days |

## Header example
```
X-Business-Use-Case-Usage: {"<BUSINESS_ID>":[{"type":"whatsapp_business_management","call_count":28,"total_cputime":15,"total_time":25,"estimated_time_to_regain_access":0}]}
```
(Structure illustrative; field names verified, wrapping keys unverified 2026-10-04.)

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 4 | Rate limit exceeded | Back off | After delay |
| 80007 / 80008 | WABA rate limit | Back off | After delay |
| 130429 | Throughput limit | Token bucket, jitter | After delay |
| 131048 | Spam rate limit | Review quality | After delay |
| 131056 | Pair rate | Defer 1 h | DEFERRED |
| 131049 | Marketing limit | Defer 24 h | DEFERRED |

## Quirks and gotchas
- Throttle at the producer: a per-number token bucket sized below your mps; do not rely on retries.
- Tier counts unique recipients in 24 h, not messages. Tier upgrades arrive as `phone_number_quality_update` (`THROUGHPUT_UPGRADE`).
- Retried sends can double-send; check statuses before replaying after a timeout.
- Read `estimated_time_to_regain_access` instead of fixed sleeps.
- Template creation has its own cap (250 templates, code 2388019).

## Sources (verified 2026-10-04)
- Rate-limiting page (caller-verified: 200 x users per hour, BUC header, 80008, 4/17/80001)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/throughput (rendered only a heading summary; numbers unverified)
- Error codes page; phone_number_quality_update webhook page; messaging tiers (caller-verified).
