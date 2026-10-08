# Access Tokens — Specification

> **When to load**: You are choosing, generating, validating or rotating the token used in `Authorization: Bearer <TOKEN>` for WhatsApp Cloud and Management APIs.

## Quick Reference
| Field | Value |
|---|---|
| **Header** | `Authorization: Bearer <TOKEN>` (resumable-upload step 2 uses `Authorization: OAuth <TOKEN>`) |
| **Production token** | System User token (long-lived) |
| **Required permissions** | `business_management`, `whatsapp_business_management`, `whatsapp_business_messaging` |
| **Validation endpoint** | `GET /v26.0/debug_token?input_token=<TOKEN>` |
| **Current Graph version** | v26.0 (released 2026-07-29) |
| **Expiry error** | code 190 |

## Token types
| Type | Who | Lifetime | Use |
|---|---|---|---|
| System User access token | Your own business; Admin or Employee system user | Long-lived, suited to automation | Server-to-server production |
| Business Integration System User token | A single onboarded customer; Tech Providers / solution partners via Embedded Signup with Facebook Login for Business | Scoped per customer | Multi-tenant platforms |
| User access token | A developer | Short-lived; regenerate every few hours | Testing from the App Dashboard only |

## Generating a System User token
1. Business Settings > Users > System Users.
2. "+Add" a system user (Admin or Employee).
3. Assign assets with "Manage app" permission (the app and the WABA).
4. "Generate token".
5. Select the app and the token expiration preference.
6. Tick the three permissions above.
7. Store the token in a secret manager. It is shown once.

The business edge `owned_whatsapp_business_accounts` needs an Admin System User token.

## Validating: debug_token
```bash
curl -s -G "https://graph.facebook.com/v26.0/debug_token" \
  --data-urlencode "input_token=<TOKEN>" \
  --data-urlencode "access_token=<APP_ID>|<APP_SECRET>"
```
The caller must hold an app access token (`<APP_ID>|<APP_SECRET>`) or a developer user token tied to the app.

Response `data` fields: `app_id`, `application`, `is_valid`, `expires_at` (unix time; 0 commonly means non-expiring, unverified 2026-10-04), `data_access_expires_at`, `user_id`, `scopes[]`, `granular_scopes[]` (permission plus optional target ids such as WABA ids).
```json
{ "data": { "app_id": "<APP_ID>", "application": "My App", "is_valid": true,
            "expires_at": 0, "data_access_expires_at": 0, "user_id": "<ID>",
            "scopes": ["whatsapp_business_management","whatsapp_business_messaging","business_management"],
            "granular_scopes": [ { "scope": "whatsapp_business_management", "target_ids": ["<WABA_ID>"] } ] } }
```

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 190 | Token expired or invalid | Mint/rotate token | After refresh |
| 0 | Unable to authenticate the app user | Obtain fresh token | After refresh |
| 200 | No token provided, or permission missing | Include token / add scope | No |
| 3 | Capability or permission issue | Run debug_token, check scopes | No |
| 10 | Permission not granted or removed | Verify via debugger | No |
| 4 / 80007 | App / WABA rate limit | Reduce frequency | Yes |
| 368 | Account restricted or disabled (policy) | Review policy enforcement | No |
(463/467 session codes were not on any fetched page: unverified 2026-10-04.)

## Rotation and handling practice
- Expiry preference at generation: choose "never" only if your secret store and rotation policy cover compromise; otherwise use 60 days and automate rotation (preference options as shown in the Business Settings UI; exact choices unverified 2026-10-04).
- Keep two valid tokens during rotation: generate new, deploy, verify with debug_token, then revoke old in Business Settings.
- Treat 190 as non-retryable until a new token is loaded; alert, do not loop.
- Never put the token in query strings or logs; use the header. Redact in logs and error reports.
- Revocation procedures were not documented on the fetched page; use Business Settings > System Users > revoke (unverified 2026-10-04).

## Quirks and gotchas
- A system user must be assigned both the app and the WABA assets, otherwise calls fail with 200/403 even though the token is valid.
- Tokens are tied to an app; calling `/<APP_ID>/uploads` uses the same app's token.
- Version in the path (`/v26.0/`) is independent of the token; v21.0 stops being served on 2027-01-21. Newest versions: v22.0 to 2027-05-20, v23.0 to 2027-10-08, v24.0 to 2028-02-18, v25.0 to 2028-07-29, v26.0 no end date yet.
- Test (user) tokens work for the sandbox number only in practice; do not ship them.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/access-tokens
- https://developers.facebook.com/docs/graph-api/reference/debug_token
- https://developers.facebook.com/docs/graph-api/changelog
- https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes
- https://developers.facebook.com/docs/graph-api/reference/business/owned_whatsapp_business_accounts/

404: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/debugging. Empty (wrong topic): https://developers.facebook.com/docs/graph-api/guides/debugging.

## Header cheat sheet
```text
Graph/Management/Cloud API calls     Authorization: Bearer <TOKEN>
Resumable upload step 2 (/upload:ID) Authorization: OAuth <TOKEN>
debug_token                          input_token=<TOKEN>  + app token or developer token
```

## Startup self-check
Run once at service start and daily thereafter:
```bash
curl -s -G "https://graph.facebook.com/v26.0/debug_token" \
  --data-urlencode "input_token=<TOKEN>" \
  --data-urlencode "access_token=<APP_ID>|<APP_SECRET>"
```
Fail health checks when any of these hold:
1. `data.is_valid` is false.
2. A required scope (`whatsapp_business_messaging`, `whatsapp_business_management`, `business_management`) is missing from `scopes`.
3. `granular_scopes` target ids do not include your `<WABA_ID>`.
4. `expires_at` is non-zero and less than 7 days away.

## Secret storage guidance
- Store in a secret manager, inject by environment variable, never commit.
- Separate tokens per environment (sandbox, staging, production).
- Scope the system user to only the WABAs it must serve.
- For multi-tenant setups use one Business Integration System User token per customer and store it encrypted with a per-tenant key.
- Log only a token fingerprint (last 4 characters), never the token.

## Failure handling
| Symptom | Likely cause | Fix |
|---|---|---|
| 190 on every call | Expired or revoked token | Rotate token |
| 200 on specific WABA | System user lacks the asset | Assign asset with Manage app |
| 3 or 10 | Permission removed | Re-grant scopes and regenerate |
| 368 | Account restricted | Policy enforcement review, not a token problem |

## Permission-to-API map
| API area | Permission |
|---|---|
| Send messages, media | `whatsapp_business_messaging` |
| Templates, phone numbers, profile, analytics, subscribed_apps | `whatsapp_business_management` |
| Business edges such as `owned_whatsapp_business_accounts` | `business_management` |
