# Retrieve Media URL — Specification

> **When to load**: Turning a media id (from an upload or an inbound webhook) into a temporary download URL plus MIME type, size and hash.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/{version}/{media-id}` (`https://graph.facebook.com/v26.0/<MEDIA_ID>`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Resolve a media id to a short-lived URL on Meta's media CDN |
| **Idempotency / retry** | Read-only and safe to retry. Each call returns a fresh URL, so call it again when the previous URL has expired. |

## Request

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `media-id` (path) | string | yes | Id from upload response or inbound webhook | API ids live 30 days; webhook ids 7 days |
| `phone_number_id` (query) | string | no | Restricts lookup to media owned by that phone number | Optional safeguard; returns an error if the media belongs to another number (unverified 2026-10-04) |

## Example request
```bash
curl "https://graph.facebook.com/v26.0/<MEDIA_ID>?phone_number_id=<PHONE_NUMBER_ID>" \
  -H "Authorization: Bearer <TOKEN>"
```

## Response
```json
{
  "messaging_product": "whatsapp",
  "url": "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=<MEDIA_ID>&ext=...&hash=...",
  "mime_type": "image/jpeg",
  "sha256": "<HEX_SHA256>",
  "file_size": 123456,
  "id": "<MEDIA_ID>"
}
```
Field set is standard for this endpoint; Meta's reference page rendered empty in this run, so the exact field list is (unverified 2026-10-04).

| Field | Type | Description |
|---|---|---|
| `messaging_product` | string | `whatsapp` |
| `url` | string | Download URL. Valid about 5 minutes. Needs the access token to download (see `download.md`) |
| `mime_type` | string | MIME type of the stored file |
| `sha256` | string | SHA-256 of the file; verify after download |
| `file_size` | integer | Bytes |
| `id` | string | The media id |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Unknown, expired or malformed media id, or not owned by this number (unverified 2026-10-04) | Ask the user to resend, or re-upload | No |
| 190 | Token invalid or expired (unverified 2026-10-04) | Refresh token | After fixing |
| 130429 | Throughput exceeded | Back off | Yes, backoff |
| 131052 / 131053 | Media related errors; 131053 is the upload error (verified code), 131052 download error (unverified 2026-10-04) | Check media | Depends |

## Quirks and gotchas
- The returned `url` expires after about 5 minutes. Resolve it immediately before downloading, do not store it.
- Media ids from inbound webhooks expire after 7 days; ids from your own uploads after 30 days. Download inbound customer media promptly and keep your own copy (for example in S3).
- Downloading the `url` needs your token (see `download.md`); the URL alone returns an auth error.
- A 404 on download means the URL expired: call this endpoint again for a new URL.
- Verify `sha256` and `file_size` after download to catch truncation.
- The URL host is a Meta CDN host; whitelist outbound egress to Meta's media hosts if your service is firewalled.
- Do not log the full URL; it contains a signed hash.

### Typical flow for inbound media
```
webhook messages[].image.id = <MEDIA_ID>
  -> GET /v26.0/<MEDIA_ID>            (resolve url, mime_type, sha256, file_size)
  -> GET url with Bearer token        (see download.md, within 5 minutes)
  -> verify sha256, store copy, record own reference
```

### Field handling advice
```
Field         Use
url           download immediately, never persist
mime_type     choose file extension and validation rules
sha256        integrity check and de-duplication key
file_size     enforce your own size cap before downloading
id            keep for audit; expires in 7 days (inbound) or 30 days (upload)
```

### Rate considerations
Every retrieve call is a Graph API call. For bursts of inbound media (for example a customer sending ten photos) resolve and download sequentially with a small concurrency cap, and back off on 130429.

### Failure handling
- Id unknown or expired: record the failure, ask the customer to resend the file.
- Token error: refresh the token and retry once.
- Never block webhook acknowledgement on retrieve and download; acknowledge with HTTP 200 first, process asynchronously.

### Spring Feign sketch
```java
@FeignClient(name = "metaMedia", url = "https://graph.facebook.com/v26.0")
interface MetaMediaClient {
    @GetMapping("/{mediaId}")
    MediaInfo retrieve(@PathVariable String mediaId,
                       @RequestHeader("Authorization") String bearer);
}
record MediaInfo(String id, String url, @JsonProperty("mime_type") String mimeType,
                 String sha256, @JsonProperty("file_size") long fileSize) {}
```
Ignore unknown JSON properties so that new fields from Meta do not break deserialisation.

### Test checklist
- Valid id returns a non-empty `url` and a `mime_type` that matches what was uploaded.
- Unknown id surfaces as a typed client error, not a generic exception.
- Two calls in a row return working URLs (each call mints a fresh URL).

### Related endpoints
(All use the same bearer token and the `v26.0` base.)
- Download the bytes: `download.md`; upload your own: `upload.md`; delete: `delete.md`.

## Sources (verified 2026-10-04)
Returned content:
- Earlier run: reference/media page (lifetimes, download URL 5 minutes, token needed, 404 means re-fetch)

Rendered empty:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/media (this run)
