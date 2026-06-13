# Integration Checklist — Pre & Post

> **Scope**: Generic checklist applicable to every Delhivery B2C API integration. Use this to validate completeness.

---

## Pre-Integration (Discuss with User)

- [ ] **Field name fidelity**: Confirm that EXACT field names from API spec will be used (no renaming, no synonyms)
- [ ] **Configuration location**: Where will base URLs, paths, and timeouts live? (Ask about their config file structure)
- [ ] **Environment selection**: How does their system distinguish staging from production? (Ask explicitly — never default)
- [ ] **Timeout**: Set appropriate default based on API's p99 latency. Ensure it's read from config, not hardcoded.
- [ ] **Authentication scheme**: Confirm which auth scheme the specific API uses (Token header, Bearer header, or query parameter).
- [ ] **Input validation**: Agree on validation rules and where validation logic should live.
- [ ] **Retry strategy**: Clarify which errors to retry, how many attempts, and delay schedule.
- [ ] **Error handling philosophy**: Exceptions vs result objects vs error codes — match their existing pattern.
- [ ] **Tests**: Ask if they want tests generated.

---

## Post-Integration (Verify)

- [ ] **Field names match API spec exactly** (no renaming like `pincode` → `pin`, `origin_pincode` → `origin_pin`)
- [ ] Base URL and path stored separately in configuration
- [ ] Authentication token sourced from environment variables, never hardcoded
- [ ] All required input validation in place before API calls
- [ ] Exponential backoff retry implemented for 5xx and timeouts only
- [ ] 4xx errors and business logic errors are NOT retried
- [ ] All errors logged with sufficient context (URL, params, status code, response body)
- [ ] Response parsing handles missing or null fields gracefully (`.get()` with defaults)
- [ ] Privacy requirements addressed for logging (token masking, PII handling)
- [ ] Complete runnable files delivered (not snippets or pseudocode)
- [ ] **Do NOT auto-execute**: After delivering files, STOP. Do not run or test the code yourself. The user will do it.

---

## Common Pitfalls Quick Reference

| Pitfall | Correct Approach |
|---------|-----------------|
| **Using wrong field names** (`pincode` vs `pin`, `origin_pincode` vs `origin_pin`) | **Copy exact field names from API spec** |
| Hardcoding base URLs | Store in config, construct at runtime |
| Hardcoding tokens in source | Read from env vars or secrets manager |
| Using `Bearer` when `Token` is required | Check API-specific spec for correct scheme |
| Retrying on 4xx errors | 4xx = fix the request, don't retry |
| Retrying business logic errors in 200 | Check response body, don't retry `status="Failure"` |
| Hardcoding timeout values | Read from config, default based on p99 latency |
| Not validating inputs before API calls | Validate locally to avoid unnecessary network calls |
| Assuming 200 always means success | Some APIs return 200 with failure payload |
| Unsafe nested field access | Use `.get()` with defaults at every nesting level |
| Logging full auth tokens | Log only masked portion (first 8 chars) |
| Passing `int` when API expects `float` | Check API spec for type requirements |
| Sending `boolean` when API expects string `"true"` | Check API spec for string boolean requirements |
