# Logging & Observability — Common Patterns

> **Scope**: Logging patterns shared across ALL Delhivery B2C API integrations.

---

## 1. What to Log

### Per API Call
- URL (without full token)
- HTTP method
- Parameters (excluding sensitive values)
- Timestamp

### Per Response
- HTTP status code
- Success/failure indicator
- Key response fields (waybill, order_id, status)

### Per Error
- Full error message
- Status code
- Raw response body (if available)

### Per Retry
- Attempt number
- Delay before next attempt
- Reason for retry

---

## 2. Log Levels

| Scenario | Level |
|----------|-------|
| Successful API call | INFO |
| Retry attempt | WARNING |
| Client error (4xx) | WARNING |
| Server error (5xx) | ERROR |
| Parsing failure | ERROR |
| Network failure | ERROR |

---

## 3. Data Sensitivity

- **Never** log full authentication tokens. Log only a masked version (first 8 characters + `***`).
- Discuss with the team whether pincodes, waybill numbers, or customer details need redaction.
- Align logging verbosity with the team's existing standards (verbose in staging, minimal in production).

---

## 4. Structured Logging

Prefer structured logging (key-value pairs or JSON) for easy searching and filtering:

```
{
  "event": "api_call",
  "api": "tracking",
  "waybill": "84649910000011",
  "status_code": 200,
  "success": true,
  "duration_ms": 245
}
```

Include a request identifier or correlation ID to trace calls across services.

---

## 5. Implementation Guidance

When helping a developer add logging:

1. Check their existing logging setup (framework, format, destination).
2. Follow their existing logging pattern exactly.
3. Add structured entries for API calls that include status, key identifiers, and duration.
4. Don't introduce a new logging framework if they already have one.
