# Error Handling & Retry Strategy — Common Patterns

> **Scope**: Error handling and retry patterns shared across ALL Delhivery B2C APIs. Load this when writing integration code.

---

## 1. Error Categories

Errors fall into three distinct categories. Each requires different handling.

### 1.1 HTTP Status Code Errors

| Code | Meaning | Action | Retry? |
|------|---------|--------|--------|
| 200 | Request processed | **Check body** — may contain business logic failure | No |
| 400 | Bad Request | Log error with full context. Fix the request. | **Never** |
| 401 | Unauthorized | Token invalid/expired. Refresh token. | **Never** (with same token) |
| 403 | Forbidden | Rate limit exceeded or WAF block. Pause 30s, then retry. Also used for insufficient permissions. | **Yes** (after 30s pause) |
| 5xx | Server Error | Transient failure. Retry with backoff. | **Yes** |
| Timeout | Request timeout | Network/server slow. Retry with backoff. | **Yes** |

**Note on 403**: A 403 response can indicate either:
- **Rate limiting**: You've exceeded 750 requests per 5 minutes. Pause for 30 seconds.
- **WAF protection**: Your request pattern triggered the Web Application Firewall. Pause for 30 seconds.
- **Permissions**: Insufficient permissions or invalid token (less common).

### 1.2 Business Logic Errors (Inside 200 Responses)

Some APIs return HTTP 200 but include failure indicators in the response body. **These MUST NOT be retried.**

| API | Failure Indicator | Example |
|-----|-------------------|---------|
| Edit Shipment | `status: "Failure"` with `error` field | `"Unable to change payment mode from Pre-paid to COD"` |
| Package Tracking | 400 with `Success: false` | `"Data does not exists for provided Waybill(s)"` — data not found, not a server error |
| Expected TAT | `success: false` with `msg` field | `"Origin pin not serviceable"` |
| Cancel Shipment | `status: true` with `remark` field | `"Shipment has been cancelled."` (success case — but always check `status`) |
| Shipment Creation | `success: false` with `rmk` field | `"ClientWarehouse matching query does not exist."` |
| RVP QC | `success: false` with per-package `status: "Fail"` in `packages[]` | `"Duplicate waybill"`, `"Package type Pickup not serviceable for {client}"` |
| Document Download | `success: false` with `message` field | `"Invalid waybill passed"` |
| E-Waybill Update | 200 with `success: false` and `message` field | `"Package not found"`, `"Following EWBNs are invalid: ..."` |
| NDR Status | `status: "Failure"` with `remark` field | `"Zero waybills affected"` |
| Pickup Request | 400 with object containing field-level errors | `{"pickup_location": "Invalid Pickup Location ClientWarehouse matching query does not exist."}` |

**Rule**: Always inspect the response body after a 200 response. Check for application-level success/failure indicators before treating the call as successful.

### 1.3 Per-Package / Per-Item Errors (Batch Operations)

Some APIs process multiple items in one request. Individual items can fail while others succeed:

| API | How to Check | Details |
|-----|-------------|---------|
| Shipment Creation | Check each `packages[].status` | `"Success"` or `"Fail"` per package, with `remarks[]` |
| RVP QC | Check each `packages[].status` | Same structure as Shipment Creation |
| Packing Slip | Check each entry in `packages[]` | Some may have data, others may be missing |
| NDR Status | Check `failed_wbns[]` and `success_wbns[]` | Per-waybill success/failure with reasons |

**Rule**: For batch APIs, always iterate the response array and check each item's status individually. A top-level `success: true` does NOT guarantee all items succeeded.

### 1.5 Critical Error Codes & Troubleshooting

| Code/Remark | Context | Action/Fix |
|:---|:---|:---|
| `EOD-74, 15, 104, 43...` | NDR Re-attempt | Valid states for re-attempt action via NDR Update API |
| `EOD-777` | RVP QC Fail | Eligible for PICKUP_RESCHEDULE action |
| `EOD-21` | Pickup Canceled | Eligible for PICKUP_RESCHEDULE (if non-OTP) |
| `NoneType...end_date` | Token/Env mismatch | Check that you're using Staging credentials with Staging URLs, or Prod credentials with Prod URLs |
| `Suspicious order` | Consignee flagged | The consignee has been flagged in Delhivery's system. Contact your Business POC for resolution |
| `403 Forbidden` | WAF/Rate Limit | Pause for 30 seconds. Ensure you stay below 750 requests per 5 minutes |
| `1100** is non serviceable` (on valid pincode) | Account type mismatch | Verify if your account is B2C-only vs Heavy-enabled. Some pincodes require Heavy account access |

### 1.4 Parsing Errors

Errors encountered while parsing the API response.

**Handling**:
- Use safe access patterns (`.get()` with defaults) for ALL nested field access.
- Wrap response parsing in `try-except` to catch `KeyError`, `IndexError`, `TypeError`, and `JSONDecodeError`.
- Log the raw response body when parsing fails.
- Return a structured error to the caller.

---

## 2. Retry Strategy — Exponential Backoff

### 2.1 Default Parameters

| Parameter | Value |
|-----------|-------|
| Max attempts | 3 |
| Initial delay | 1.0 seconds |
| Backoff multiplier | 2.0 |
| Delay sequence | 1s → 2s → 4s |

### 2.2 When to Retry

- HTTP 5xx server errors (500, 502, 503, 504)
- Request timeouts
- Transient network failures (connection reset, DNS resolution failure)

### 2.3 When NOT to Retry

- HTTP 400 Bad Request — fix the input
- HTTP 401 Unauthorized — refresh the token
- HTTP 403 Forbidden — check permissions (or try alternate auth for Expected TAT)
- Business logic errors inside 200 responses (e.g., `status="Failure"`, `success=false`)
- Data-not-found responses (e.g., 400 with `Success=false` for tracking)
- Per-package failures in batch responses — retry the failed items only, not the entire batch

### 2.4 Retry Flow

```
1. Attempt the request with configured timeout.
2. If response is 5xx OR request timed out OR network error:
   a. If attempts < max_attempts:
      - Wait: delay = initial_delay × (multiplier ^ attempt_number)
      - Retry
   b. Else: Return clear error to caller
3. If response is 4xx: Return error immediately (no retry)
4. If response is 200: Check body for business logic errors
   - If business error found: Return error immediately (no retry)
   - If success: Return result
```

### 2.5 Configuration

Store retry parameters in configuration so they can be tuned per API:

```
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0
```

---

## 3. Implementation Guidance

When helping a developer implement error handling:

1. Check if they already have retry utilities in their codebase.
2. If yes, extend their existing pattern.
3. If no, suggest a retry wrapper that:
   - Accepts a callable (the API call function)
   - Reads retry parameters from configuration
   - Distinguishes between retryable and non-retryable errors
   - Logs each attempt with attempt number, delay, and reason
4. Make sure business logic errors are caught BEFORE the retry logic triggers.
5. For batch APIs, implement per-item error handling — don't treat the entire batch as failed if one item fails.
