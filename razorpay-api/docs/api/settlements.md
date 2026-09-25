# Settlements toolset

> **When to load**: when/what money reached the bank account, reconciling payments, refunds and fees
> against a settlement, or instant (on-demand) settlements.

## Usage notes

- `fetch_all_settlements` / `fetch_settlement_with_id` (`setl_…`) → amount, fees, tax, UTR, status.
- `fetch_settlement_recon_details` (`GET /v1/settlements/recon/combined`, `year` + `month`
  [+ `day`]) → row-level report linking each payment/refund/adjustment to its settlement. This is the
  tool for "which payments were in settlement X" and "why is the credit less than sales".
- `create_instant_settlement` is **local-server only**; min 200 paise; `settle_full_balance: true`
  ignores `amount`; `description` ≤ 30 alphanumeric chars. Moves money — confirm with the user first.
- Instant settlement IDs are `setlod_…` and live under `/v1/settlements/ondemand`; `expand:
  ["ondemand_payouts"]` includes payout legs.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `fetch_settlement_with_id`

**Read** · remote ✅ · `GET /v1/settlements/{id}`

> Fetch details of a specific settlement using its ID

| Param | Type | Constraints | Description |
|---|---|---|---|
| `settlement_id` | string | REQUIRED | The ID of the settlement to fetch.ID starts with the 'setl_' |

## `fetch_settlement_recon_details`

**Read** · remote ✅ · `GET /v1/settlements/recon/combined`

> Fetch settlement reconciliation report for a specific time period

| Param | Type | Constraints | Description |
|---|---|---|---|
| `year` | number | REQUIRED | Year for which the settlement report is requested (YYYY format) |
| `month` | number | REQUIRED | Month for which the settlement report is requested (MM format) |
| `day` | number | — | Optional: Day for which the settlement report is requested (DD format) |
| `count` | number | — | Optional: Number of records to fetch (default: 10, max: 100) |
| `skip` | number | — | Optional: Number of records to skip for pagination |

## `fetch_all_settlements`

**Read** · remote ✅ · `GET /v1/settlements`

> Fetch all settlements with optional filtering and pagination

| Param | Type | Constraints | Description |
|---|---|---|---|
| `count` | number | Min=1; Max=100 | Number of settlement records to fetch (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of settlement records to skip (default: 0) |
| `from` | number | Min=0 | Unix timestamp (in seconds) from when settlements are to be fetched |
| `to` | number | Min=0 | Unix timestamp (in seconds) up till when settlements are to be fetched |

## `create_instant_settlement`

**Write** · remote ❌ · `POST /v1/settlements/ondemand`

> Create an instant settlement to get funds transferred to your bank account

| Param | Type | Constraints | Description |
|---|---|---|---|
| `amount` | number | REQUIRED; Min=200 | The amount you want to get settled instantly in paise (smallest currency sub-unit). For INR: 100 paise = ₹1. Example: for ₹295, use 29500 |
| `settle_full_balance` | boolean | DefaultValue=false | If true, Razorpay will settle the maximum amount possible and ignore amount parameter |
| `description` | string | Max=30; Pattern="^[a-zA-Z0-9 ]*$" | Custom note for the instant settlement. |
| `notes` | object | MaxProperties=15 | Key-value pairs for additional information. Max 15 pairs, 256 chars each |

## `fetch_all_instant_settlements`

**Read** · remote ✅ · `GET /v1/settlements/ondemand`

> Fetch all instant settlements with optional filtering, pagination, and payout details

| Param | Type | Constraints | Description |
|---|---|---|---|
| `count` | number | Min=1; Max=100 | Number of instant settlement records to fetch (default: 10, max: 100) |
| `skip` | number | Min=0 | Number of instant settlement records to skip (default: 0) |
| `from` | number | Min=0 | Unix timestamp (in seconds) from when instant settlements are to be fetched |
| `to` | number | Min=0 | Unix timestamp (in seconds) up till when instant settlements are to be fetched |
| `expand` | array | — | Pass this if you want to fetch payout details as part of the response for all instant settlements. Supported values: ondemand_payouts |

## `fetch_instant_settlement_with_id`

**Read** · remote ✅ · `GET /v1/settlements/ondemand/{id}`

> Fetch details of a specific instant settlement using its ID

| Param | Type | Constraints | Description |
|---|---|---|---|
| `settlement_id` | string | REQUIRED | The ID of the instant settlement to fetch. ID starts with 'setlod_' |
