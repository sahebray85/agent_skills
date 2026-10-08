# Authentication — Specification

> **When to load**: You are choosing, storing, sending or debugging access tokens, `appsecret_proof`, or permissions for the WhatsApp Cloud API.

## Quick Reference
| Field | Value |
|---|---|
| Header | `Authorization: Bearer <TOKEN>` |
| Base URL | `https://graph.facebook.com/v26.0/` |
| Production token | System user access token (long-lived) |
| Test token | User access token (expires "every few hours") |
| Partner token | Business Integration System User token (Embedded Signup) |
| Permissions | `whatsapp_business_messaging`, `whatsapp_business_management`, `business_management` |
| `appsecret_proof` | `hex(HMAC_SHA256(key=<APP_SECRET>, msg=<TOKEN>))`, query param `appsecret_proof` |
| Webhook signature | Separate mechanism, see `docs/webhooks/signature_validation.md` |

## Token types
| Type | Use | Expiry |
|---|---|---|
| System User (Admin) | Full access to all WABAs and assets; backend services | Long-lived |
| System User (Employee) | Needs per-WABA grants | Long-lived |
| Business Integration System User | Per-customer, Tech Provider / solution partner via Embedded Signup | Long-lived (unverified 2026-10-04) |
| User access token | First test message from the App Dashboard only | Expires within hours |
Tokens are opaque: "Do not parse, decode, or make assumptions about the format of an access token". Use a system user token in production; never a user token.

## Request
```
GET /v26.0/<WABA_ID>/message_templates HTTP/1.1
Host: graph.facebook.com
Authorization: Bearer <TOKEN>
```

## appsecret_proof
Computed as `hash_hmac('sha256', $access_token, $app_secret)` (hex), sent as `appsecret_proof` alongside the token. To require it: App Dashboard > App Settings > Advanced > Security > **Require App Secret**. When on, calls without a valid proof fail, so all calls must come from your backend.
```java
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(new SecretKeySpec(appSecret.getBytes(UTF_8), "HmacSHA256"));
String proof = HexFormat.of().formatHex(mac.doFinal(token.getBytes(UTF_8)));
// GET .../messages?appsecret_proof=<proof>
```
Whether WhatsApp Cloud API enforces it when the toggle is on is unverified 2026-10-04 (Graph-wide behaviour per the secure-requests page).

## Token debugging
`GET /debug_token?input_token=<TOKEN>` with an app token returns validity, scopes and expiry. The WhatsApp access-tokens page does not reference this endpoint (unverified 2026-10-04 for WhatsApp specifics).

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 0 | Authentication failed | Get a new token | No |
| 190 | Token expired/invalid | Replace token | No |
| 10 / 200-299 | Permission missing | Grant permission to system user and WABA asset | No |
| 100 with proof message | `appsecret_proof` wrong or missing | Recompute with current secret and token | No |
| 131005 | Permission denied | Check asset assignment | No |

## Quirks and gotchas
- Assign the WABA asset to the system user in Business Settings; a token with the right scopes but no asset access still fails.
- Token and App Secret belong in a secret store, never in git or logs (see `logging_privacy.md`, `config.md`).
- Rotating the App Secret invalidates webhook signature checks and `appsecret_proof` until config is updated.
- Do not send the token in the query string (appears in access logs).

## Sources (verified 2026-10-04)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/access-tokens
- https://developers.facebook.com/docs/graph-api/guides/secure-requests
- https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages (Bearer header example)
- Not fetched: debug_token page.
