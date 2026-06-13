# Configuration Management — Common Patterns

> **Scope**: Configuration patterns shared across ALL Delhivery B2C APIs. Load this when writing integration code.

---

## 1. Core Principle

**Separate ALL configuration from application code.** Every value that could change between environments or deployments must come from configuration, not hardcoded literals.

---

## 2. Base URL Management

### 2.1 Available Environments

| Environment | Base URL | Purpose |
|-------------|----------|---------|
| Production | `https://track.delhivery.com` | Live traffic |
| Staging | `https://staging-express.delhivery.com` | Development and testing |

**Note**: Some APIs use `https://express.delhivery.com` as their production URL (e.g., Pickup Request). Check the raw OpenAPI spec for each API. However, `https://track.delhivery.com` is the most common production base.

### 2.2 Base URL MUST Come from Config

**CRITICAL**: The base URL must ALWAYS be loaded from configuration — never hardcoded and never chosen via code logic. The deployment environment (dev/staging/prod) determines which config is loaded, and the code simply reads the value.

```
# The code always reads from one config variable:
base_url = os.getenv("DELHIVERY_BASE_URL")
# OR
base_url = config.BASE_URL
```

The **env file or config file** for each environment sets the correct value:
```
# .env.staging
DELHIVERY_BASE_URL=https://staging-express.delhivery.com

# .env.production
DELHIVERY_BASE_URL=https://track.delhivery.com
```

Do NOT ask the user "staging or production?" — the code should work for both by reading from config. Provide both URLs in comments or `.env.example` so the user knows what to set for each environment.

### 2.3 URL Construction

Store the base URL and API paths separately. Construct the full URL at runtime:

```
base_url = config.BASE_URL           # From env/config — NOT hardcoded
path     = config.TRACKING_API_PATH  # "/api/v1/packages/json/"
full_url = base_url + path           # Combined at runtime
```

---

## 3. Path Management

Store each API endpoint path as a configuration constant:

| API | Method | Path |
|-----|--------|------|
| Pincode Serviceability | GET | `/c/api/pin-codes/json/` |
| Bulk Client Pincode | GET | `/c/api/pin-codes/json/` (same as above — client-scoped) |
| Edit Shipment | POST | `/api/p/edit` |
| Cancel Shipment | POST | `/api/p/edit` (same as Edit — distinguished by `cancellation: "true"`) |
| NDR Update | POST | `/api/p/update` |
| Bulk Waybill | GET | `/waybill/api/bulk/json/` |
| Package Tracking | GET | `/api/v1/packages/json/` |
| Invoice Charges | GET | `/api/kinko/v1/invoice/charges/.json` |
| Packing Slip | GET | `/api/p/packing_slip` |
| Expected TAT | GET | `/api/dc/expected_tat` |
| Pickup Request (PUR) | POST | `/fm/request/new/` |
| Shipment Creation | POST | `/api/cmu/create.json` |
| RVP QC (Reverse Shipment) | POST | `/api/cmu/create.json` (same as Shipment Creation — distinguished by `custom_qc` payload) |
| NDR Status / Bulk Upload Status | GET | `/api/cmu/get_bulk_upl/{request_id}` |
| Warehouse Create | POST | `/api/backend/clientwarehouse/create/` |
| Warehouse Edit | POST | `/api/backend/clientwarehouse/edit/` |
| Document Download | GET | `/api/rest/fetch/pkg/document/` |
| E-Waybill Update | PUT | `/api/rest/ewaybill/{waybill}/` |

**Shared endpoints to note**:
- `/api/p/edit` is used by both Edit Shipment and Cancel Shipment.
- `/api/cmu/create.json` is used by both Shipment Creation and RVP QC.
- `/c/api/pin-codes/json/` is used by both Pincode Serviceability and Bulk Client Pincode.

---

## 4. Timeout Configuration

Set configurable timeouts for each API. Since exact p99 latency data is not available, use these **sensible defaults** and tune based on your own observations:

| Category | APIs | Recommended Default Timeout |
|----------|------|-----------------------------|
| **Fast lookups** | Pincode Serviceability, Bulk Client Pincode, Expected TAT | 10s |
| **Standard CRUD** | Edit Shipment, Cancel Shipment, Pickup Request, Warehouse Create/Edit, E-Waybill Update, NDR Update | 10s |
| **Shipment creation** | Shipment Creation, RVP QC | 15s |
| **Data retrieval** | Package Tracking, Invoice Charges, NDR Status, Document Download | 15s |
| **Bulk generation** | Bulk Waybill | 15s |
| **PDF generation** | Packing Slip | 20s (PDF generation is inherently slower) |

**Rules**:
- Read timeout from configuration — never hardcode.
- Start with the defaults above and adjust based on production observations.
- Set a global default timeout (e.g., 10s) and override per-API only where needed.
- Packing Slip (PDF mode) needs the highest timeout — S3 signed URL generation takes longer.

---

## 5. Secrets Management

1. **Never** commit tokens, API keys, or credentials to source control.
2. Use environment variables or a secrets manager.
3. Provide a `.env.example` or similar file documenting which variables are needed without exposing real values.

---

## 6. Warehouse & Pickup Prerequisites

### 6.1 Warehouse Registration

**CRITICAL**: Warehouses must exist in Delhivery's system (via CDP/One Panel or Warehouse Creation API) **before** you can create shipments from that location.

**Error if missing**: Attempting to create a shipment with an unregistered warehouse will result in:
```
"ClientWarehouse matching query does not exist."
```

**Solution**: 
1. Register the warehouse using the Warehouse Creation API
2. Or have it created via the Delhivery One Panel
3. Wait for confirmation before attempting shipment creation

### 6.2 Pickup Request (PUR) Requirements

**Forward shipments**: Pickup Request (PUR) is **mandatory**. You must create a PUR for Delhivery's operations team to schedule pickup.

**Reverse shipments**: PUR is **auto-scheduled** by Delhivery. You do not need to create a manual PUR.

**PUR Date Constraints**:
- **Cannot be in the past**: The pickup date must be today or a future date
- **Maximum advance**: PUR date must be within +7 days of creation
- **Example**: If today is Jan 1, you can schedule pickups from Jan 1 to Jan 8

**Capacity Limits**: 
- "Volume exceeded" errors indicate you've hit the daily pickup capacity limit
- These limits reset at midnight
- If you encounter this error, schedule the pickup for the next day

---

## 7. Implementation Guidance

When helping a developer set up configuration:

1. Check how they currently manage configuration (env vars, config files, secrets manager).
2. Follow their existing pattern.
3. Add Delhivery-specific variables to their existing config structure.
4. If they have no config pattern, suggest the simplest approach that works for their project (typically env vars + a config module).
