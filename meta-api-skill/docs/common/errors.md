# Error Codes and Classification — Specification

> **When to load**: A Graph/WhatsApp call or a status webhook returned an error code and you must decide AUTH/ACCOUNT/TEMPLATE/QUOTA/REJECTED/DEFERRED/RETRY handling.

## Quick Reference
| Field | Value |
|---|---|
| Error body | `{"error":{"message","type","code","error_subcode","error_data":{"messaging_product","details"},"fbtrace_id"}}` |
| Webhook error | `statuses[].errors[]{code,title,message,error_data.details,href}` |
| Buckets | AUTH, ACCOUNT, TEMPLATE, QUOTA, REJECTED, DEFERRED, RETRY |
| Special deferral | 131049 -> DEFERRED 24 h; 131056 -> DEFERRED 1 h |
| HTTP status | Only listed where the Meta page shows one; "-" means not shown (do not assume) |
| Meta page | .../whatsapp/support/error-codes |

## Error body anatomy
| Field | Meaning |
|---|---|
| `message` | Human text; do not parse |
| `type` | e.g. `OAuthException`; coarse |
| `code` | Primary integer; key all policy off this |
| `error_subcode` | Optional finer code (Graph-level) |
| `error_data.details` | WhatsApp-specific detail string (the most informative text) |
| `fbtrace_id` | Support trace id; log it and quote it to Meta support. Not secret but not useful to end users |
```json
{ "error": { "message": "(#131030) Recipient phone number not in allowed list", "type": "OAuthException", "code": 131030,
  "error_data": { "messaging_product": "whatsapp", "details": "<details>" }, "fbtrace_id": "<TRACE_ID>" } }
```
(Example shape; 131030 does not appear on the fetched error-codes page, unverified 2026-10-04.)

## Sync vs async errors
- **Sync**: returned in the HTTP response of the API call (4xx/5xx with the error body). Nothing was sent. Cases: bad token, invalid parameter, template not found, rate limits.
- **Async**: the call returned 200 with a wamid, then a `statuses[]` webhook with `status: failed` and `errors[]` arrives (131026, 131049, 131047 and similar delivery-time failures). Persist the wamid so the failure can be correlated.
- Throughput and system errors may also arrive as `value.errors[]` webhooks (example 130429).
- Never mark a message "delivered" from the sync 200 alone.

## Bucket policy
| Bucket | Handling |
|---|---|
| AUTH | Stop; rotate/fix token or permission; alert ops. No blind retry |
| ACCOUNT | Business/WABA/number state problem; pause channel, alert, human fix |
| TEMPLATE | Template/parameter problem; fix and resubmit; do not retry unchanged |
| QUOTA | Throughput/limit; back off with jitter, then retry |
| REJECTED | Permanent for this recipient/content; mark failed, no retry |
| DEFERRED | Do not retry now; reschedule after the stated delay |
| RETRY | Transient; retry with exponential backoff and a cap |

## Full table
Meta page has no stated retryability; the Retry/Bucket columns are this skill's classification. "Action" quotes Meta only where in quotation marks; otherwise it is a paraphrase from the page title/solution (unverified 2026-10-04 for wording).

| Code | Title | HTTP | Meaning | Action | Retryable | Bucket |
|---|---|---|---|---|---|---|
| 0 | Authentication Failed | - | Token invalid for this request | "Get a new access token" | no | AUTH |
| 1 | Invalid Request | - | Unknown/unsupported request or API call | Check endpoint, params, version | no | REJECTED |
| 2 | Temporary Unavailable | - | Temporary Graph downtime | Retry later | yes | RETRY |
| 3 | Capability / Permissions | - | App lacks a capability or permission | Check app permissions and capability | no | AUTH |
| 4 | Rate Limit Exceeded | - | Platform call limit hit | Back off, see `rate_limits.md` | after delay | QUOTA |
| 10 | Permission Not Granted | - | Permission denied/not granted | Request/grant permission | no | AUTH |
| 33 | Phone Number Deleted | - | Number/object no longer exists | Verify number id | no | ACCOUNT |
| 100 | Invalid Parameter | 400 | Missing/invalid parameter | Fix request | no | REJECTED |
| 130403 | User Blocked | - | Recipient blocked the business (new code vs brief) | Stop messaging this user | no | REJECTED |
| 130429 | Throughput Limit | - | Too many messages from the number in short time | Slow down sends | after delay | QUOTA |
| 130472 | Experiment Block | - | Number is in a Meta experiment; message not delivered | Do not retry | no | REJECTED |
| 130497 | (not on page) | - | Reported as business restricted from messaging users in this country | - | no | ACCOUNT |
| 131000 | Unknown | - | Something went wrong | Retry; contact support with fbtrace_id if persistent | yes (limited) | RETRY |
| 131005 | Permission Denied | - | Missing permission for the action | Check token permissions | no | AUTH |
| 131008 | Missing Parameter | - | Required parameter missing | Fix request | no | REJECTED |
| 131009 | Invalid Parameter Value | 400 | Parameter value invalid | Fix request | no | REJECTED |
| 131016 | Service Unavailable | - | Service temporarily unavailable | Retry later | yes | RETRY |
| 131021 | Same Phone Number | - | Sender and recipient are the same number | Use a different recipient | no | REJECTED |
| 131026 | Delivery Failed | - | Message undeliverable (not on WhatsApp, old app version, etc.) | Verify recipient; do not loop | no | REJECTED |
| 131030 | (not on page) | - | Recipient not in allowed list (test-mode) | Add recipient or go live | no | REJECTED |
| 131031 | (not on page) | - | Reported as account locked | - | no | ACCOUNT |
| 131037 | No Display Name | - | Display name not approved | Complete display name approval | no | ACCOUNT |
| 131042 | Payment Error | - | Billing/payment method problem | Fix payment setup | no | ACCOUNT |
| 131045 | Registration Error | - | Number not registered/incorrect certificate | Register number | no | ACCOUNT |
| 131047 | 24-Hour Limit | - | Outside customer service window | "Send the recipient a template message instead" | template only | REJECTED |
| 131048 | Quality / Spam Block | - | Blocked by spam rate limit | Improve quality, wait | after delay | QUOTA |
| 131049 | Marketing Limit | - | Meta withheld marketing message for ecosystem health | Wait 24+ h before trying again | after 24 h | DEFERRED (24 h) |
| 131051 | Unsupported Type | - | Message type unsupported | Use supported type | no | REJECTED |
| 131052 | Media Download Failed | - | Could not download inbound media | Re-query media id, retry | yes | RETRY |
| 131053 | Media Upload Failed | 400 | Media upload failed (type/size/corrupt) | Check file format and size | no | REJECTED |
| 131055 | Method Not Allowed | 400 | Wrong method (Marketing Messages API) | Use correct endpoint | no | REJECTED |
| 131056 | Recipient Throttle | - | Pair rate limit: too many messages to one user | Wait, retry later | after 1 h | DEFERRED (1 h) |
| 131057 | Maintenance Mode | - | Account in maintenance | Retry later | yes | RETRY |
| 131050 | User Opted Out | - | Recipient opted out of marketing | Stop marketing to user | no | REJECTED |
| 131063 | Marketing Disabled | - | Marketing messages disabled | Check account setting | no | ACCOUNT |
| 131064 | (not on page) | - | Unknown to this run | - | - | unverified |
| 132000 | Parameter Count Mismatch | - | Template params count differs | Match template | no | TEMPLATE |
| 132001 | Template Not Found / Approved | - | Name+language missing or not approved | Check name, language, status | no | TEMPLATE |
| 132005 | Translation Too Long | - | Hydrated text too long | Shorten params | no | TEMPLATE |
| 132007 | Policy Violation | - | Content violates WhatsApp policy | Revise template | no | TEMPLATE |
| 132012 | Parameter Format Error | - | Param format mismatch | Fix param type/format | no | TEMPLATE |
| 132015 | Low Quality Paused | - | Template paused for low quality | Edit/replace template | no | TEMPLATE |
| 132016 | Permanently Disabled | - | Template permanently disabled | Create new template | no | TEMPLATE |
| 132018 | Template Validation Error | 400 | Template content validation failed | Fix template | no | TEMPLATE |
| 132068 | Flow Blocked | - | Flow is blocked | Fix/publish flow | no | TEMPLATE |
| 132069 | Flow Throttled | - | Flow throttled | Wait | after delay | QUOTA |
| 133000 | Deregistration Failed | - | Could not deregister number | Retry | yes | RETRY |
| 133004 | Server Unavailable | - | Server temporarily unavailable | Retry later | yes | RETRY |
| 133005 | Invalid PIN | - | Two-step PIN incorrect | Correct PIN | no | ACCOUNT |
| 133006 | Phone Not Verified | - | Number not verified | Verify number | no | ACCOUNT |
| 133008 | Too Many PIN Guesses | - | PIN attempts exceeded | Wait before retry | after delay | ACCOUNT |
| 133009 | PIN Too Quick | - | PIN entered too fast | Wait and retry | after delay | ACCOUNT |
| 133010 | Not Registered | - | Number not registered | Register number | no | ACCOUNT |
| 133015 | Deletion Incomplete | - | Previous deletion still processing | Wait 5 minutes | after 5 min | RETRY |
| 133016 | Registration Attempt Limit | - | Too many registration attempts | Wait | after delay | ACCOUNT |
| 134011 | Payments TOS Pending | - | Payments terms not accepted | Accept terms | no | ACCOUNT |
| 134100 | Non-Marketing Template | 400 | Marketing Messages API needs marketing template | Use marketing template | no | TEMPLATE |
| 134101 | Template Syncing | 400 | Template still syncing | Wait 10 minutes | after 10 min | RETRY |
| 134102 | Template Unavailable | 500 | Template unavailable | Retry later | yes | RETRY |
| 135000 | Unknown Parameter Error | - | Unknown param | Fix request | no | REJECTED |
| 190 | Token Expired | - | Access token expired/invalid | Refresh/replace token (system user) | no | AUTH |
| 200 | Permission error | - | Generic permission failure | Check permissions | no | AUTH |
| 200-299 | API Permission | - | Specific missing permission range | Grant missing permission | no | AUTH |
| 200005-200007 | Template insights errors | - | Template analytics request errors | Fix request | no | REJECTED |
| 368 | Account Restricted | - | Temporarily blocked for policy violations | Wait / review policy | no | ACCOUNT |
| 80007 | WABA Rate Limit | - | WABA rate limit on the error page | Back off; see conflict below | after delay | QUOTA |
| 80008 | (rate-limit page) | - | Rate-limit page names 80008 for WhatsApp Business Management API | Back off | after delay | QUOTA |
| 1752041 | (see page) | - | Present on page; meaning not captured | Consult Meta page | - | unverified |
| 2388012, 2388019, 2388039, 2388040, 2388047, 2388072, 2388073, 2388091, 2388093, 2388103, 2388293, 2388299 | 2388xxx family | - | Template create/edit errors; 2388019 = 250 template limit reached | Fix template / delete unused templates | no | TEMPLATE |
| 2494055, 2494100 | (see page) | - | Present on page; meaning not captured | Consult Meta page | - | unverified |
| 2593107, 2593108 | (see page) | - | Present on page; meaning not captured | Consult Meta page | - | unverified |

## Discrepancies to remember
- **80007 vs 80008**: the error-codes page says 80007 "WABA Rate Limit"; the rate-limiting page lists 80008 for the Business Management API. Treat both as QUOTA.
- Codes 130497, 131030, 131031, 131064, 131060 were not on the fetched error-codes page (unverified 2026-10-04); meanings shown above for 130497/131030/131031 come from prior knowledge, not the page.
- HTTP statuses are only those the page shows (100, 131009, 131053, 132018, 131055, 134100, 134101 = 400; 134102 = 500). Rely on `error.code`, not HTTP status.
- 2388xxx individual meanings other than 2388019 were not captured by the summariser (unverified 2026-10-04).
- Meta's "recommended action" is quoted verbatim only for 0, 131047, 131049; the rest are paraphrases.

## Retry guidance
- RETRY: exponential backoff (e.g. 1 s, 2 s, 4 s ... cap 60 s, max ~5 attempts) with jitter. Reuse nothing that creates duplicates: sends are not idempotent, so after an ambiguous timeout look for a status webhook before resending.
- QUOTA: slow the producer, not only the single call.
- DEFERRED: persist `retry_after`, re-queue; for 131049 consider the same user is blocked for marketing for 24 h and also stop other marketing to them.
- Never retry AUTH/ACCOUNT/TEMPLATE/REJECTED unchanged.

## Quirks and gotchas
- Same code can appear sync (HTTP error) and async (status webhook); handle both through one classifier.
- `message` text contains `(#code)`; do not parse.
- Marketing Messages API codes 134100-134102 and 131055 do not apply to the normal send endpoint.
- Log `fbtrace_id`, `code`, `error_data.details`; never log full request bodies (PII).

## Sources (verified 2026-10-04)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes (fetched in prior run via summariser; re-verify before relying on single rows)
- Rate-limiting page (80008, caller-verified)
- Webhook errors page: .../webhooks/reference/messages/errors (130429 example)
