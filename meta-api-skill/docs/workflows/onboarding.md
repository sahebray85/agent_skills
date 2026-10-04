# Workflow — Onboarding a business number (HITL + API)

> **Scope**: The one-time setup from nothing to a number that can send an approved template and receive webhooks. Load when the user is setting up WhatsApp for the first time or debugging "why can't I send".

---

## 1. Human steps (Meta Business Suite / App Dashboard)

| # | Step | Where | Outcome |
|---|---|---|---|
| 1 | Create or pick a Business Portfolio and complete **business verification** (legal docs, website or social proof) | business.facebook.com → Settings → Security Centre | Unlocks the 1k tier and the display name |
| 2 | Create a Meta **App** (type Business), add the **WhatsApp** product | developers.facebook.com | App ID, App Secret |
| 3 | Create or attach a **WABA**; add a **phone number** (a number not currently on consumer WhatsApp, or opt into coexistence with the Business app) | App Dashboard → WhatsApp → API Setup | `<WABA_ID>`, `<PHONE_NUMBER_ID>` |
| 4 | Create a **System User** (admin), assign the app and the WABA as assets, **generate a token** with `whatsapp_business_messaging` + `whatsapp_business_management` (and `business_management` if listing WABAs) | Business Settings → Users → System Users | Permanent token → secrets manager |
| 5 | Set a **payment method** on the WABA; for India choose **INR** (mandatory by 2026-12-31) | Business Settings → Billing | Sends beyond the free tier work |
| 6 | Configure the **webhook**: callback URL, verify token, subscribe fields (`messages` at minimum) | App Dashboard → WhatsApp → Configuration | Meta calls `GET` once to verify |
| 7 | Submit the **display name** and, optionally, apply for the Official Business Account tick | Business Settings → WhatsApp Accounts | Name shows on the customer's phone |

---

## 2. API steps (in order)

```bash
# 1. Check the token
curl -s "https://graph.facebook.com/v26.0/debug_token?input_token=<TOKEN>" -H "Authorization: Bearer <TOKEN>"

# 2. Find the phone number id and its state
curl -s "https://graph.facebook.com/v26.0/<WABA_ID>/phone_numbers?fields=id,display_phone_number,verified_name,quality_rating,messaging_limit_tier,code_verification_status" \
  -H "Authorization: Bearer <TOKEN>"

# 3. Register the number with a two-step PIN (once)
curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/register" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","pin":"123456"}'

# 4. Subscribe the app to the WABA (webhooks do not fire without this)
curl -s -X POST "https://graph.facebook.com/v26.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer <TOKEN>"

# 5. Create a template (or do it in Business Manager) and wait for APPROVED
#    see templates/create_template.md

# 6. Send to your own number with the test template
curl -s -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"template","template":{"name":"hello_world","language":{"code":"en_US"}}}'
```

Details for each call: `account/access_tokens.md`, `account/phone_numbers.md`, `account/waba.md`, `templates/create_template.md`, `messaging/send_template.md`.

---

## 3. First-send checklist

- [ ] `debug_token` shows the two WhatsApp scopes and `is_valid: true`
- [ ] `code_verification_status` is `VERIFIED` and the number is registered (a send answers 200, not 133010 "not registered")
- [ ] `subscribed_apps` lists your app; the App Dashboard "Test" button reaches your endpoint and the signature validates
- [ ] A template is `APPROVED` in the language you will send
- [ ] Billing is set up; in India the WABA currency is INR
- [ ] The recipient has opted in (policy) and, for marketing, is not a US (+1) number
- [ ] `ENGAGEMENT_WHATSAPP_API_VERSION`-style config pins `v26.0`; nothing hardcodes the host
- [ ] A test number (Meta's sandbox number from API Setup) was used before the real one

---

## 4. Common first-day failures

| Symptom | Cause | Doc |
|---|---|---|
| 190 on every call | Temporary 24 h token expired, or token lacks the WhatsApp scopes | `common/auth.md` |
| 131005 | System User not assigned the WABA asset | `account/access_tokens.md` |
| 133010 / "phone number not registered" | Step 3 skipped | `account/phone_numbers.md` |
| 132001 | Template name or language not approved for this WABA | `templates/lifecycle_quality.md` |
| 131026 | Recipient is not a WhatsApp user, or marketing to a US number | `common/errors.md` |
| Webhook never fires | App not subscribed to the WABA, or the GET verification failed | `webhooks/setup_verification.md` |
| 200 on send, no delivery | Check `statuses[]` webhooks: `failed` with `errors[]` arrives asynchronously | `webhooks/statuses.md` |

---

## Sources

- Onboarding flow: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started (page family moved in 2026; verify the exact URL when needed)
- Verified today: `debug_token`, `register`, `subscribed_apps` paths as used in the account docs of this skill (see their Sources sections).
