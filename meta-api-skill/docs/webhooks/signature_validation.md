# Webhook Signature Validation — Specification

> **When to load**: You are implementing or debugging `X-Hub-Signature-256` verification of inbound webhook POSTs.

## Quick Reference
| Field | Value |
|---|---|
| Header | `X-Hub-Signature-256: sha256=<64 hex chars>` |
| Algorithm | HMAC-SHA256 |
| Key | App Secret (`<APP_SECRET>`) of the app that owns the webhook |
| Message | The exact raw request body bytes |
| Compare | Constant-time, on the hex digest |
| On mismatch | Reject (401/403), do not process, do not log the body |

## Steps
1. Read the raw body bytes before any JSON parsing or charset conversion.
2. Read header `X-Hub-Signature-256`. If missing or lacking the `sha256=` prefix, reject.
3. Compute `HMAC_SHA256(key = APP_SECRET bytes, message = raw body bytes)`, lowercase hex.
4. Build `expected = "sha256=" + hex`.
5. Compare `expected` with the header using a constant-time comparison (`MessageDigest.isEqual`, `hmac.compare_digest`).
6. Only on success parse JSON and dispatch.

## Java pseudo-code
```java
byte[] raw = request.getInputStream().readAllBytes();          // raw, before Jackson
String header = request.getHeader("X-Hub-Signature-256");
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(new SecretKeySpec(appSecret.getBytes(UTF_8), "HmacSHA256"));
String expected = "sha256=" + HexFormat.of().formatHex(mac.doFinal(raw));
boolean ok = header != null && MessageDigest.isEqual(
        expected.getBytes(UTF_8), header.getBytes(UTF_8));
```
In Spring, take `@RequestBody byte[]` (or `String` with a byte-preserving converter), never a deserialised DTO.

## Python pseudo-code
```python
raw = request.get_data()                       # bytes
header = request.headers.get("X-Hub-Signature-256", "")
digest = hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
ok = hmac.compare_digest("sha256=" + digest, header)
```

## Example
```
POST /webhooks/whatsapp
X-Hub-Signature-256: sha256=<hex-hmac-of-body>
Content-Type: application/json

{"object":"whatsapp_business_account","entry":[...]}
```

## Errors / failure modes
| Code | Meaning | Action | Retry? |
|---|---|---|---|
| Header absent | Not from Meta, or proxy stripped it | Reject 401; check proxy header pass-through | n/a |
| Mismatch, always | Wrong secret (token vs secret, other app, rotated secret) or body mutated | Use App Secret from App Settings > Basic | Fix config |
| Mismatch, intermittent | Body re-serialised, gzip/charset altered, trailing newline | Hash the bytes as received | Fix code |
| Rejecting returns non-200 | Meta will retry the same payload | Expected for forged calls; legit calls should not hit this | Meta retries |

## Quirks and gotchas
- The key is the App Secret, not the verify token and not the access token.
- Compute over raw bytes. Parsing then re-serialising changes whitespace and key order and breaks the hash. Unicode escaping (`é` vs literal) is the classic trap: Meta escapes non-ASCII in its body, so hashing a decoded string gives the wrong result.
- A request body filter (Spring `ContentCachingRequestWrapper`, Servlet filter) must cache the bytes before the controller reads them.
- Never compare with `==`/`equals`; timing leaks.
- If several apps share one URL, select the secret per app (route by path), not by trial.
- This is separate from `appsecret_proof` (outbound calls), see `docs/common/auth.md`.
- Do not log the secret or the full computed digest.

## Sources (verified 2026-10-04)
- https://developers.facebook.com/docs/graph-api/webhooks/getting-started (header format and HMAC description; verified by caller)
- The Unicode-escaping note is widely reported behaviour, not re-confirmed on a Meta page this run (unverified 2026-10-04).
