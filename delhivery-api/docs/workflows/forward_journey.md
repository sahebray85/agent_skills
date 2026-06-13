# Forward Journey — End-to-End Workflow

> **Scope**: Detailed workflow for the forward shipment journey (seller → consumer). Load this when a user wants to understand or implement the complete forward shipping flow.

---

## Workflow

```
┌─────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│ 1. Setup    │──▶│ 2. Pre-Ship  │──▶│ 3. Ship & Pick │──▶│ 4. In Transit│
│             │   │              │   │                │   │              │
│ • API Key   │   │ • Waybill    │   │ • Create Order │   │ • Track      │
│ • Warehouse │   │ • Pin Check  │   │ • E-Waybill    │   │ • Notify     │
│             │   │ • Cost Est.  │   │ • Label Print  │   │              │
│             │   │              │   │ • Pickup Req   │   │              │
└─────────────┘   └──────────────┘   └────────────────┘   └──────────────┘
                                                                │
                                                                ▼
                                          ┌──────────────────────────────┐
                                          │ 5. Delivery / Exception      │
                                          │                              │
                                          │ • Delivered → POD / Docs     │
                                          │ • Failed → NDR → Reattempt   │
                                          │ • Returned → RTO             │
                                          │ • Lost                       │
                                          └──────────────────────────────┘
```

---

## Phase 1: Setup (One-Time)

| Step | API | Action |
|------|-----|--------|
| Get API Key | — | Obtain from Delhivery POC or One Panel: Settings > API Setup > Existing API Token |
| Register Warehouse | Warehouse Create API | Register pickup location with address, contact, and operational details |
| Update Warehouse | Warehouse Edit API | Update existing pickup location details if needed |

---

## Phase 2: Pre-Shipment (Per Order)

| Step | API | Action |
|------|-----|--------|
| Check Serviceability | Pincode Serviceability API | Verify destination pincode is serviceable. Check for embargo (`"emargo"`). |
| Get TAT Estimate | Expected TAT API | Get estimated delivery days between origin-destination pincode pair. |
| Get Shipping Cost | Invoice Charges API | Estimate charges based on weight, dimensions, origin, destination, payment type. |
| Generate Waybill | Bulk Waybill API | *Optional* — pre-generate tracking numbers if required by your workflow. |

---

## Phase 3: Shipment Creation & Pickup

| Step | API | Action |
|------|-----|--------|
| Create Shipment | Shipment Creation API | Create the shipment order with consignee details, products, dimensions. |
| Edit (if needed) | Edit Shipment API | Update consignee info, payment mode, dimensions after creation. |
| Cancel (if needed) | Cancel Shipment API | Cancel before dispatch if order is cancelled. |
| E-Waybill (if needed) | E-Waybill Update API | Update e-waybill and invoice numbers for shipments with value ≥ ₹50k. |
| Generate Label | Packing Slip API | Generate and print shipping label. Attach to package. |
| Request Pickup | Pickup Request API | Request Delhivery to pick up packages from warehouse. |

---

## Phase 4: In Transit

| Step | API | Action |
|------|-----|--------|
| Track Shipment | Package Tracking API | Poll for status updates. Get scan history and current status. |
| Invoice | Invoice Charges API | Get actual shipping charges for billing reconciliation. |

---

## Phase 5: Delivery / Exception

| Outcome | API | Next Action |
|---------|-----|-------------|
| **Delivered** | Document Download API | Download POD (proof of delivery), signatures, EPOD, QC images. |
| **Delivery Failed (NDR)** | NDR Update API | Submit re-attempt or pickup reschedule action. |
| **Check NDR Result** | NDR Status API | Check per-waybill success/failure of the NDR update. |
| **Returned (RTO)** | Package Tracking API | Monitor return shipment back to seller via tracking. |
| **Lost** | — | Flag as exception. Contact Delhivery support. |

---

## API Dependency Chain

```
API Key (required for everything)
  └─▶ Warehouse Create (register pickup location — one-time setup)
  └─▶ Pincode Serviceability (validate before creating shipment)
  └─▶ Expected TAT (inform customer of delivery estimate)
  └─▶ Invoice Charges (estimate shipping cost)
  └─▶ Bulk Waybill (optional, for pre-assigned waybills)
       └─▶ Shipment Creation (requires valid pincode, optionally pre-assigned waybill)
            └─▶ Edit Shipment (modify after creation)
            └─▶ Cancel Shipment (cancel before dispatch)
            └─▶ E-Waybill Update (for shipments ≥ ₹50k)
            └─▶ Packing Slip (generate label for created shipment)
            └─▶ Pickup Request (schedule pickup)
                 └─▶ Package Tracking (track after pickup)
                      └─▶ Document Download (fetch POD, signatures, QC images)
                      └─▶ NDR Update (re-attempt failed deliveries)
                           └─▶ NDR Status (check NDR update results)
                      └─▶ Invoice Charges (billing after delivery)
```
