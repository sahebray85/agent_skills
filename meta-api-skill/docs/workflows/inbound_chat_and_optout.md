# Workflow — Inbound messages, replies and opt-out

> **Scope**: Receiving customer messages, answering inside the 24 h window, and turning STOP into a durable opt-out. Load when the user builds a webhook receiver, a chat ingestion pipeline or consent handling.

---

## 1. Receive

```
Meta ──POST /webhook──► your HTTPS endpoint
   1. read the RAW body bytes
   2. verify X-Hub-Signature-256 = sha256(HMAC-SHA256(raw body, APP_SECRET))   (webhooks/signature_validation.md)
   3. answer 200 immediately; do the work after (queue, outbox)                 (webhooks/setup_verification.md)
   4. iterate entry[].changes[] where field == "messages":
        value.messages[]  → inbound message(s)                                  (webhooks/inbound_messages.md)
        value.statuses[]  → delivery receipts for your sends                    (webhooks/statuses.md)
        value.errors[]    → account-level errors
```

Meta retries on non-200 (Graph docs: decreasing frequency over 36 h; WhatsApp overview: up to 7 days), may batch up to 1000 updates in one POST, and does not guarantee order or uniqueness. **The consumer must be idempotent on `messages[].id` and on `(statuses[].id, status)`.**

---

## 2. The 24 h customer-service window

An inbound message opens a 24 h window for that `wa_id`. Inside it you may send free-form text, media and interactive messages (`messaging/send_text.md`, `send_media.md`, `send_interactive.md`). Outside it only templates go through; a free-form send answers 131047 ("re-engagement message") and must be replaced by a template. Mark messages read and show typing with `messaging/mark_read_typing.md`.

---

## 3. Inbound types you will meet first

| `messages[].type` | Payload | Typical handling |
|---|---|---|
| `text` | `text.body` | chat pipeline; STOP detection |
| `button` | `button.text`, `button.payload` (template quick reply) | opt-out or quick action by payload |
| `interactive` | `interactive.button_reply.id` / `list_reply.id` | menu selection |
| `image`, `document`, `video`, `audio`, `sticker` | `<type>.id`, `mime_type`, `sha256`, `caption` | fetch media URL then download with the token (`media/retrieve_url.md`, `download.md`); URLs are short-lived |
| `location` | `location.latitude/longitude/name/address` | address capture |
| `contacts` | vCard-like array | contact capture |
| `reaction` | `reaction.message_id`, `emoji` | ignore or log |
| `order` | catalog order | commerce |
| `system` | user changed number | update the contact |
| `unsupported` | `errors[]` | log |

`contacts[].profile.name` and `contacts[].wa_id` accompany the first message of a batch. Every message carries `from` (digits, E.164 without `+`), `id` (wamid), `timestamp` (unix seconds as a string).

---

## 4. Opt-out (STOP)

```
inbound text  ──► normalise: trim, case-fold, collapse whitespace
              ──► equals one of {STOP, UNSUBSCRIBE, STOP ALL, CANCEL, END, QUIT}?   (configurable)
                    yes → publish opt-out {channel: WHATSAPP, address: "+" + from, purpose, source: "whatsapp-stop"}
                          and still forward the message to the chat pipeline
                    no  → chat pipeline only ("please stop sending" is a conversation, not a keyword)
template quick-reply button with payload "STOP" → same opt-out
```

- Decide the **purpose** once: marketing-only (order conversations continue) or everything. It is a business decision, not an API one.
- Store consent keyed on `(channel, normalised address, purpose)`; first opt-out wins; a later opt-in is an explicit staff action.
- Confirm the opt-out to the customer only if you are still inside the 24 h window (you are: their STOP just opened it). Use plain text, not a marketing template.
- Meta also offers the customer **block** and **report**; you never see those, only the quality rating.

---

## 5. Receipts (statuses)

`statuses[].id` equals the wamid from your send response. Statuses: `sent`, `delivered`, `read`, `played` (voice), `failed` with `errors[]`. Keep your own rows **forward only**: a late `delivered` after `read` is ignored; `failed` after `sent` is final (131026 = not a WhatsApp user). `timestamp` is unix seconds; convert to ISO-8601 with an offset when handing it to another service. `conversation` and `pricing` appear only on billable events and changed in v24.0+. Details: `webhooks/statuses.md`.

---

## 6. Privacy

Never log `from`, `wa_id`, `text.body`, media URLs, tokens or wamids (a wamid encodes the number). Log message ids from your own queue, outcome, Meta `code` and `fbtrace_id`. `common/logging_privacy.md`.

---

## Sources (verified 2026-10-04)

- Text webhook: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/text
- Status webhook: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/status
- Webhook overview and retries: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview
- Graph webhooks (verification, signature, 36 h retries): https://developers.facebook.com/docs/graph-api/webhooks/getting-started
- Error codes: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes
