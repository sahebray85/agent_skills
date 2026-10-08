# Send Media Message — Specification

> **When to load**: Sending an image, document, video, audio or sticker message by uploaded media id or public link, and checking MIME types and size limits.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/{version}/{phone-number-id}/messages` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Deliver a media file to a user within the 24 h window (outside it, use a template with a media header) |
| **Idempotency / retry** | None; retrying can duplicate. Media ids are reusable across many sends until they expire (30 days). |

## Request

Envelope: `messaging_product` = `"whatsapp"`, `recipient_type` (`individual`|`group`, optional), `to`, `type` = `image` | `document` | `video` | `audio` | `sticker`, optional `context.message_id`, `biz_opaque_callback_data`.

Each media object takes either `id` or `link`:

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `<type>.id` | string | one of id/link | Media id from `POST /{phone-number-id}/media` | Recommended. API-issued ids live 30 days; webhook-issued ids 7 days |
| `<type>.link` | string | one of id/link | Public HTTPS URL of the asset | Not recommended; Cloud API caches the asset 10 minutes and reuses it when the link string is identical. Meta must be able to fetch it without auth |
| `image.caption`, `video.caption`, `document.caption` | string | no | Caption text | Not supported for `audio` and `sticker`. Max length not stated in the fetched pages (unverified 2026-10-04; 1024 is the commonly cited value) |
| `document.filename` | string | no | File name shown to the user | Documents only |

### MIME and size limits

```
Type      Formats (MIME)                                                   Max size
image     image/jpeg, image/png (8-bit, RGB or RGBA)                       5 MB
video     video/mp4, video/3gpp (H.264 video, AAC audio)                   16 MB
audio     audio/aac, audio/amr, audio/mpeg, audio/mp4, audio/ogg (opus)    16 MB
document  text/plain, application/pdf, .doc/.docx, .xls/.xlsx, .ppt/.pptx  100 MB
sticker   image/webp static                                                100 KB
sticker   image/webp animated                                              500 KB
```

Audio list per Meta: AAC, AMR, MP3, M4A, OGG. Documents: TXT, XLS, XLSX, DOC, DOCX, PPT, PPTX, PDF. Exact MIME strings for office formats and audio (for the upload `type` field) are standard values; Meta's fetched page lists format names, so the MIME strings are partly (unverified 2026-10-04). Ogg audio must use the opus codec for voice notes (unverified 2026-10-04).

## Example request
```bash
# 1. Upload (see docs/media/upload.md), keep the returned id
# 2. Send image by id with caption
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","recipient_type":"individual","to":"919999999999",
       "type":"image","image":{"id":"<MEDIA_ID>","caption":"Your order"}}'

# Document by link with filename
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"919999999999","type":"document",
       "document":{"link":"https://example.com/invoice.pdf","filename":"invoice-SB-1001.pdf","caption":"Invoice"}}'

# Video, audio, sticker
#   "type":"video","video":{"id":"<MEDIA_ID>","caption":"..."}
#   "type":"audio","audio":{"id":"<MEDIA_ID>"}
#   "type":"sticker","sticker":{"id":"<MEDIA_ID>"}
```

## Response
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{"input": "919999999999", "wa_id": "919999999999"}],
  "messages": [{"id": "wamid.HBgM..."}]
}
```

| Field | Type | Description |
|---|---|---|
| `contacts[].wa_id` | string | Canonical recipient id |
| `messages[].id` | string | `wamid`; delivery status arrives via webhook |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131053 | Media upload error (link unreachable, wrong type, too large, bad codec) | Verify MIME, size, link reachability, or upload and use an id | After fixing |
| 131047 | Outside 24 h window | Use a template with media header | No |
| 131026 | Recipient not on WhatsApp | Mark undeliverable | No |
| 131056 | Pair rate limit | Back off | Yes |
| 130429 | Throughput exceeded | Slow down | Yes, backoff |
| 131052 | Media download error on the recipient side (unverified 2026-10-04) | Re-send later | Maybe |
| 100 | Invalid parameter, e.g. unknown media id (unverified 2026-10-04) | Re-upload and use the new id | After fixing |

## Quirks and gotchas
- Prefer `id` over `link`: ids avoid public hosting, remove fetch failures, and can be reused for many recipients (upload once, send many).
- Link caching: the Cloud API reuses a cached copy for 10 minutes if the link string is identical. Change the URL (for example `?v=<random>`) to force a refetch.
- Media ids expire: 30 days for ids from the upload API, 7 days for inbound webhook ids. A send with an expired id fails; re-upload.
- Image PNG must be 8-bit RGB or RGBA; 16-bit or palette PNGs are rejected. Images are recompressed by WhatsApp.
- Video must be H.264 with AAC audio in MP4 or 3GP; other codecs fail even if the extension is `.mp4`.
- `audio` and `sticker` have no caption.
- Stickers: WebP only, 100 KB static, 500 KB animated.
- Declared file MIME at upload must match actual bytes.
- Media messages outside the 24 h window are only possible as template headers (`send_template.md`).

### Choosing id versus link
```
Situation                                   Use
Same asset to many users                    id (upload once)
Asset already on a public CDN               link (accept the 10 minute cache)
Asset is private or time-limited            id
Template header sample at creation time     resumable upload handle (not an id)
```

### Pre-send validation checklist
- Check file size against the type limit before calling the API.
- Sniff MIME from bytes, not from the file extension.
- For PNG, confirm 8-bit RGB or RGBA; convert 16-bit PNG to 8-bit.
- For video, confirm H.264 and AAC; transcode otherwise.
- For documents, set `filename` so the user sees a meaningful name (invoices, size charts).
- Keep a map of `(content hash -> media id, uploaded_at)` and re-upload after 25 days to stay inside the 30 day lifetime.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/sticker-messages
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages (10 minute link cache)
- Earlier run: reference/media page (size and format limits, id lifetimes)

Rendered empty or 404: none fetched in this run for image/document/video/audio message pages; caption max length and MIME strings are therefore marked unverified.
