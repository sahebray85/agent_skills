# Pricing and INR Billing — Specification

> **When to load**: You need to understand per-message pricing, free windows, volume tiers, rate-card cadence, billing currency, or the India INR migration deadlines.

## Quick Reference
| Field | Value |
|---|---|
| **Model** | Per delivered template message (since 2025-07-01); conversation-based pricing retired |
| **Categories** | Marketing, Utility, Authentication, Service |
| **Free** | Service messages; utility/authentication inside an open service window; everything inside a 72 h free-entry-point window |
| **Rate card update cadence** | Only on the 1st day of each quarter: Jan 1, Apr 1, Jul 1, Oct 1 |
| **Billing reads** | analytics `pricing_analytics`, `conversation_analytics` (see analytics.md) |
| **India** | INR billing localisation launched 2026-01-01; all WABAs INR by 2026-12-31 |

## Charging rules
| Category | Charged? |
|---|---|
| Marketing | Always, every delivered message |
| Utility | Charged outside the customer service window; free inside |
| Authentication | Charged outside the window; free inside |
| Service | Free (since 2024-11-01) |

Windows:
- Customer Service Window (CSW): opens when a user messages you; open 24 h after their last message. Non-template messages and utility templates are free in it.
- Free Entry Point (FEP) window: opens when the user arrives through Click-to-WhatsApp ads or a Page CTA button; for 72 hours any message type is free.
- Charges apply only when a template message is delivered (failed sends are not billed).

## Volume tiers
- Utility and authentication get lower rates at higher monthly volume, computed at business-portfolio level.
- Tiers are market-and-category specific and reset monthly at 12:00 am in the WABA timezone.
- Only charged messages count toward tiers.
- Analytics dimension `TIER` exposes the tier in `pricing_analytics`.

## Rate cards and notice periods
- Meta may change prices only on the first day of a quarter.
- Minimum notice: 1 month for rate updates, 3 months for pricing add-ons, 6 months for model changes.
- Actual per-message INR amounts live in the downloadable rate card; the fetched page does not enumerate them. Do not hard-code rates; INR rates unverified 2026-10-04. Read the current rate card from Meta's pricing page or WhatsApp Manager and store with an effective-from date.

## India and INR
| Date | Event |
|---|---|
| 2026-01-01 | Billing localisation for eligible Indian customers launched |
| 2026-06-01 | Currency Migration APIs available (from brief; endpoints not on the fetched page: unverified 2026-10-04) |
| 2026-12-31 | Deadline: all WABAs in the eligible business portfolio must be on INR |
| 2027-01-01 | Meta stops delivering messages for non-INR WABAs of eligible customers |

Action items for an Indian business:
1. List WABAs (`owned_whatsapp_business_accounts`) and check each WABA's currency (field availability unverified; use WhatsApp Manager if the API rejects `currency`).
2. Migrate every WABA, not just the busiest one: a single non-INR WABA stops delivering after the cutoff.
3. Update cost reporting to INR; `pricing_analytics` cost values follow the WABA currency.
4. Re-check credit line currency (error 131042 appears on payment problems).

Supported billing currencies: USD, AED, ARS, AUD, BRL, CLP, COP, EUR, GBP, IDR, INR, MXN, MYR, PEN, SAR, SGD.

## US restriction
Marketing templates are not delivered to US (+1) numbers (paused since 2025-04-01 per brief); you are not billed for undelivered messages.

## Example: reading cost
```bash
curl -s -G "https://graph.facebook.com/v26.0/<WABA_ID>" \
  -H "Authorization: Bearer <TOKEN>" \
  --data-urlencode "fields=pricing_analytics.start(1759276800).end(1761955200).granularity(DAILY).metric_types(COST,VOLUME).dimensions(PRICING_CATEGORY,PRICING_TYPE)"
```
Analytics data is approximate and can differ slightly from invoices.

## Errors related to billing
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131042 | Payment method / credit line problem | Fix billing setup | After fix |
| 131049 | Marketing not delivered (engagement cap) | Not billed; wait 24 h | Later |
| 131055 / 134100 | Marketing Messages API wrong template category | Use marketing template | No |

## Quirks and gotchas
- Per-conversation pricing language in older docs and SDKs is obsolete; model cost per message and category.
- `MARKETING_LITE` and `AUTHENTICATION_INTERNATIONAL` appear as pricing categories in analytics (see analytics.md).
- Solution Partner credit lines hide COST metrics for WABAs sharing the partner's line.
- Pricing tiers reset in the WABA timezone, not UTC; align your cost reports.
- Do not assume a template's category on the sender side: Meta may recategorise (billing follows the final category).

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing
- https://developers.facebook.com/documentation/business-messaging/whatsapp/analytics
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes
- https://developers.facebook.com/docs/whatsapp/message-templates/guidelines

Empty render: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/pricing-updates-on-whatsapp-business-platform. Unverified: INR per-message rates, Currency Migration API endpoints and 2026-06-01 date, the US pause start date.

## Cost estimation model
```text
cost = sum over delivered template messages of rate(country, category, tier)
       where charged = category == MARKETING
                    or (category in {UTILITY, AUTHENTICATION} and no open service window)
       and   not inside a free entry point window
```
Keep `rate` in a table keyed by (market, category, tier, effective_from) loaded from the current rate card, and pick the row effective on the send date.

## Budget guardrails
1. Alert when daily marketing cost exceeds a threshold derived from the previous 7 days.
2. Pace campaigns so a bad audience cannot burn the whole budget (see templates/marketing_limits.md).
3. Prefer utility templates sent inside a service window for transactional updates (free).
4. Review volume tiers monthly; utility and authentication unit prices drop with volume and reset at month start.

## Checklist before 2026-12-31 (India)
- [ ] Inventory all WABAs under every portfolio.
- [ ] Confirm which are non-INR.
- [ ] Schedule the migration for each, outside peak campaign hours.
- [ ] Verify sends and billing after each migration.
- [ ] Update dashboards and finance exports to INR.

## FAQ
- Is a utility template free? Only inside an open customer service window; outside it is charged.
- Is a service (non-template) reply free? Yes, service messages are free.
- When can prices change? Only on Jan 1, Apr 1, Jul 1 or Oct 1, with at least one month notice.
- What happens to a non-INR WABA on 2027-01-01? Meta stops delivering its messages (eligible Indian customers).
- Where do I see actual spend? `pricing_analytics` with `COST`, noting it is approximate versus invoices.

## Quick triage
```text
Unexpected charge?     -> check category (Meta may recategorise) and window state
Messages not arriving? -> check WABA currency against the INR deadline, then 131042
Cost report mismatch?  -> compare timezone (WABA vs UTC) and expect small variance
```
