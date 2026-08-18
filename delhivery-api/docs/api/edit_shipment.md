# Edit Shipment API — Specification

> **When to load**: User asks about updating shipment details, changing COD amount, changing payment mode, modifying consignee info, or updating dimensions/weight after shipment creation.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/p/edit` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Update shipment details (consignee info, payment mode, dimensions, weight) |
| **Avg Latency (Prod)** | 153.43ms |
| **P99 Latency (Prod)** | 318ms |
| **Rate Limit** | 12,200/5 min/IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Edit Shipment API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to update shipment details such as consignee information, payment mode, dimensions, and weight.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Shipment
    description: Operations related to shipment management and updates

security:
  - TokenAuth: []

components:
  securitySchemes:
    TokenAuth:
      type: http
      scheme: Token
      description: |
        Token-based authentication. Use the format: `Authorization: Token <your-token>`
        Here client need to pass the client token in the Authorization header.

  schemas:
    EditShipmentRequest:
      type: object
      properties:
        waybill:
          type: string
          description: Waybill for which update is required
          example: "84649910000011"
        name:
          type: string
          description: Name of the consignee
          example: "John Doe"
        phone:
          type: string
          description: Consignee phone number(s) as comma-separated string
          example: "9876543210,9876543211"
        pt:
          type: string
          description: Payment mode that needs to be updated
          example: "COD/Pre-paid"
        add:
          type: string
          description: Address of the consignee
          example: "123 Main Street, City, State"
        products_desc:
          type: string
          description: Product Description
          example: "Electronics"
        gm:
          type: number
          format: float
          description: Weight of the shipment (gms)
          example: 100.2
        shipment_height:
          type: number
          format: float
          description: Height of the shipment in cm
          example: 40
        shipment_width:
          type: number
          format: float
          description: Width of the shipment in cm
          example: 30
        shipment_length:
          type: number
          format: float
          description: Length of the shipment in cm
          example: 50
        cod:
          type: number
          format: float
          description: Cash on Delivery (COD) amount
          example: 100
      required:
        - waybill

    EditShipmentResponse:
      type: object
      properties:
        status:
          oneOf:
            - type: boolean
            - type: string
          description: Status of the update operation. Can be boolean (true) for success or string ("Failure") for errors
          example: true
        waybill:
          type: string
          nullable: true
          description: Waybill number
          example: "waybill number"
        order_id:
          type: string
          nullable: true
          description: Order ID associated with the waybill
          example: "order number"
        error:
          type: string
          description: Error message (only present when status is "Failure")
          example: "Enter Waybill/OrderID, please try again"

paths:
  /api/p/edit:
    post:
      tags:
        - Shipment
      summary: Edit shipment details
      description: |
        Updates shipment details such as consignee information, payment mode, dimensions, and weight.
        Only the waybill parameter is mandatory. All other parameters are optional.
      operationId: editShipment
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EditShipmentRequest'
            example:
              waybill: "84649910000011"
              pt: "COD/Pre-paid"
              cod: 100
              shipment_height: 40
              weight: 100
      responses:
        '200':
          description: Response indicating success or failure of the update operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EditShipmentResponse'
              examples:
                success:
                  summary: Successful update
                  value:
                    status: true
                    waybill: "waybill number"
                    order_id: "order number"
                errorEmptyWaybill:
                  summary: Empty waybill/OrderID
                  value:
                    error: "Enter Waybill/OrderID, please try again"
                    status: "Failure"
                    waybill: null
                    order_id: null
                errorUnauthorized:
                  summary: User not authorized
                  value:
                    error: "You are not authorised to this action, please contact tech.admin@delhivery.com"
                    status: "Failure"
                    waybill: "waybill"
                    order_id: null
                errorIncorrectWaybill:
                  summary: No packages found with given waybill
                  value:
                    error: "Incorrect Waybill/OrderID, please try again"
                    status: "Failure"
                    waybill: null
                    order_id: "waybill"
                errorMultipleMPS:
                  summary: Multiple MPS lots found
                  value:
                    error: "Multiple MPS lot found, please try again"
                    status: "Failure"
                    waybill: null
                    order_id: "waybill"
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Edit Eligibility by Shipment Type

Edit is allowed only on specific package statuses depending on the shipment type:

| Shipment Type | Payment Mode | Allowed Statuses for Edit |
|---------------|-------------|--------------------------|
| Forward Shipment | COD / Prepaid | Manifested, In Transit, Pending |
| RVP Shipment | Pickup | Scheduled |
| REPL Shipment | REPL | Manifested, In Transit, Pending |

Edit is **NOT allowed** on any Dispatched or Terminal status: **Delivered, DTO, RTO, LOST, Closed**.

---

## Payment Mode Conversion Rules

When updating payment mode (`pt` field), the following rules apply:

| # | Conversion | Allowed? | Notes |
|---|-----------|----------|-------|
| 1 | COD → Prepaid | ✅ Yes | — |
| 2 | Prepaid → COD | ✅ Yes | COD amount **must** be provided |
| 3 | Prepaid → Prepaid | ❌ No | Same-mode "conversion" not allowed |
| 4 | COD → COD | ❌ No | Same-mode "conversion" not allowed |
| 5 | Prepaid → Pickup | ❌ No | — |
| 6 | Pickup → Prepaid | ❌ No | — |
| 7 | COD → Pickup | ❌ No | — |
| 8 | Pickup → COD | ❌ No | — |
| 9 | Prepaid → REPL | ❌ No | — |
| 10 | REPL → Prepaid | ❌ No | — |
| 11 | COD → REPL | ❌ No | — |
| 12 | REPL → COD | ❌ No | — |

**Key takeaway**: Only COD ↔ Prepaid conversions are allowed. All other payment mode changes are rejected.

---

## CRITICAL Editable Attributes

The following attributes of an order can be edited during the lifecycle of a shipment.

| Order Status | COD Amount | Pickup Location | Billing Address |Shipping Address | Shipping Mode |
|--------------|------|---------|--------|--------|--------|
| Pending | Yes | Yes | Yes | Yes | Yes  |
| Ready to Ship | Yes | No | Yes | Yes | No  |
| Ready for Pickup | Yes | No | Yes | Yes | No  |
| In Transit | Yes | No | Yes | Yes | No  |
| Out for Delivery | No | No | Yes | No | No |

## CRITICAL: `status` Field is Dual-Type

The `status` field can be **either boolean or string**:

| `status` value | Type | Meaning |
|----------------|------|---------|
| `true` (boolean) | boolean | Update successful |
| `"Failure"` (string) | string | Business logic error — read `error` field for details |

Always check the **type** of `status`, not just the value.

---

## CRITICAL: `cod` Field in Request

The `cod` field (float) allows updating the Cash on Delivery amount. This is separate from the `pt` (payment type) field.

---

## Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `waybill` | string | Yes | Waybill number to update |
| `name` | string | No | Consignee name |
| `phone` | string (comma-separated) | No | Consignee phone number(s) as comma-separated string (e.g., `"9876543210,9876543211"`) |
| `pt` | string | No | Payment mode (`"COD"` / `"Pre-paid"`) |
| `add` | string | No | Consignee address |
| `products_desc` | string | No | Product description |
| `gm` | float | No | Weight of the shipment (gms) |
| `shipment_height` | float | No | Height in cm |
| `shipment_width` | float | No | Width in cm |
| `shipment_length` | float | No | Length in cm |
| `cod` | float | No | COD amount |

---

## Response Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `status` | boolean \| string | No | `true` = success, `"Failure"` = error |
| `waybill` | string | Yes | Waybill number |
| `order_id` | string | Yes | Associated order ID |
| `error` | string | — | Error message (only present when `status` is `"Failure"`) |

---

## Known Error Scenarios (4 documented in spec)

| Error | Cause |
|-------|-------|
| `"Enter Waybill/OrderID, please try again"` | Empty or missing waybill in payload |
| `"You are not authorised to this action, please contact tech.admin@delhivery.com"` | User lacks permission for this operation |
| `"Incorrect Waybill/OrderID, please try again"` | No packages found for the given waybill |
| `"Multiple MPS lot found, please try again"` | Multiple MPS lots found for the waybill |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Phone as array/list | `phone` is a comma-separated string: `"9876543210,9876543211"` |
| Not handling dual-type `status` | Check for both `boolean true` and `string "Failure"` |
| Retrying when `status: "Failure"` | Business logic error — don't retry |
| Sending all fields when updating one | Only `waybill` is required; send only fields that need updating |
| Confusing with Cancel Shipment | Both use same endpoint `/api/p/edit` — cancel adds `cancellation: "true"` |
