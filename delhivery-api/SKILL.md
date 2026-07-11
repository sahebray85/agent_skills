---
name: delhivery-api
description: Implement, integrate, and debug any of the 18 Delhivery B2C Logistics APIs (shipment creation, tracking, pickup, warehouse, NDR, packing slip, e-waybill, etc.) using the Delhivery MCP server. Use when user mentions Delhivery, wants to integrate logistics APIs, ship parcels, track shipments, handle NDR, generate waybills, check pincode serviceability, create/edit warehouses, or troubleshoot Delhivery API errors. Also use when user mentions forward journey, reverse journey, RVP QC, or courier integration.
---

# Delhivery API Skill

## Source of Truth Hierarchy

> Official portal docs are the **authoritative source**. The local `docs/` directory in this skill is a
> pre-fetched cache of the MCP server's content and is the **default reference** — read it directly with
> the `Read` tool, no permission or MCP call needed. Use in this order:
>
> 1. **Official Portal** — `https://one.delhivery.com/developer-portal/documents/b2c` _(login required)_
> 2. **Local `docs/` directory** (this skill folder) — `docs/api/<api_name>.md`, `docs/common/<topic>.md`,
>    `docs/workflows/<flow_type>.md`. Read these directly by default — they mirror the MCP tool outputs.
> 3. **MCP tools** — only if a local doc is missing the needed detail, or appears stale/incomplete for the
>    question at hand
> 4. **`web_search`** — last resort only for undocumented edge cases not covered by portal, local docs, or MCP

### Portal Access Workflow
The portal is a JavaScript SPA behind authentication — it **cannot be fetched programmatically**.

- **When portal content is needed**: Ask the user to navigate to the portal, find the relevant API doc, and paste the content into the chat.
- **When user provides portal content**: That content **overrides everything** in local docs/MCP — use it without question.
- **Discrepancy rule**: If portal and local docs/MCP disagree, use the portal version and add a `// NOTE: portal overrides MCP on <field>` comment in code.
- **When portal is unavailable**: Use the local `docs/` directory transparently — no need to mention the portal or ask permission.

## MCP Tools Available (fallback only — prefer local `docs/` above)

| Tool | When to Use |
|------|-------------|
| `delhivery_mcp-list_available_apis` | FIRST call — confirms all 18 APIs and 3 workflows |
| `delhivery_mcp-get_api_documentation(api_name)` | Implementing a specific API (spec, auth, quirks, checklist) |
| `delhivery_mcp-get_diagnostic_info(api_name)` | Debugging an error on a specific API |
| `delhivery_mcp-get_integration_guide(flow_type)` | Broad integration planning (`forward_journey`, `reverse_journey`, `overview`) |
| `delhivery_mcp-get_doc(category, topic)` | Load a specific doc: auth, errors, config, logging, request_construction |

## 18 Available APIs

| API Name | Use Case |
|----------|----------|
| `shipment_creation` | Create forward shipments |
| `tracking` | Track packages by waybill |
| `pickup_request` | Schedule pickup (mandatory for forward) |
| `cancel_shipment` | Cancel a shipment |
| `edit_shipment` | Edit shipment details post-creation |
| `warehouse_create` | Register a new warehouse |
| `warehouse_edit` | Update warehouse details |
| `pincode_serviceability` | Check if a pincode is serviceable |
| `bulk_pincode` | Bulk pincode serviceability check |
| `bulk_waybill` | Generate waybill numbers in bulk |
| `packing_slip` | Download packing slip / label PDF |
| `document_download` | Download shipment documents |
| `invoice_charges` | Calculate shipping cost — pre-shipment estimation (portal name: "Calculate Shipping Cost") AND post-shipment invoice/charge reconciliation. Same endpoint, same params (`md`, `cgm`, `o_pin`, `d_pin`, `ss`, `pt`, `l`, `b`, `h`, `ipkg_type`) for both use cases. |
| `expected_tat` | Get estimated delivery TAT |
| `ndr_update` | Respond to Non-Delivery Reports |
| `ndr_status` | Check NDR bulk upload status |
| `ewaybill_update` | Update e-waybill on a shipment |
| `rvp_qc` | Create reverse shipments with QC |

## Workflow: Implementing an API

```
1. Check if user provided portal doc content → use it as-is (highest priority)
2. Read docs/api/<api_name>.md                         ← full spec + quirks (default, no MCP needed)
3. Read docs/common/auth.md                            ← auth patterns
4. Read docs/common/errors.md                          ← error handling
5. Read docs/common/config.md                          ← URL + timeout config
6. Implement following docs/common/checklist.md
(Only fall back to delhivery_mcp-get_api_documentation(api_name) / get_doc if the local doc is missing something)
```

## Workflow: Debugging an Error

```
1. Read docs/api/<api_name>.md and docs/common/errors.md  ← error patterns + quirks
2. Match the error against the error table in the doc
3. Apply the recommended fix (do NOT retry business logic errors)
(Fall back to delhivery_mcp-get_diagnostic_info(api_name) only if local docs don't cover the error)
```

## Workflow: Planning Full Integration

```
1. Read docs/workflows/forward_journey.md or reverse_journey.md (or overview.md)
2. Follow the API dependency chain in the guide
3. Implement each API in dependency order
(Fall back to delhivery_mcp-get_integration_guide(flow_type) only if local docs are insufficient)
```

## Critical Rules (Always Apply)

- **Auth prefix**: Use `Token <value>` NOT `Bearer` (except Expected TAT which uses Bearer JWT)
- **Bulk Waybill**: token is a **query param**, not a header
- **200 ≠ success**: Always check response body for `success: false` or `status: "Failure"`
- **Batch APIs**: Iterate each item's status — top-level success doesn't cover all items
- **Rate limit**: 750 req/5min — pause 30s on 403
- **Base URL**: Always from config (`DELHIVERY_BASE_URL`), never hardcoded
- **Warehouse prerequisite**: Register warehouse BEFORE creating shipments
- **PUR mandatory**: Forward shipments require a Pickup Request; reverse = auto-scheduled
- **Shared endpoints**: Cancel & Edit both use `/api/p/edit`; Shipment Creation & RVP QC both use `/api/cmu/create.json`

## Environments

| Env | Base URL |
|-----|----------|
| Staging | `https://staging-express.delhivery.com` |
| Production | `https://track.delhivery.com` |

See [REFERENCE.md](REFERENCE.md) for all endpoint paths, timeout table, and retry strategy.
