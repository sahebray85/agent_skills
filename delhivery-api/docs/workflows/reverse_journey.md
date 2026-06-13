# Reverse & Return Journey — Workflow

> **Scope**: Workflow for reverse pickup (customer returns) and replacement/buyback flows. Load this when the user is implementing return or exchange functionality.

---

## 1. Return Journey (Undeliverable)

When a shipment cannot be delivered (incorrect address, recipient unavailable, refused), it automatically enters the return flow.

```
Delivery Attempt Failed
  └─▶ Package marked as "Undelivered"
       └─▶ Rerouted to return center or seller warehouse
            └─▶ Return transit (same hub network, reverse direction)
                 └─▶ Delivered back to seller
```

**No separate API call needed** — the return is triggered by Delhivery operations. Track the shipment status via the Package Tracking API to monitor the return.

---

## 2. Reverse Pickup (RVP) — Customer-Initiated Return

When a customer initiates a return, the seller creates a reverse shipment order.

| Step | API | Action |
|------|-----|--------|
| Create Reverse Shipment | Shipment Creation API | Create order with payment mode = `Pickup`. Pickup from customer address. |
| Create Reverse Shipment **with QC** | RVP QC 3.0 API | Create reverse shipment with item-level quality check questions. FE inspects items on pickup. |
| Generate Label | Packing Slip API | Generate return shipping label for the customer to attach. |
| Request Pickup | PUR Creation API | Schedule pickup from customer's address. |
| Track Return | Package Tracking API | Monitor return shipment until received at seller warehouse. |

**Key differences from forward journey**:
- Payment mode is `Pickup` (not Prepaid/COD).
- Pickup location is the **customer's address**, not the warehouse.
- Delivery destination is the **seller's warehouse** or returns facility.

**RVP QC 3.0** (optional but recommended for returns):
- Adds item-level quality check at pickup — FE verifies product condition before accepting.
- Uses same endpoint (`/api/cmu/create.json`) but with `client`, `qc_type`, and `custom_qc` fields.
- QC questions can be `varchar` (typed answer) or `multi` (select from options).
- Use `required: true` on questions that must match expected answers for QC to pass.

---

## 3. Replacement / Buyback (REPL)

When a customer requests a product replacement, two simultaneous flows are triggered:

```
┌──────────────────────────┐    ┌──────────────────────────┐
│ Forward: New Product     │    │ Reverse: Old Product     │
│ Seller → Customer        │    │ Customer → Seller        │
│                          │    │                          │
│ Payment Mode: REPL       │    │ (Linked reverse flow)    │
└──────────────────────────┘    └──────────────────────────┘
```

| Step | API | Action |
|------|-----|--------|
| Create Replacement Order | Shipment Creation API | Create order with payment mode = `REPL`. |
| Track Both Legs | Package Tracking API | Track forward delivery and reverse pickup separately. |

---

## 4. When to Load This Document

Load this document when the user mentions:
- "return", "reverse", "RVP", "reverse pickup"
- "replacement", "buyback", "exchange", "REPL"
- "customer return", "undelivered", "failed delivery"
