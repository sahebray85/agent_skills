# Download Media — Specification

> **When to load**: Downloading the bytes of an inbound or uploaded media file from the short-lived URL returned by the retrieve-URL call.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | The full `url` returned by `GET /{version}/{media-id}` (a Meta CDN URL, not `graph.facebook.com`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Fetch the binary content of a media file |
| **Idempotency / retry** | Read-only, safe to retry while the URL is valid (about 5 minutes). On 404 fetch a new URL and retry once. |

## Request

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| URL | string | yes | `url` from `retrieve_url.md` | Valid about 5 minutes; use as returned, including all query parameters |
| `Authorization` header | string | yes | `Bearer <TOKEN>` | Download without the token fails. Some HTTP clients drop the header on redirect: re-send it manually |
| `User-Agent` header | string | recommended | Any non-empty value | Missing User-Agent can be rejected by the CDN (unverified 2026-10-04) |

## Example request
```bash
# 1. resolve
URL=$(curl -s "https://graph.facebook.com/v26.0/<MEDIA_ID>" \
        -H "Authorization: Bearer <TOKEN>" | jq -r .url)
# 2. download (url is not on graph.facebook.com; token still required)
curl -L "$URL" -H "Authorization: Bearer <TOKEN>" -H "User-Agent: sor-service/1.0" -o media.bin
sha256sum media.bin   # compare with sha256 from the retrieve call
```

## Response
Binary body with `Content-Type` equal to the media `mime_type`.

| Field | Type | Description |
|---|---|---|
| body | bytes | The file |
| `Content-Type` | header | Matches `mime_type` from retrieve |
| `Content-Length` | header | Should equal `file_size` (unverified 2026-10-04) |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 404 | URL expired (older than about 5 minutes) | Call retrieve again for a fresh URL | Yes, once with a new URL |
| 401 / 403 | Missing or wrong token (unverified 2026-10-04) | Send `Authorization: Bearer <TOKEN>` on the CDN request | After fixing |
| 400 | Malformed URL (query parameters stripped or encoded) (unverified 2026-10-04) | Use the URL verbatim; mind JSON escaping of `&` | After fixing |
| 5xx | CDN transient error | Retry with backoff, then re-resolve URL | Yes |

The CDN responds with HTTP status codes, not the Graph `error` envelope.

## Quirks and gotchas
- The URL is on a Meta CDN, not the Graph host, yet the bearer token is still required.
- The URL lives about 5 minutes; resolve and download back to back. Do not queue downloads with stored URLs.
- 404 on download means expiry, not a missing file; the media id itself may still be valid (7 days for inbound, 30 days for uploads).
- Inbound webhook media ids die after 7 days: persist customer images and documents to your own storage on receipt.
- Validate `sha256` and size, and re-detect the MIME type from bytes before trusting the file (user-supplied content; scan documents for malware before opening).
- Do not forward the download URL to browsers or third parties; it needs your token.
- Large documents (up to 100 MB) need streaming download, not full buffering.

### Download flow in pseudocode
```
GET url with headers {Authorization: Bearer <TOKEN>, User-Agent: sor-service}
if status == 404: url = retrieve(mediaId).url; retry once
stream body to temp file while computing SHA-256
compare with sha256 from retrieve; reject on mismatch
move temp file to final storage (for example S3) and record mime_type, file_size
```

### Common failure matrix
```
Symptom                                  Likely cause                         Fix
404 right after retrieve                 URL mangled or re-encoded            use URL verbatim
404 several minutes later                URL expired                          call retrieve again
401 / 403                                no Authorization header on CDN call  add header, also after redirects
Empty or short body                      connection cut                       compare Content-Length, retry
Hash mismatch                            truncated or wrong file              discard and re-download
```

### Security notes
- Treat downloaded files as untrusted input: scan, size-cap, and never execute.
- Strip EXIF location data from customer photos before sharing them internally if privacy policy requires it.
- Store only the media id and your own copy location, not the signed CDN URL.
- Limit download concurrency so bursts of inbound media do not exceed Graph throughput limits (the retrieve call is a Graph call; 130429 applies).

### Java client sketch
```java
HttpRequest request = HttpRequest.newBuilder(URI.create(mediaUrl))
    .header("Authorization", "Bearer " + token)
    .header("User-Agent", "sor-service/1.0")
    .GET().build();
HttpResponse<InputStream> response =
    client.send(request, HttpResponse.BodyHandlers.ofInputStream());
if (response.statusCode() == 404) { /* re-resolve url via retrieve and retry once */ }
```
Use a `HttpClient` with `Redirect.NORMAL`; Java drops the Authorization header on cross-host redirects, so if the CDN redirects, re-issue the request manually with the header.

### Test checklist
- Valid URL with token returns bytes whose SHA-256 equals the retrieve response.
- Missing token yields an auth failure.
- Expired URL (wait over 5 minutes) yields 404 and the retry path recovers.
- A file near the 100 MB document limit streams without exhausting heap.

### Related endpoints
(All use the same bearer token and the `v26.0` base.)
- Resolve the URL first: `retrieve_url.md`.
- Upload your own files: `upload.md`.
- Inbound media arrives in webhooks as `messages[].image|video|audio|document|sticker.id` with `mime_type` and `sha256`.

### Storage guidance
- Store under a key derived from the SHA-256 to de-duplicate repeated uploads by the same customer.
- Record `mime_type`, `file_size`, source `wamid` and receipt time next to the object.
- Apply a retention policy; customer media can contain personal data and falls under your privacy obligations.

## Sources (verified 2026-10-04)
Returned content:
- Earlier run: reference/media page (download URL lifetime 5 minutes, token required, 404 means re-fetch)

Rendered empty:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/media (this run)
