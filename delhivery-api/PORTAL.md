# Delhivery Developer Portal — Navigation Guide

## Portal URL

```
https://one.delhivery.com/developer-portal/documents/b2c
```

**Authentication required** — you must be logged in with a Delhivery account.

---

## Why the Agent Can't Access It Directly

The portal is a JavaScript SPA (Vue.js). Programmatic `web_fetch` returns only the HTML shell
(`<div id="app">`). The documentation content is loaded by the browser after authentication.

**The agent will ask you to paste relevant doc sections** when it needs portal content.

---

## How to Share Portal Content With the Agent

1. Log in at `https://one.delhivery.com`
2. Navigate to **Developer Portal → B2C Documentation**
3. Find the API you need in the left sidebar
4. Select all text in the main content area (`Ctrl+A` then `Ctrl+C`)
5. Paste into the chat with a prompt like:
   > "Here is the portal doc for shipment creation: [paste content]"

The agent will use this as the authoritative source, overriding any MCP content for that API.

---

## Portal Sidebar Navigation — 18 APIs

| Portal Section | API Name (MCP) |
|----------------|----------------|
| Shipment Creation | `shipment_creation` |
| Package Tracking | `tracking` |
| Pickup Request | `pickup_request` |
| Cancel Shipment | `cancel_shipment` |
| Edit Shipment | `edit_shipment` |
| Reverse Pickup (RVP QC) | `rvp_qc` |
| NDR Action | `ndr_update` |
| NDR Status | `ndr_status` |
| Warehouse Create | `warehouse_create` |
| Warehouse Edit | `warehouse_edit` |
| Pincode Serviceability | `pincode_serviceability` |
| Bulk Pincode | `bulk_pincode` |
| Bulk Waybill | `bulk_waybill` |
| Packing Slip | `packing_slip` |
| Document Download | `document_download` |
| Invoice & Charges | `invoice_charges` |
| Expected TAT | `expected_tat` |
| E-Waybill Update | `ewaybill_update` |

---

## Discrepancy Resolution

When portal content and MCP content differ:

1. **Portal wins** — always. No debate.
2. Update the implementation to match the portal.
3. Add a comment in code:
   ```java
   // NOTE: portal overrides MCP — field 'xyz' is String "true" per portal docs, not boolean
   ```
4. If the discrepancy is significant (e.g., different endpoint, field type), mention it to the user
   so the MCP can be updated accordingly.

---

## Common Reasons MCP and Portal May Differ

- **Field types**: MCP may document `boolean` where portal uses `"true"/"false"` strings
- **Endpoint paths**: Some APIs have different staging vs. production paths
- **New APIs**: Portal may have APIs added after the MCP snapshot was taken
- **Auth method**: Portal is always up to date; MCP may lag on auth changes
