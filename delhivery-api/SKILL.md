---
name: delhivery-api
description: Implement, integrate, and debug any of the 18 Delhivery B2C Logistics APIs (shipment creation, tracking, pickup, warehouse, NDR, packing slip, e-waybill, etc.) using the Delhivery MCP server. Use when user mentions Delhivery, wants to integrate logistics APIs, ship parcels, track shipments, handle NDR, generate waybills, check pincode serviceability, create/edit warehouses, or troubleshoot Delhivery API errors. Also use when user mentions forward journey, reverse journey, RVP QC, or courier integration.
---

# Delhivery API Skill

## Source of Truth Hierarchy

> Official portal docs are the **authoritative source**. MCP is a pre-built cache. Use in this order:
>
> 1. **Official Portal** — `https://one.delhivery.com/developer-portal/documents/b2c` _(login required)_
> 2. **MCP tools** — use when portal is not accessible (default path since portal is auth-gated)
> 3. **`web_search`** — last resort only for undocumented edge cases not covered by portal or MCP

### Portal Access Workflow
The portal is a JavaScript SPA behind authentication — it **cannot be fetched programmatically**.

- **When portal content is needed**: Ask the user to navigate to the portal, find the relevant API doc, and paste the content into the chat.
- **When user provides portal content**: That content **overrides everything** in MCP — use it without question.
- **Discrepancy rule**: If portal and MCP disagree, use the portal version and add a `// NOTE: portal overrides MCP on <field>` comment in code.
- **When portal is unavailable**: Fall back to MCP tools transparently — no need to mention the portal.

## MCP Tools Available

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
2. delhivery_mcp-get_api_documentation(api_name)      ← full spec + quirks (default)
3. delhivery_mcp-get_doc("common", "auth")             ← auth patterns
4. delhivery_mcp-get_doc("common", "errors")           ← error handling
5. delhivery_mcp-get_doc("common", "config")           ← URL + timeout config
6. Implement following the checklist in the API doc
```

## Workflow: Debugging an Error

```
1. delhivery_mcp-get_diagnostic_info(api_name)         ← error patterns + quirks
2. Match the error against the error table in the doc
3. Apply the recommended fix (do NOT retry business logic errors)
```

## Workflow: Planning Full Integration

```
1. delhivery_mcp-get_integration_guide("forward_journey")   ← or "reverse_journey"
2. Follow the API dependency chain in the guide
3. Implement each API in dependency order
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
