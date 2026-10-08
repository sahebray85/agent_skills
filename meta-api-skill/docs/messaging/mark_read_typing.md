# Mark as Read and Typing Indicator — Specification

> **When to load**: Marking an inbound message as read (blue ticks) or showing a typing indicator while preparing a reply.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/{version}/{phone-number-id}/messages` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages`) |
| **Auth** | `Authorization: Bearer <token>` (system or business integration system user token) |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Send a read receipt for an inbound `wamid`, optionally with a typing indicator |
| **Idempotency / retry** | Marking the same message read twice is harmless (naturally idempotent). Safe to retry on 5xx or timeout. |

## Request

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `messaging_product` | string | yes | `"whatsapp"` | Fixed |
| `status` | string | yes | `"read"` | Only value |
| `message_id` | string | yes | `wamid` of the inbound message, from the received-message webhook | Must be a message received by this number |
| `typing_indicator` | object | no | `{"type":"text"}` | Shows "typing..." to the user. Requires `status` and `message_id` as well |
| `typing_indicator.type` | string | yes (within object) | `"text"` | Only documented value |

Behaviour of the typing indicator: "The typing indicator will be dismissed once you respond, or after 25 seconds, whichever comes first." Meta advises to "only display a typing indicator if you are going to respond" and to use it when "it will take you a few seconds to respond".

24 h window: receiving a message opens or resets the customer service window; marking read and typing do not extend it. Only a new inbound message from the user resets the 24 h timer. (Window definition from Meta's send-messages page; the statement that read/typing do not extend it is inferred (unverified 2026-10-04).)

## Example request
```bash
# Mark as read only
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","status":"read","message_id":"wamid.HBgM..."}'

# Mark as read and show typing indicator
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","status":"read","message_id":"wamid.HBgM...",
       "typing_indicator":{"type":"text"}}'
```

## Response
```json
{"success": true}
```

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the read receipt (and indicator) was accepted. Exact response shape is not shown on the fetched typing-indicator page; `{"success":true}` is the standard read-receipt response (unverified 2026-10-04) |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid parameter, e.g. unknown or malformed `message_id` (unverified 2026-10-04) | Use the `wamid` from the webhook | After fixing |
| 190 | Access token invalid or expired (unverified 2026-10-04) | Refresh token | After fixing |
| 130429 | Throughput exceeded | Slow down | Yes, backoff |
| 131009 | Parameter value not valid | Check `status` and `typing_indicator.type` | After fixing |

Note: `131056` and `131049` apply to outbound content messages, not to read receipts.

## Quirks and gotchas
- Typing indicator is attached to the read call; there is no stand-alone typing endpoint. Always include `status: "read"` and `message_id`.
- The indicator disappears when you send your reply or after 25 seconds. If your processing takes longer, you cannot extend it (re-sending the call to refresh is not documented, unverified 2026-10-04).
- Do not show the indicator if you will not reply; this gives a poor user experience.
- Read receipts only apply to messages received from users, not to your outbound messages.
- Mark as read is not required for the customer service window; it is a UX signal.
- Marking read does not trigger status webhooks to your system.
- Use a system user or business integration token; a plain user token is not supported for this call.
- Read receipts are visible to the user as blue ticks unless the user disabled read receipts in their own settings (applies to person-to-person, business accounts always show them; unverified 2026-10-04).

### Recommended handling pattern
1. Receive the inbound webhook (`messages[].id` is the `wamid`).
2. De-duplicate on the `wamid` (webhooks can be delivered more than once).
3. If the reply will take more than about a second (LLM call, database lookup, human handover), call mark-read with `typing_indicator`.
4. Send the reply with the normal send endpoint; the indicator clears automatically.
5. If you decide not to reply, do not send the indicator at all. A plain read receipt is enough.

### Sequence and timing
```
user message  -> webhook -> POST status=read + typing_indicator
                         -> (work, under 25 s)
                         -> POST /messages (reply)  => indicator dismissed
```
- If work exceeds 25 seconds the indicator disappears on its own; the reply can still be sent while the window is open.
- For a burst of inbound messages, marking the latest `message_id` is usually enough (client behaviour, unverified 2026-10-04). Marking each one is harmless.

### Request validation checklist
- `messaging_product` is exactly `whatsapp`.
- `status` is exactly `read`.
- `message_id` starts with `wamid.` and was received on this phone number.
- `typing_indicator.type` is `text`.
- Token is a system user or business integration token with access to the WABA.

### Observability
Log the `wamid`, the HTTP status and the `fbtrace_id` of any failure. Do not alert on read-receipt failures; they are cosmetic and must never block message processing.

### Spring Feign sketch
```java
record ReadRequest(@JsonProperty("messaging_product") String messagingProduct,
                   String status,
                   @JsonProperty("message_id") String messageId,
                   @JsonProperty("typing_indicator") @JsonInclude(NON_NULL) TypingIndicator typingIndicator) {
    static ReadRequest read(String wamid, boolean typing) {
        return new ReadRequest("whatsapp", "read", wamid, typing ? new TypingIndicator("text") : null);
    }
}
record TypingIndicator(String type) {}
```
Fire this call asynchronously and swallow failures after logging; the main reply path must not depend on it.

### Test checklist
- Read-only payload omits `typing_indicator` entirely (no `null` field in the JSON).
- Indicator payload shows "typing..." on a test handset and clears on reply.
- Duplicate calls for the same `wamid` do not raise errors in your wrapper.
- Failure of this call never prevents the reply from being sent.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/docs/whatsapp/cloud-api/typing-indicators (typing indicator JSON, 25 second expiry, usage guidance, token requirement)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages (24 h window definition)

Rendered empty:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/typing-indicators

Response body and error codes for this call were not on any fetched page and are marked unverified.
