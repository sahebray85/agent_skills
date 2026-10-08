# Delete Media — Specification

> **When to load**: Removing an uploaded media file from WhatsApp storage before its 30 day expiry, for example for privacy or cleanup.

## Quick Reference
| Field | Value |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/{version}/{media-id}` (`https://graph.facebook.com/v26.0/<MEDIA_ID>`) |
| **Auth** | `Authorization: Bearer <token>` |
| **Permissions** | `whatsapp_business_messaging` |
| **Purpose** | Delete a media object and invalidate its id |
| **Idempotency / retry** | Effectively idempotent: deleting an already-deleted or expired id returns an error but leaves the same end state. Treat "not found" as success. |

## Request

| Name | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `media-id` (path) | string | yes | Id to delete | Must be an id your account owns |
| `phone_number_id` (query) | string | no | Restricts the delete to media owned by this phone number | Optional (unverified 2026-10-04) |

## Example request
```bash
curl -X DELETE "https://graph.facebook.com/v26.0/<MEDIA_ID>?phone_number_id=<PHONE_NUMBER_ID>" \
  -H "Authorization: Bearer <TOKEN>"
```

## Response
```json
{"success": true}
```

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the media was deleted. Response shape is standard for this endpoint; Meta's reference page rendered empty, so this is (unverified 2026-10-04) |

## Errors
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| 100 | Unknown, expired or not owned media id (unverified 2026-10-04) | Treat as already gone | No |
| 190 | Token invalid or expired (unverified 2026-10-04) | Refresh token | After fixing |
| 130429 | Throughput exceeded | Back off | Yes, backoff |
| 5xx | Transient | Retry with backoff | Yes |

## Quirks and gotchas
- Deleting does not unsend messages already delivered; recipients keep their copy.
- A deleted id cannot be used for new sends; templates whose header used the id by reference are unaffected if you supply a fresh id at send time.
- Ids expire on their own: 30 days for API uploads, 7 days for webhook ids. Delete only when needed earlier.
- Delete only your own uploads; inbound customer media ids can be left to expire, but copy them to your storage first.
- The Cloud API caches link-based media for 10 minutes; deleting your hosted file does not purge that cache.
- Use sparingly in bulk jobs; each call counts toward API throughput.
- Keep a record of your own uploads (id, uploaded-at, owner) so cleanup does not need a list call, since there is no documented "list media" endpoint (unverified 2026-10-04).

### When deleting is worth it
```
Case                                              Action
Customer asked for data removal                   delete your uploads, remove your stored copies
Upload with wrong or sensitive content            delete immediately
Routine cleanup of old catalogue images           let ids expire (30 days)
Inbound customer media                            copy to own storage, let the id expire (7 days)
```

### Cleanup job outline
1. Keep a table of uploads: `media_id`, `phone_number_id`, `sha256`, `uploaded_at`, `purpose`.
2. A scheduled job selects rows past retention.
3. Call DELETE for each, treat a "not found" style error as success.
4. Remove the row. Record the deletion time for audit.

### Verification after delete
A follow-up `GET /{version}/<MEDIA_ID>` should now fail (error code 100 or similar, unverified 2026-10-04). Do not rely on this in production code paths; it costs an extra call.

### Permissions note
Deleting uses the same token scope as uploading. A token that can only read (for example an analytics token) cannot delete.

### Spring Feign sketch
```java
@FeignClient(name = "metaMedia", url = "https://graph.facebook.com/v26.0")
interface MetaMediaClient {
    @DeleteMapping("/{mediaId}")
    SuccessResponse delete(@PathVariable String mediaId,
                           @RequestParam(value = "phone_number_id", required = false) String phoneNumberId,
                           @RequestHeader("Authorization") String bearer);
}
record SuccessResponse(boolean success) {}
```
Map a "not found" error to a no-op in the error decoder so cleanup jobs stay idempotent.

### Test checklist
- Delete of a fresh id returns `success: true`.
- Second delete of the same id is treated as success by your wrapper.
- Delete with a token lacking permission surfaces as an authorisation error, not as a silent skip.
- Cleanup job continues past a single failure and reports the count of failures.

### Related endpoints
(All use the same bearer token and the `v26.0` base.)
- Upload: `upload.md`; retrieve: `retrieve_url.md`; download: `download.md`.
- Template sample handles from `resumable_upload.md` are not message media ids and cannot be deleted with this call (unverified 2026-10-04).
- Sending by id: `../messaging/send_media.md`.

### Audit note
Log `media_id`, caller, reason and result for each delete so that data-removal requests can be evidenced later. Do not log tokens.

### Edge cases to test
```
Case                                   Expected handling
Id already expired                     treat as success, drop local row
Id belongs to another phone number     surface error, do not retry
Token revoked                          stop the job, alert the owner
Network timeout during delete          retry; a second call is safe
Concurrent delete by two workers       one succeeds, the other sees not found: success
```
Run the cleanup job off-peak so it does not compete with send traffic for throughput.

## Sources (verified 2026-10-04)
Returned content:
- Earlier run: reference/media page (id lifetimes 30 days and 7 days)

Rendered empty:
- https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/media (this run); the DELETE response and error details are therefore unverified
