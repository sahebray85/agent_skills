# Invoice Charges API — Specification

> **When to load**: User asks about calculating tentative shipping costs, getting invoice charges, or estimating delivery fees.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/kinko/v1/invoice/charges/.json` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Calculate estimated/tentative shipping charges based on origin, destination, weight, payment type, billing mode, and shipment status |
| **Avg Latency (Prod)** | 450.94ms |
| **P99 Latency (Prod)** | 61.14s |
| **Rate Limit** | 50 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Invoice Charges API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to calculate estimated/tentative shipping charges for shipments based on origin, destination, weight, payment type, and other parameters. Note: This API provides approximate values for shipping charges, which are subject to change.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Invoice
    description: Operations related to invoice charges calculation

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
    InvoiceChargesResponse:
      type: array
      items:
        type: object
        properties:
          charge_ROV:
            type: number
            description: ROV charge
            example: 0
          charge_REATTEMPT:
            type: number
            description: Reattempt charge
            example: 0
          charge_RTO:
            type: number
            description: RTO charge
            example: 0
          charge_MPS:
            type: number
            description: MPS charge
            example: 0
          charge_pickup:
            type: number
            description: Pickup charge
            example: 0
          charge_CWH:
            type: number
            description: CWH charge
            example: 0
          tax_data:
            type: object
            properties:
              swacch_bharat_tax:
                type: number
                description: Swachh Bharat tax
                example: 0
              IGST:
                type: number
                description: Integrated GST
                example: 0
              SGST:
                type: number
                description: State GST
                example: 0
              service_tax:
                type: number
                description: Service tax
                example: 0
              krishi_kalyan_cess:
                type: number
                description: Krishi Kalyan Cess
                example: 0
              CGST:
                type: number
                description: Central GST
                example: 0
          charge_DEMUR:
            type: number
            description: Demurrage charge
            example: 0
          charge_AWB:
            type: number
            description: AWB charge
            example: 0
          zone:
            type: string
            description: Zone classification
            example: "A"
          wt_rule_id:
            type: string
            nullable: true
            description: Weight rule ID
            example: null
          charge_AIR:
            type: number
            description: Air charge
            example: 0
          charge_FSC:
            type: number
            description: FSC charge
            example: 0
          charge_LABEL:
            type: number
            description: Label charge
            example: 0
          charge_COD:
            type: number
            description: COD charge
            example: 0
          status:
            type: string
            description: Status of shipment
            example: "Delivered"
          charge_PEAK:
            type: number
            description: Peak charge
            example: 0
          charge_POD:
            type: number
            description: POD charge
            example: 0
          charge_LM:
            type: number
            description: LM charge
            example: 0
          adhoc_data:
            type: object
            description: Adhoc data
            example: {}
          wt_sop_type:
            type: string
            nullable: true
            description: Weight SOP type
            example: null
          charge_CCOD:
            type: number
            description: CCOD charge
            example: 0
          gross_amount:
            type: number
            description: Gross amount
            example: 0
          charge_E2E:
            type: number
            description: E2E charge
            example: 0
          charge_DTO:
            type: number
            description: DTO charge
            example: 0
          charge_COVID:
            type: number
            description: COVID charge
            example: 0
          divisor:
            type: integer
            description: Divisor for calculation
            example: 5000
          zonal_cl:
            type: string
            nullable: true
            description: Zonal classification
            example: null
          charge_DL:
            type: number
            description: DL charge
            example: 0
          total_amount:
            type: number
            description: Total amount
            example: 0
          charge_DPH:
            type: number
            description: DPH charge
            example: 0
          charge_FOD:
            type: number
            description: FOD charge
            example: 0
          charge_DOCUMENT:
            type: number
            description: Document charge
            example: 0
          charge_WOD:
            type: number
            description: WOD charge
            example: 0
          charge_INS:
            type: number
            description: Insurance charge
            example: 0
          charge_FS:
            type: number
            description: FS charge
            example: 0
          charge_CNC:
            type: number
            description: CNC charge
            example: 0
          charge_FOV:
            type: number
            description: FOV charge
            example: 0
          charge_QC:
            type: number
            description: QC charge
            example: 0
          charged_weight:
            type: integer
            description: Charged weight in grams
            example: 10

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Error message
          example: "md is mandatory field and possible values can be S,E"

paths:
  /api/kinko/v1/invoice/charges/.json:
    get:
      tags:
        - Invoice
      summary: Calculate estimated shipping charges
      description: |
        Calculates and returns estimated/tentative shipping charges for shipments based on origin pincode, destination pincode, weight, payment type, billing mode, and shipment status. Note: Values are approximate and subject to change.
      operationId: getInvoiceCharges
      security:
        - TokenAuth: []
      parameters:
        - name: md
          in: query
          required: true
          description: Billing Mode of shipment (E for Express/S for Surface)
          schema:
            type: string
            enum: [E, S]
          example: "E"
        - name: cgm
          in: query
          required: true
          description: Chargeable weight of the shipment in Grams Unit. Default value is 0
          schema:
            type: integer
            minimum: 0
          example: 10
        - name: o_pin
          in: query
          required: true
          description: Pincode of origin city (6 Digit Valid Pin code)
          schema:
            type: integer
            minimum: 100000
            maximum: 999999
          example: 110042
        - name: d_pin
          in: query
          required: true
          description: Pincode of destination city (6 Digit Valid Pin code)
          schema:
            type: integer
            minimum: 100000
            maximum: 999999
          example: 110053
        - name: ss
          in: query
          required: true
          description: Status of shipment (Delivered, RTO, DTO)
          schema:
            type: string
            enum: [Delivered, RTO, DTO]
          example: "Delivered"
        - name: pt
          in: query
          required: true
          description: Payment Type (Pre-paid, COD)
          schema:
            type: string
            enum: [Pre-paid, COD]
          example: "Pre-paid"
        - name: l
          in: query
          required: false
          description: Length of shipment
          schema:
            type: integer
          example: 30
        - name: b
          in: query
          required: false
          description: Breadth of shipment
          schema:
            type: integer
          example: 20
        - name: h
          in: query
          required: false
          description: Height of shipment
          schema:
            type: integer
          example: 40
        - name: ipkg_type
          in: query
          required: false
          description: Type of Package (box/flyer)
          schema:
            type: string
            enum: [box, flyer]
          example: "box"
      responses:
        '200':
          description: Successful response with invoice charges
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InvoiceChargesResponse'
              example:
                - charge_ROV: 0
                  charge_REATTEMPT: 0
                  charge_RTO: 0
                  charge_MPS: 0
                  charge_pickup: 0
                  charge_CWH: 0
                  tax_data:
                    swacch_bharat_tax: 0
                    IGST: 0
                    SGST: 0
                    service_tax: 0
                    krishi_kalyan_cess: 0
                    CGST: 0
                  charge_DEMUR: 0
                  charge_AWB: 0
                  zone: "A"
                  wt_rule_id: null
                  charge_AIR: 0
                  charge_FSC: 0
                  charge_LABEL: 0
                  charge_COD: 0
                  status: "Delivered"
                  charge_PEAK: 0
                  charge_POD: 0
                  charge_LM: 0
                  adhoc_data: {}
                  wt_sop_type: null
                  charge_CCOD: 0
                  gross_amount: 0
                  charge_E2E: 0
                  charge_DTO: 0
                  charge_COVID: 0
                  divisor: 5000
                  zonal_cl: null
                  charge_DL: 0
                  total_amount: 0
                  charge_DPH: 0
                  charge_FOD: 0
                  charge_DOCUMENT: 0
                  charge_WOD: 0
                  charge_INS: 0
                  charge_FS: 0
                  charge_CNC: 0
                  charge_FOV: 0
                  charge_QC: 0
                  charged_weight: 10
        '400':
          description: Bad Request - Invalid or missing mandatory parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                missingMD:
                  summary: Missing or invalid md parameter
                  value:
                    error: "md is mandatory field and possible values can be S,E"
                missingSS:
                  summary: Missing or invalid ss parameter
                  value:
                    error: "ss is mandatory field and possible values can be Delivered,RTO,DTO"
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Required Query Parameters

| Parameter | Type | Enum Values | Description |
|-----------|------|-------------|-------------|
| `md` | string | `E`, `S` | Billing mode — Express or Surface |
| `cgm` | integer | — | Chargeable weight in grams (min: 0) |
| `o_pin` | integer | — | Origin pincode (6-digit) |
| `d_pin` | integer | — | Destination pincode (6-digit) |
| `ss` | string | `Delivered`, `RTO`, `DTO` | Shipment status |
| `pt` | string | `Pre-paid`, `COD` | Payment type |

## Optional Query Parameters

| Parameter | Type | Enum Values | Description |
|-----------|------|-------------|-------------|
| `l` | integer | — | Length of shipment |
| `b` | integer | — | Breadth of shipment |
| `h` | integer | — | Height of shipment |
| `ipkg_type` | string | `box`, `flyer` | Package type |

---

## CRITICAL: Charges Are Approximate and Subject to Change

This API provides **approximate values** for shipping charges, which are **subject to change**. Do not treat these as final billing amounts — actual invoice charges may differ. Always communicate this to the user when presenting results.

---

## CRITICAL: Response Is an Array

The response is a **JSON array** containing a single object (not a plain object). Always index into it:

```
response[0].total_amount   // correct
response.total_amount      // WRONG — will be undefined
```

---

## CRITICAL: ~40 Charge Fields in Response

The response object contains a large number of charge fields. The key fields for most integrations:

| Field | Description |
|-------|-------------|
| `total_amount` | Final total amount |
| `gross_amount` | Gross amount before adjustments |
| `charged_weight` | Weight used for billing (grams) |
| `zone` | Zone classification (e.g., `"A"`) |
| `divisor` | Volumetric weight divisor (typically `5000`) |
| `tax_data` | Nested object with GST breakdown (`IGST`, `SGST`, `CGST`, etc.) |

All `charge_*` fields are numeric and default to `0`. Don't assume only a few charges exist — the full list includes: `charge_ROV`, `charge_REATTEMPT`, `charge_RTO`, `charge_MPS`, `charge_pickup`, `charge_CWH`, `charge_DEMUR`, `charge_AWB`, `charge_AIR`, `charge_FSC`, `charge_LABEL`, `charge_COD`, `charge_PEAK`, `charge_POD`, `charge_LM`, `charge_CCOD`, `charge_E2E`, `charge_DTO`, `charge_COVID`, `charge_DL`, `charge_DPH`, `charge_FOD`, `charge_DOCUMENT`, `charge_WOD`, `charge_INS`, `charge_FS`, `charge_CNC`, `charge_FOV`, `charge_QC`.

---

## Error Messages Are Descriptive

400 errors tell you exactly which parameter is missing and what values are accepted:

```json
{"error": "md is mandatory field and possible values can be S,E"}
{"error": "ss is mandatory field and possible values can be Delivered,RTO,DTO"}
```

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Treating response as object | It's an **array** — access `response[0]` |
| Using made-up charge field names | Use exact field names from spec (e.g., `charge_FSC`, not `fuel_surcharge`) |
| Ignoring `divisor` for volumetric weight | Use `divisor` (typically 5000) to calculate volumetric weight: `(l × b × h) / divisor` |
| Passing pincode as string | Spec defines `o_pin` and `d_pin` as `integer` |
| Omitting `ss` (shipment status) | Required — charges differ by status (`Delivered` vs `RTO` vs `DTO`) |
| Using `"express"` instead of `"E"` for `md` | Enum values are single characters: `E` or `S` |
| Using `"cod"` instead of `"COD"` for `pt` | Values are case-sensitive: `Pre-paid`, `COD` |
