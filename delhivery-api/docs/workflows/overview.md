# B2C Logistics Overview — Terminology, Lifecycle, & Integration Steps

> **Scope**: Foundational knowledge about Delhivery's B2C Transportation APIs. Load this when the user needs orientation on what APIs exist, how they relate to each other, and what order to integrate them.

---

## 1. What is the B2C Transportation API Suite?

Delhivery's B2C API suite enables businesses to manage end-to-end consumer delivery logistics — from order creation through delivery to potential return. The platform covers First-Mile Pickup, Mid-Mile Connectivity, and Last-Mile Delivery.

**Target users**: E-commerce platforms, retailers, and businesses handling high volumes of consumer shipments across India.

---

## 2. Terminology Glossary

| Term | Definition |
|------|-----------|
| **Waybill** | Unique tracking number assigned to each physical box. Also called AWB (Air Waybill). |
| **Master Waybill** | In a Multi-Piece Shipment (MPS), one waybill is the master, the rest are child waybills. |
| **E-Waybill** | Electronic document required in India under GST for movement of goods with invoice value > ₹50,000. |
| **Pickup Location** | Client's warehouse from where shipments are picked up by Delhivery field executive. |
| **API Token** | Static authentication token for B2C API requests. Obtained from Delhivery POC or One Panel. |
| **POD** | Proof of Delivery — document or electronic confirmation (signature, image) that consignee received the shipment. |
| **MPS** | Multi-Piece Shipment — a single order comprising multiple physical packages. |
| **HQ Name** | Delhivery Registered Account Name. |
| **RVP** | Reverse Pickup — collecting a shipment from the consignee (e.g., for returns). |
| **REPL** | Replacement — simultaneous forward delivery and reverse pickup for product exchange. |
| **NSZ** | Non-Serviceable Zone — center code indicating the pincode is not serviceable. |
| **ODA** | Out of Delivery Area — pincode is serviceable but may incur extra charges or delays. |
| **COD** | Cash on Delivery — consignee pays upon receiving the shipment. |

---

## 3. Package Lifecycle

### 3.1 Journey Types

| Journey | Description |
|---------|-------------|
| **Forward** | Shipment moves from seller's warehouse → consumer's doorstep via first-mile pickup, transit, and last-mile delivery. |
| **Return** | Shipment could not be delivered (incorrect address, recipient unavailable, order cancelled) — rerouted back to seller's warehouse. |
| **Reverse (RVP)** | Customer-initiated return — shipment collected from consignee and shipped back to seller. |
| **Replacement / Buyback** | Customer requests replacement — new product delivered to customer while original is picked up simultaneously. Involves both forward and reverse flows. |

### 3.2 Key Stages

| Stage | Name | Description |
|-------|------|-------------|
| 1 | **Order Creation** | Shipment order created via API or Delhivery ONE Panel. |
| 2 | **First-Mile Pickup** | Package picked up from seller's warehouse or designated location. |
| 3 | **Mid-Mile Transit** | Package moves through Delhivery's hub network toward the delivery city. |
| 4 | **Last-Mile Delivery** | Final delivery to the consumer's doorstep. |
| 5 | **Return Process** | If delivery fails, package rerouted back through transit phases to origin. |
| 6 | **Lost** | Shipment lost during transit (exception case). |

---

## 4. Payment Modes

| Mode | Description | When Used |
|------|-------------|-----------|
| **Prepaid** | Consignee pays upfront at time of purchase. | Most e-commerce orders. |
| **COD (Cash on Delivery)** | Consignee pays upon delivery. | When buyer prefers to pay at doorstep. |
| **Pickup** | For Reverse (RVP) shipments — shipment picked from consignee. | Customer-initiated returns. |
| **REPL (Replacement)** | For replacement orders — simultaneous forward + reverse. | Product exchanges. |

---

## 5. Integration Steps (Recommended Order)

Follow this order when integrating Delhivery APIs. Present this to the user and let them pick which APIs they need.

| Step | Name | API | Description |
|------|------|-----|-------------|
| 1 | **API Keys** | — | Obtain API key from Delhivery POC or One Panel (Settings > API Setup > Existing API Token > View/Copy). |
| 2 | **Fetch Waybill** | Bulk Waybill API | Generate waybill numbers in advance. Required only for pre-assigned waybill orders. |
| 3 | **Serviceability & TAT** | Pincode Serviceability + Expected TAT | Check if destination pincode is serviceable. Get estimated delivery time. |
| 4 | **Warehouse Setup** | Warehouse Create + Warehouse Edit API | Register and manage pickup locations. |
| 5 | **Shipping Cost** | Invoice Charges API | Get estimated shipping charges. Same API used for post-delivery billing. |
| 6 | **Shipment Creation** | Shipment Creation API | Create shipment orders (SPS/MPS). |
| 6a | **RVP QC Shipment** | RVP QC 3.0 API | Create reverse pickup shipments with quality check parameters. |
| 7 | **Update & Cancel** | Edit Shipment + Cancel Shipment API | Modify or cancel shipments before dispatch. |
| 7a | **E-Waybill Update** | Update E-Waybill API | Update e-waybill (EWB) and invoice numbers for shipments with value ≥ ₹50k. |
| 8 | **Pickup Request** | PUR Creation API | Create pickup request for Delhivery operations team. |
| 9 | **Shipping Label** | Packing Slip API | Generate printable shipping labels. |
| 10 | **Tracking** | Package Tracking API | Track shipment status and scan history. |
| 10a | **NDR Handling** | Update NDR API | Handle failed deliveries — re-attempt or reschedule pickup. |
| 10b | **NDR Status** | Get NDR Status API | Check results of NDR update — per-waybill success/failure details. |
| 11 | **Documents** | Document Download API | Fetch signatures, QC images, EPOD, and other documents by waybill. |

### When presenting to the user:
- List all steps with one-line descriptions.
- Ask which APIs they need and in what order.
- Default to the recommended order above unless the user overrides.
- Some APIs are optional (e.g., Bulk Waybill is only needed for pre-assigned waybills).

---

## 6. Available API Specs

Each API has a dedicated spec document. Load only the relevant one based on the current conversation:

| API | Resource URI | Primary Use Case | Status |
|-----|-------------|-----------------|--------|
| Pincode Serviceability | `delhivery://pincode_serviceability/spec` | Check if pincode is serviceable | ✅ Full |
| Edit Shipment | `delhivery://edit_shipment/spec` | Update shipment after creation | ✅ Full |
| Bulk Waybill Generation | `delhivery://bulk_waybill/spec` | Generate tracking numbers in bulk | ✅ Full |
| Cancel Shipment | `delhivery://cancel_shipment/spec` | Cancel shipment before dispatch | ✅ Full |
| Package Tracking | `delhivery://tracking/spec` | Track shipment status and history | ✅ Full |
| Invoice Charges | `delhivery://invoice_charges/spec` | Estimate shipping charges / billing | ✅ Full |
| Packing Slip | `delhivery://packing_slip/spec` | Generate shipping labels/slips | ✅ Full |
| Expected TAT | `delhivery://expected_tat/spec` | Get estimated delivery time | ✅ Full |
| Bulk Client Pincode | `delhivery://bulk_pincode/spec` | Enterprise pincode serviceability | ✅ Full |
| Pickup Request (PUR) | `delhivery://pickup_request/spec` | Schedule pickup from warehouse | ✅ Full |
| Shipment Creation | `delhivery://shipment_creation/spec` | Create shipment orders (SPS/MPS) | ✅ Full |
| Warehouse Create | `delhivery://warehouse_create/spec` | Register new pickup locations | ✅ Full |
| Warehouse Edit | `delhivery://warehouse_edit/spec` | Update existing pickup locations | ✅ Full |
| Document Download | `delhivery://document_download/spec` | Fetch signatures, QC images, EPOD by waybill | ✅ Full |
| E-Waybill Update | `delhivery://ewaybill_update/spec` | Update e-waybill and invoice numbers for shipments | ✅ Full |
| NDR Update | `delhivery://ndr_update/spec` | Handle failed deliveries — re-attempt or reschedule | ✅ Full |
| NDR Status | `delhivery://ndr_status/spec` | Check bulk upload / NDR update results per waybill | ✅ Full |
| RVP QC 3.0 | `delhivery://rvp_qc/spec` | Create reverse shipments with quality check (custom QC questions) | ✅ Full |
