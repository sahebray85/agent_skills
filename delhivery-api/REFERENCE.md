# Delhivery API — Reference

## Official Documentation

| Source | URL | Notes |
|--------|-----|-------|
| **Developer Portal** | `https://one.delhivery.com/developer-portal/documents/b2c` | **Authoritative**. Requires login. Navigate sidebar to find each API. |
| MCP Tools | See `SKILL.md` | Pre-built cache. Use when portal is unavailable. |

> **Auth-gate note**: The portal is a Vue SPA that requires an active Delhivery account login.
> It cannot be fetched by an agent. To use portal content: open it in your browser, navigate to the
> relevant API page, and paste the documentation into the chat. Portal content overrides MCP.

---

## Naming Note: "Calculate Shipping Cost" vs "Invoice Charges"

The Delhivery portal documents the **same API** (`GET /api/kinko/v1/invoice/charges/.json`) under two different page names depending on use case:

- **"Calculate Shipping Cost"** — pre-shipment estimation (before creating a shipment, to show the customer an estimated delivery fee)
- **"Invoice Charges"** — post-shipment reconciliation (after delivery, to fetch actual/final charges)

Both use identical parameters (`md`, `cgm`, `o_pin`, `d_pin`, `ss`, `pt`, `l`, `b`, `h`, `ipkg_type`) and the same response schema. Do not treat these as two separate APIs — implement once under `invoice_charges`.

---

## All Endpoint Paths

| API | Method | Path |
|-----|--------|------|
| Pincode Serviceability | GET | `/c/api/pin-codes/json/` |
| Bulk Client Pincode | GET | `/c/api/pin-codes/json/` |
| Edit Shipment | POST | `/api/p/edit` |
| Cancel Shipment | POST | `/api/p/edit` (add `cancellation: "true"`) |
| NDR Update | POST | `/api/p/update` |
| Bulk Waybill | GET | `/waybill/api/bulk/json/` |
| Package Tracking | GET | `/api/v1/packages/json/` |
| Invoice Charges (aka "Calculate Shipping Cost" on portal) | GET | `/api/kinko/v1/invoice/charges/.json` |
| Packing Slip | GET | `/api/p/packing_slip` |
| Expected TAT | GET | `/api/dc/expected_tat` |
| Pickup Request | POST | `/fm/request/new/` |
| Shipment Creation | POST | `/api/cmu/create.json` |
| RVP QC | POST | `/api/cmu/create.json` (use `custom_qc` payload) |
| NDR Status | GET | `/api/cmu/get_bulk_upl/{request_id}` |
| Warehouse Create | POST | `/api/backend/clientwarehouse/create/` |
| Warehouse Edit | POST | `/api/backend/clientwarehouse/edit/` |
| Document Download | GET | `/api/rest/fetch/pkg/document/` |
| E-Waybill Update | PUT | `/api/rest/ewaybill/{waybill}/` |

---

## Timeout Defaults

| Category | APIs | Timeout |
|----------|------|---------|
| Fast lookups | Pincode Serviceability, Bulk Pincode, Expected TAT | 10s |
| Standard CRUD | Edit, Cancel, Pickup Request, Warehouse, E-Waybill, NDR Update | 10s |
| Shipment creation | Shipment Creation, RVP QC | 15s |
| Data retrieval | Tracking, Invoice, NDR Status, Document Download | 15s |
| Bulk generation | Bulk Waybill | 15s |
| PDF generation | Packing Slip | 20s |

---

## Authentication Summary

| API | Scheme | Location |
|-----|--------|----------|
| Most APIs | `Token <value>` | `Authorization` header |
| Expected TAT | `Bearer <JWT>` | `Authorization` header |
| Bulk Waybill | `token=<value>` | Query parameter |

```
# Standard header
Authorization: Token YOUR_TOKEN
Content-Type: application/json
Accept: application/json
```

---

## Retry Strategy

| Status | Retryable? | Action |
|--------|------------|--------|
| 200 (check body) | No | Inspect body for `success: false` |
| 400 | Never | Fix the input |
| 401 | Never (same token) | Refresh token |
| 403 | Yes (after 30s) | Rate limit / WAF — pause then retry |
| 5xx | Yes (backoff) | 3 attempts: 1s → 2s → 4s |
| Timeout | Yes (backoff) | Same as 5xx |

---

## Business Logic Error Indicators

| API | Failure Field |
|-----|---------------|
| Edit Shipment | `status: "Failure"` + `error` |
| Tracking | `Success: false` |
| Expected TAT | `success: false` + `msg` |
| Cancel Shipment | check `status: true/false` |
| Shipment Creation | `success: false` + `rmk` |
| RVP QC | per-package `status: "Fail"` |
| Document Download | `success: false` + `message` |
| E-Waybill Update | `success: false` + `message` |
| NDR Status | `status: "Failure"` + `remark` |
| Pickup Request | `400` with field-level error object |

---

## Critical Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `NoneType...end_date` | Token/env mismatch | Use staging token with staging URL |
| `ClientWarehouse matching query does not exist` | Warehouse not registered | Register warehouse first |
| `1100** is non serviceable` | Account type mismatch | Check B2C vs Heavy account |
| `Suspicious order` | Consignee flagged | Contact Delhivery Business POC |
| `EOD-777` | RVP QC fail | Use `PICKUP_RESCHEDULE` action |
| `Volume exceeded` | Pickup capacity hit | Schedule for next day |

---

## Forward Journey — API Dependency Order

```
1. Warehouse Create (once, prerequisite)
2. Pincode Serviceability (check deliverability)
3. Bulk Waybill (reserve waybill numbers)
4. Shipment Creation (create the shipment)
5. Pickup Request (schedule collection — mandatory)
6. Packing Slip / Document Download (print labels)
7. Tracking (monitor delivery)
8. NDR Update (handle failed delivery)
9. Invoice Charges (reconcile billing)
```

## Reverse Journey — API Dependency Order

```
1. Pincode Serviceability (check pickup location)
2. RVP QC (create reverse shipment — auto-schedules pickup)
3. Tracking (monitor return)
4. Document Download (documents if needed)
```

---

## Config Variables (.env.example)

```bash
# Environment
DELHIVERY_BASE_URL=https://staging-express.delhivery.com
# Production: https://track.delhivery.com

# Auth
DELHIVERY_TOKEN=your_token_here
DELHIVERY_JWT_TOKEN=your_jwt_for_tat_api  # Expected TAT only

# Timeouts (seconds)
DELHIVERY_TIMEOUT_DEFAULT=10
DELHIVERY_TIMEOUT_SHIPMENT=15
DELHIVERY_TIMEOUT_PDF=20

# Retry
DELHIVERY_MAX_RETRIES=3
DELHIVERY_INITIAL_BACKOFF=1.0
DELHIVERY_BACKOFF_MULTIPLIER=2.0
```
