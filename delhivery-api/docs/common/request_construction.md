# Request Construction — Common Patterns

> **Scope**: Request building and input validation patterns shared across ALL Delhivery B2C APIs.

---

## 0. CRITICAL: Field Name Fidelity

**ABSOLUTE RULE**: Use the EXACT field names from the API specification. Do NOT rename, abbreviate, or "improve" field names.

### Why This Matters

The Delhivery API expects precise field names. Changing `origin_pin` to `origin_pincode` or `pin` to `pincode` will cause the API to reject your request with validation errors or silently ignore the field.

### Enforcement Rules

1. **Copy field names character-for-character** from the API spec
2. **Do NOT make assumptions** about what a field "should" be called
3. **Do NOT use synonyms** (e.g., `pincode` instead of `pin`, `waybill_number` instead of `waybill`)
4. **Do NOT add prefixes or suffixes** (e.g., `origin_pincode` instead of `origin_pin`)
5. **Preserve exact casing** (e.g., `origin_pin` not `Origin_Pin` or `ORIGIN_PIN`)

### Common Mistakes to AVOID

| ❌ WRONG | ✅ CORRECT | API |
|---------|-----------|-----|
| `origin_pincode` | `origin_pin` | Expected TAT |
| `destination_pincode` | `destination_pin` | Expected TAT |
| `pincode` | `pin` | Shipment Creation |
| `waybill_number` | `waybill` | Tracking, Edit, Cancel |
| `phone_number` | `phone` | Shipment Creation, Edit |
| `order_number` | `order` | Shipment Creation |
| `pickup_location_name` | `name` (inside `pickup_location` object) | Shipment Creation |

### When Creating Sample Requests or Test Data

**ALWAYS**:
1. Reference the API spec document for exact field names
2. Copy field names directly from the spec
3. Verify field names match the spec before sending requests

**NEVER**:
1. Guess or infer field names based on their meaning
2. Use "more descriptive" names than what the spec provides
3. Assume field naming conventions (e.g., all fields use `_pincode` suffix)

### Example: Expected TAT API

**API Spec Says**:
- `origin_pin` (integer)
- `destination_pin` (integer)

**CORRECT Request**:
```json
{
  "origin_pin": 110001,
  "destination_pin": 400001
}
```

**WRONG Request** (will fail):
```json
{
  "origin_pincode": 110001,
  "destination_pincode": 400001
}
```

### Example: Shipment Creation API

**API Spec Says**:
- `pin` (integer) - destination pincode
- `phone` (array of strings)

**CORRECT Request**:
```json
{
  "pin": 110001,
  "phone": ["9876543210"]
}
```

**WRONG Request** (will fail):
```json
{
  "pincode": 110001,
  "phone_number": ["9876543210"]
}
```

---

## 1. URL Construction

- Construct the full URL at runtime by joining `base_url + path` from configuration.
- Keep URL construction in a shared utility so all callers build URLs consistently.
- **Never** hardcode full URLs in application code.

### Path Parameters

Some APIs use path parameters (not query parameters):

| API | Path Pattern | Example |
|-----|-------------|---------|
| E-Waybill Update | `/api/rest/ewaybill/{waybill}/` | `/api/rest/ewaybill/84649910000011/` |
| NDR Status | `/api/cmu/get_bulk_upl/{request_id}` | `/api/cmu/get_bulk_upl/UPL17749083484755923441` |

Build these with string formatting, not string concatenation:
```
# GOOD — clear and safe
url = f"{base_url}/api/rest/ewaybill/{waybill}/"

# BAD — fragile concatenation
url = base_url + "/api/rest/ewaybill/" + waybill + "/"
```

---

## 2. HTTP Methods

Most Delhivery APIs use GET or POST, but not all:

| Method | APIs |
|--------|------|
| **GET** | Pincode Serviceability, Bulk Client Pincode, Package Tracking, Invoice Charges, Packing Slip, Expected TAT, Bulk Waybill, NDR Status, Document Download |
| **POST** | Edit Shipment, Cancel Shipment, Shipment Creation, RVP QC, Pickup Request, Warehouse Create, Warehouse Edit, NDR Update |
| **PUT** | E-Waybill Update |

Make sure the HTTP client uses the correct method — using POST where PUT is required (or vice versa) will result in 405 Method Not Allowed or unexpected behavior.

---

## 3. Sync vs Async — Decision Guide

### 3.1 Detection First, Ask Only If Ambiguous

Before deciding sync or async, **inspect the user's codebase**:

| Codebase Signal | Decision |
|-----------------|----------|
| Uses `requests`, `urllib3`, Flask (sync) | **Follow sync** — use `requests` |
| Uses `aiohttp`, `httpx.AsyncClient`, FastAPI (async) | **Follow async** — use their async HTTP client |
| Uses `httpx` (sync mode) | **Follow sync** — use `httpx` in sync mode |
| Mixed (e.g., Django with some async views) | **Ask the user** which pattern to follow for this integration |
| Greenfield / no existing HTTP calls | **Ask the user** — present trade-offs below |

**Rule**: If the codebase already has a clear pattern, follow it silently. Only ask when it's genuinely ambiguous.

### 3.2 When Async Provides Clear Benefit

| Scenario | Why Async Helps |
|----------|----------------|
| Bulk operations (Bulk Waybill, Bulk Pincode) — many concurrent requests | Parallel I/O without threads |
| Creating multiple shipments in a batch | Fire concurrent creation calls |
| Polling tracking status for many waybills simultaneously | Fan-out reads in parallel |
| Already inside an async framework (FastAPI, aiohttp server) | Avoids blocking the event loop |

### 3.3 When Sync Is Perfectly Fine

| Scenario | Why Sync Is Fine |
|----------|-----------------|
| Single API calls (Edit, Cancel, single Tracking lookup) | One request-response — async adds complexity for no gain |
| CLI tools, scripts, cron jobs | No event loop, no concurrency needed |
| Django/Flask sync views handling one shipment at a time | Framework is sync — going async adds friction |
| Simple webhook handlers | Process one event at a time |

### 3.4 Implementation Guidance

- **Sync**: Use the user's existing HTTP client (`requests`, `httpx`, etc.). Wrap in a service function.
- **Async**: Use `httpx.AsyncClient` or `aiohttp.ClientSession`. Use `asyncio.gather()` for concurrent calls. Always use a session/client context manager.
- **Never mix**: Don't create async functions that internally use sync `requests`. Don't call `asyncio.run()` inside an already-async context.
- **Timeouts apply equally**: Whether sync or async, always configure request timeouts from config.

---

---

## 4. Input Validation

Validate ALL required parameters **before** making the API call to avoid unnecessary network round-trips.

### Common Validations

| Parameter Type | Validation Rule | Used By |
|----------------|----------------|---------|
| Pincodes | 6-digit numeric (100000–999999) | Pincode Serviceability, Bulk Pincode, Expected TAT, Shipment Creation, Warehouse Create/Edit |
| Waybill | Non-empty string | Tracking, Edit Shipment, Cancel Shipment, Packing Slip, E-Waybill Update, Document Download |
| Order ID | Max 50 characters | Shipment Creation, Edit Shipment |
| Phone numbers | Array of strings with valid prefixes: `91`, `+91`, `+91-`, `91-`, `0` | Shipment Creation, Edit Shipment, RVP QC |
| Dates (YYYY-MM-DD) | Parse with `datetime.strptime` or equivalent | Expected TAT (`expected_pickup_date`), Pickup Request (`pickup_date`) |
| Time (HH:MM:SS) | Validate format | Pickup Request (`pickup_time`) |
| Enumerations | Value must be in allowed set | Invoice Charges (`md`: E/S, `ss`: Delivered/RTO/DTO, `pt`: Pre-paid/COD), Packing Slip (`pdf_size`: A4/4R) |
| Numeric fields | Positive values, correct type (`float` vs `int`) | Edit Shipment (dimensions must be `float`), Invoice Charges (`cgm` must be `int`) |
| E-Waybill numbers | Valid pattern (12-digit) | E-Waybill Update (`ewbn` field) |
| Required string fields | Non-empty after trimming | Most APIs |

### Validation Rules Details

**Order ID**: Maximum 50 characters. Longer values will be rejected.

**Phone Number Prefixes**: The following prefixes are allowed:
- `91` (e.g., `919876543210`)
- `+91` (e.g., `+919876543210`)
- `+91-` (e.g., `+91-9876543210`)
- `91-` (e.g., `91-9876543210`)
- `0` (e.g., `09876543210`)

Return clear validation error messages that explain what was wrong and what is expected.

---

---

## 5. Special Request Format Requirements

### 5.1 Manifestation APIs (Shipment Creation, RVP QC)

**CRITICAL**: Manifestation APIs (Shipment Creation and RVP QC) require a special format prefix:

```
format=json&data=<JSON_PAYLOAD>
```

The request body must be URL-encoded with this exact prefix. The actual JSON payload goes after `data=`.

**Example**:
```
POST /api/cmu/create.json
Content-Type: application/x-www-form-urlencoded

format=json&data={"shipments":[{"name":"John Doe",...}]}
```

**Do NOT** send raw JSON for these APIs — it will be rejected.

### 5.2 Waybill Handling

**Auto-generation**: If you leave the `waybill` field blank in Shipment Creation or RVP QC, Delhivery will auto-generate a waybill number.

**Pre-fetching**: If you need to assign waybill numbers before creating shipments, use the Bulk Waybill API to fetch waybills in advance.

**Important**: Store pre-fetched waybills in your database. Do NOT fetch and immediately use them in the same request flow — there should be a separation between fetching and usage.

### 5.3 MPS (Multi-Piece Shipment)

**Use MPS only if** your order occupies more than one physical container/box.

**Do NOT use MPS** for single-box orders, even if the order contains multiple items. MPS is about physical containers, not item count.

### 5.4 QC Field (Quality Check)

The `custom_qc` field is **optional** and should **only be used for Reverse Pickups (RVP)**.

Do not include QC data for forward shipments unless specifically required.

---

## 6. Header Management

- Centralize header construction in a shared helper function.
- The helper should accept optional parameters for token override and authentication scheme.
- Always include `Content-Type: application/json` unless the API documentation specifies otherwise.
- Reuse the same helper across all API integrations.
- **Exception**: Bulk Waybill API does NOT use the Authorization header — token goes in query params.

---

## 7. Query Parameter Construction

- Build query parameters dynamically.
- Only include optional parameters when they have non-null, non-empty values.
- For parameters that accept multiple values (e.g., comma-separated waybills in Packing Slip), join the list into a single string before passing.

---

## 8. Request Body Construction (POST/PUT)

For POST and PUT requests, build the JSON body from all fields defined in the API spec:

- Include **all required fields** — these are mandatory.
- Include **optional fields** as configurable parameters with `None`/null defaults. Only add them to the payload if they have non-null values.
- **Do NOT skip fields** from the raw API spec — see §4.8 (Spec Fidelity) in the behavioral guide.

### Nested Structures

Some APIs have deeply nested payloads:

| API | Nesting |
|-----|---------|
| Shipment Creation | `shipments[].{fields}` + `pickup_location.name` |
| RVP QC | `shipments[].custom_qc[].questions[]` — 3 levels deep |
| E-Waybill Update | `data[].{dcn, ewbn}` |
| NDR Update | `data[].{waybill, act}` |

Build helpers for nested structures rather than constructing them inline.

---

## 9. Type-Specific Gotchas

### 8.1 Float vs Int
Some APIs require specific numeric types:
- **Edit Shipment**: Dimensions (`shipment_height`, `shipment_width`, `shipment_length`, `weight`) MUST be `float`, not `int`. Sending `int` causes error: `"volh must be an instance of float not int"`.
- **Invoice Charges**: Weight (`cgm`) should be `int` in grams.

### 8.2 Boolean as String
Some APIs expect string representations of booleans:
- **Cancel Shipment**: `cancellation` parameter must be string `"true"`, NOT boolean `true`.

### 8.3 Phone as Array
Multiple APIs expect phone numbers as arrays of strings:
- **Edit Shipment**: `phone: ["9876543210"]`
- **Shipment Creation**: `phone: ["9999999999"]`, `return_phone: []`
- **RVP QC**: `phone: ["1234567890"]`, `return_phone: ["1234567890"]`

Even for a single phone number, always wrap in an array.

### 8.4 Weight as String (RVP QC)
- **RVP QC**: `weight` is a string with unit: `"150.0 gm"` — unlike other APIs where weight is numeric.

### 8.5 String vs Integer for Pincodes
- **Expected TAT**: `origin_pin` and `destination_pin` must be **integers**, not strings.
- **Shipment Creation**: `pin` must be **integer**.
- **Pincode Serviceability**: `filter_codes` is a **string** (query parameter).

---

## 10. Implementation Guidance

When helping a developer construct requests:

1. Check if they have an existing HTTP client wrapper or request builder.
2. If yes, extend it with Delhivery-specific logic.
3. If no, suggest a simple helper that handles URL construction, header setup, and parameter building.
4. Always add input validation before the API call — but place it where the user's codebase would expect it (in the service layer, in a validator, etc.).
5. For PUT requests (E-Waybill Update), make sure the HTTP client method is explicitly set to PUT.
