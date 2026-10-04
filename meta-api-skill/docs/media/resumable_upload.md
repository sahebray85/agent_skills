# Resumable Upload API — Specification

> **When to load**: Getting an upload handle (`h`) for a template creation sample (image, video, document) or any large file, using the Graph resumable upload sessions.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `POST` (start session), `POST` (send bytes), `GET` (resume offset) |
| **Path** | `/{version}/<APP_ID>/uploads`, then `/{version}/upload:<UPLOAD_SESSION_ID>` |
| **Auth** | Start: `access_token` param or Bearer. Upload and resume: `Authorization: OAuth <token>` (not `Bearer`) |
| **Permissions** | App-level: token of a user/system user with access to the app (`whatsapp_business_management` for template use) |
| **Purpose** | Upload a file in a resumable session and obtain a handle used as `header_handle` in template creation |
| **Idempotency / retry** | Start-session is not idempotent (new session each call). Byte upload is resumable: query the offset and resend from there. |

## Request

### 1. Start session: `POST /{version}/<APP_ID>/uploads`
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `file_name` | string | yes | File name | |
| `file_length` | integer | yes | Size in bytes | Must equal the real size |
| `file_type` | string | yes | MIME type | Valid values: `application/pdf`, `image/jpeg`, `image/jpg`, `image/png`, `video/mp4` |
| `access_token` | string | yes (if no header) | Token | Can be supplied as a query parameter or form field |

### 2. Upload bytes: `POST /{version}/upload:<UPLOAD_SESSION_ID>`
| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `Authorization` header | string | yes | `OAuth <TOKEN>` | Not `Bearer`; this is the documented difference |
| `file_offset` header | integer | yes | Byte offset; `0` for a fresh upload | Use the offset from the resume call after an interruption |
| body | bytes | yes | Raw file bytes from the offset (`--data-binary @file`) | Not multipart |

### 3. Resume: `GET /{version}/upload:<UPLOAD_SESSION_ID>`
Header `Authorization: OAuth <TOKEN>`. The response includes `file_offset`; resend the POST with that offset in the `file_offset` header.

## Example request
```bash
# 1. start
curl -X POST "https://graph.facebook.com/v26.0/<APP_ID>/uploads" \
  -d "file_name=sample.jpg" -d "file_length=204800" -d "file_type=image/jpeg" \
  -d "access_token=<TOKEN>"
# -> {"id":"upload:<UPLOAD_SESSION_ID>"}

# 2. upload
curl -X POST "https://graph.facebook.com/v26.0/upload:<UPLOAD_SESSION_ID>" \
  -H "Authorization: OAuth <TOKEN>" -H "file_offset: 0" \
  --data-binary @sample.jpg
# -> {"h":"4::aW1hZ2UvanBlZw==:ARZ..."}

# 3. resume after failure
curl "https://graph.facebook.com/v26.0/upload:<UPLOAD_SESSION_ID>" \
  -H "Authorization: OAuth <TOKEN>"
# -> {"id":"upload:<UPLOAD_SESSION_ID>","file_offset":102400}
```

## Response
Start:
```json
{"id": "upload:<UPLOAD_SESSION_ID>"}
```
Upload:
```json
{"h": "<UPLOADED_FILE_HANDLE>"}
```
Resume:
```json
{"id": "upload:<UPLOAD_SESSION_ID>", "file_offset": 102400}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Session id, prefixed `upload:` (include the prefix in the next path) |
| `h` | string | File handle. Pass as `example.header_handle[0]` when creating a template with a media header |
| `file_offset` | integer | Bytes already received; continue from here |

The `id` and `h` fields and the three calls are verified. The resume response shape beyond `file_offset` is (unverified 2026-10-04).

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Invalid parameter: bad `file_type`, `file_length` mismatch, bad session id (unverified 2026-10-04) | Fix inputs | After fixing |
| 190 | Token invalid or expired (unverified 2026-10-04) | Refresh token | After fixing |
| 368 / 4 / 17 | Rate or policy limits on the Graph app (unverified 2026-10-04) | Back off | Yes, backoff |
| network drop mid-upload | Partial bytes stored | GET the offset and resume | Yes |

## Quirks and gotchas
- The upload header is `Authorization: OAuth <token>`, not `Bearer`. Using Bearer on this endpoint is a classic failure.
- Only PDF, JPEG, JPG, PNG and MP4 are accepted file types here; audio and other document types are not.
- This handle is for template creation (`header_handle`) and is different from the message media id returned by `POST /{phone-number-id}/media`; the two are not interchangeable.
- The session id keeps the `upload:` prefix.
- Session expiry is not documented (unverified 2026-10-04); upload promptly after starting.
- `file_length` must be the exact byte size; a mismatch makes the upload fail or stall.
- Handles are long opaque strings containing `:` and `=`; store them verbatim and JSON-encode them correctly.
- The app id (`<APP_ID>`) is the Meta app that owns the WABA relationship, not the WABA id or phone-number id.

### Using the handle in template creation
The handle returned as `h` goes into the template creation payload:
```json
{"type": "HEADER", "format": "IMAGE", "example": {"header_handle": ["<UPLOADED_FILE_HANDLE>"]}}
```
Create the session with `file_type` matching the sample (`image/jpeg`, `image/png`, `video/mp4` or `application/pdf`). The `header_handle` payload shape is from general Cloud API knowledge (unverified 2026-10-04).

### Resume algorithm
```
offset = 0
loop:
  try POST upload:<ID> with header file_offset=offset and body bytes[offset:]
  on success: read h, stop
  on network failure: offset = GET upload:<ID>.file_offset ; continue
```

### Checklist
- Session started with the correct `file_length`.
- Both follow-up calls use `Authorization: OAuth <TOKEN>`.
- Body sent as raw bytes (`--data-binary`), never as multipart form.
- The handle is stored only for the template creation call that follows; it is not a message media id.

## Sources (verified 2026-10-04)
Returned content:
- https://developers.facebook.com/docs/graph-api/guides/upload (steps, params, `OAuth` header, `file_offset`, `h`, valid `file_type` values; the page returned a German-localised rendering)
- Earlier run: Graph resumable upload findings (same shape)

Rendered empty or 404: none for this file.
