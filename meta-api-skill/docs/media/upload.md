# Upload Media — Specification

> **When to load**: Uploading an image, video, audio, document or sticker to WhatsApp to obtain a media id for sending or for a template header.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` (multipart/form-data) |
| **Path** | `/{version}/{phone-number-id}/media` (`https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/media`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Store a file on WhatsApp and get a reusable media id |
| **Idempotency / retry** | Not idempotent: every upload creates a new id. Retrying after a timeout may leave an orphan id (harmless; it expires). Safe to retry on 5xx. |

## Request

Form fields (multipart, not JSON):

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `messaging_product` | string | yes | `whatsapp` | Fixed |
| `file` | file | yes | Binary file; send as `-F file=@path;type=<mime>` | Size per type below |
| `type` | string | yes | MIME type of the file, e.g. `image/jpeg` | Must match real bytes and be a supported type |

### Limits
```
Type      Formats                                                   Max
image     JPEG, PNG (8-bit RGB / RGBA)                              5 MB
video     MP4, 3GP (H.264 video + AAC audio)                        16 MB
audio     AAC, AMR, MP3, M4A, OGG                                   16 MB
document  TXT, XLS, XLSX, DOC, DOCX, PPT, PPTX, PDF                 100 MB
sticker   WebP static                                               100 KB
sticker   WebP animated                                             500 KB
```

Lifetime: media ids from this API are retained 30 days; ids delivered in inbound webhooks live 7 days.

## Example request
```bash
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/media" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "messaging_product=whatsapp" \
  -F "file=@./lookbook.jpg;type=image/jpeg" \
  -F "type=image/jpeg"
```

## Response
```json
{"id": "<MEDIA_ID>"}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Media id; use in `image.id`, `document.id`, ..., template header parameters and the retrieve/delete endpoints |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 131053 | Media upload error (unsupported type, over size, corrupt file) | Check MIME, size, codec; for PNG use 8-bit | After fixing |
| 100 | Invalid parameter, e.g. missing `type` or `messaging_product` (unverified 2026-10-04) | Fix the form | After fixing |
| 190 | Token invalid or expired (unverified 2026-10-04) | Refresh token | After fixing |
| 130429 | Throughput exceeded | Back off | Yes, backoff |
| 413 / network reset | File larger than the gateway accepts (unverified 2026-10-04) | Compress or use resumable upload only for template-sample handles (see `resumable_upload.md`) | After fixing |

## Quirks and gotchas
- Multipart only; do not send JSON or base64.
- Declare the correct MIME in both the `file` part (`;type=`) and the `type` field; mismatches are rejected.
- Upload once, send to many: the id is reusable for any recipient until expiry (30 days).
- The id is scoped to the phone number that uploaded it (unverified 2026-10-04); upload against the same `<PHONE_NUMBER_ID>` you send from.
- This endpoint is for message media. Template creation samples need a handle from the resumable upload API (`resumable_upload.md`), not this id.
- For sending, prefer id over public link; links are cached by the Cloud API for 10 minutes.
- Windows and curl: quote the `@path;type=` argument, otherwise the shell can strip the semicolon.

### Example with document and sticker
```bash
curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/media" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "messaging_product=whatsapp" -F "file=@./size-chart.pdf;type=application/pdf" -F "type=application/pdf"

curl -X POST "https://graph.facebook.com/v26.0/<PHONE_NUMBER_ID>/media" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "messaging_product=whatsapp" -F "file=@./thanks.webp;type=image/webp" -F "type=image/webp"
```

### Pre-upload checklist
- Size under the type limit (image 5 MB, video and audio 16 MB, document 100 MB, sticker 100 KB static or 500 KB animated).
- MIME sniffed from bytes and equal to the declared `type`.
- PNG is 8-bit; video is H.264 with AAC.
- Hash the file and look up your cache of ids to avoid duplicate uploads.

### Cache design
Store `(sha256, phone_number_id) -> (media_id, uploaded_at)`. Treat an id older than 25 days as stale and re-upload, since ids expire at 30 days.

### Spring multipart sketch
```java
MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
body.add("messaging_product", "whatsapp");
body.add("type", mimeType);
body.add("file", new NamedByteArrayResource(bytes, fileName)); // part content type = mimeType
restClient.post().uri("/{phoneNumberId}/media", phoneNumberId)
    .header("Authorization", "Bearer " + token)
    .contentType(MediaType.MULTIPART_FORM_DATA)
    .body(body).retrieve().body(UploadResponse.class);
record UploadResponse(String id) {}
```
Set the part content type explicitly; many HTTP clients default to `application/octet-stream`, which Meta can reject.

### Test checklist
- JPEG under 5 MB returns an id; the same file declared as `image/png` is rejected.
- File over the limit fails with a media error rather than a generic 500.
- The returned id works in a follow-up send and in the retrieve call.

### Related endpoints
- Send by id: `../messaging/send_media.md`; template header media: `../messaging/send_template.md`.
- Delete early: `delete.md`; template sample handles: `resumable_upload.md`.

## Sources (verified 2026-10-04)
Returned content:
- Earlier run: reference/media (limits, formats, 30 day and 7 day lifetimes)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/sticker-messages (sticker limits, `image/webp`)
- https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages (10 minute link cache)

Rendered empty or 404: none fetched this run for the upload reference page; the response `{"id":...}` shape and the form fields come from the brief's verified facts.
