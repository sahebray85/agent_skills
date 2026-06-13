# Package Tracking API — Specification

> **When to load**: User asks about tracking shipments, getting shipment status, scan history, delivery updates, or looking up waybill/order status.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/v1/packages/json/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Get package tracking information by waybill or reference ID / order ID |
| **Avg Latency (Prod)** | 130.31ms |
| **P99 Latency (Prod)** | 529.15ms |
| **Rate Limit** | 750 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Package Tracking API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to get the current status and detailed history of scans applied to a shipment by waybill number or reference ID / order ID. Supports tracking up to 50 waybills (comma-separated) in a single request.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Package Tracking
    description: Operations related to package tracking and shipment status

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
    PackageTrackingResponse:
      type: object
      properties:
        ShipmentData:
          type: array
          items:
            type: object
            properties:
              Shipment:
                type: object
                properties:
                  PickUpDate:
                    type: string
                    format: date-time
                    description: Pickup date of the shipment
                    example: "2026-01-21T16:07:22.009"
                  Destination:
                    type: string
                    description: Destination location
                    example: ""
                  DestRecieveDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Destination receive date
                    example: null
                  Scans:
                    type: array
                    items:
                      type: object
                      properties:
                        ScanDetail:
                          type: object
                          properties:
                            ScanDateTime:
                              type: string
                              format: date-time
                              description: Date and time of the scan
                              example: "2026-01-21T16:07:22.024"
                            ScanType:
                              type: string
                              description: Type of scan
                              example: "UD"
                            Scan:
                              type: string
                              description: Scan description
                              example: "Manifested"
                            StatusDateTime:
                              type: string
                              format: date-time
                              description: Status date and time
                              example: "2026-01-21T16:07:22.024"
                            ScannedLocation:
                              type: string
                              description: Location where scan was performed
                              example: "HQ (Haryana)"
                            StatusCode:
                              type: string
                              description: Status code
                              example: "X-UCI"
                            Instructions:
                              type: string
                              description: Instructions or remarks
                              example: "Manifest uploaded"
                  Status:
                    type: object
                    properties:
                      Status:
                        type: string
                        description: Current status of the shipment
                        example: "Not Picked"
                      StatusLocation:
                        type: string
                        description: Location of current status
                        example: "HQ (Haryana)"
                      StatusDateTime:
                        type: string
                        format: date-time
                        description: Date and time of current status
                        example: "2026-02-03T12:52:56.16"
                      RecievedBy:
                        type: string
                        description: Person who received the shipment
                        example: ""
                      StatusCode:
                        type: string
                        description: Status code
                        example: "DTUP-210"
                      StatusType:
                        type: string
                        description: Type of status
                        example: "UD"
                      Instructions:
                        type: string
                        description: Status instructions
                        example: "Seller cancelled the order"
                  ReturnPromisedDeliveryDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Return promised delivery date
                    example: null
                  InvoiceAmount:
                    type: number
                    description: Invoice amount
                    example: 12931
                  ChargedWeight:
                    type: number
                    nullable: true
                    description: Charged weight
                    example: null
                  PickedupDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Picked up date
                    example: null
                  DeliveryDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Delivery date
                    example: null
                  SenderName:
                    type: string
                    description: Name of the sender
                    example: "ZIPYPOST10B2BC-B2B"
                  AWB:
                    type: string
                    description: Airway bill number (waybill)
                    example: "84649910000011"
                  DispatchCount:
                    type: integer
                    description: Dispatch count
                    example: 0
                  OrderType:
                    type: string
                    description: Order type (Pre-paid/COD)
                    example: "Pre-paid"
                  ReturnedDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Returned date
                    example: null
                  ExpectedDeliveryDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Expected delivery date
                    example: null
                  RTOStartedDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: RTO started date
                    example: null
                  Extras:
                    type: string
                    description: Extra information
                    example: ""
                  FirstAttemptDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: First attempt date
                    example: null
                  ReverseInTransit:
                    type: boolean
                    description: Whether shipment is in reverse transit
                    example: false
                  Quantity:
                    type: string
                    description: Quantity
                    example: ""
                  Origin:
                    type: string
                    nullable: true
                    description: Origin location
                    example: null
                  Consignee:
                    type: object
                    properties:
                      City:
                        type: string
                        description: City of consignee
                        example: ""
                      Name:
                        type: string
                        description: Name of consignee
                        example: "testing-1"
                      Address1:
                        type: array
                        items:
                          type: string
                        description: Address line 1
                        example: []
                      Address2:
                        type: array
                        items:
                          type: string
                        description: Address line 2
                        example: []
                      Address3:
                        type: string
                        description: Address line 3
                        example: ""
                      PinCode:
                        type: integer
                        description: Pincode
                        example: 122018
                      State:
                        type: string
                        description: State
                        example: "Haryana"
                      Telephone2:
                        type: string
                        description: Secondary telephone number
                        example: ""
                      Country:
                        type: string
                        description: Country
                        example: "India"
                      Telephone1:
                        type: string
                        description: Primary telephone number
                        example: ""
                  ReferenceNo:
                    type: string
                    description: Reference number (Order ID)
                    example: "300222"
                  OutDestinationDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Out destination date
                    example: null
                  CODAmount:
                    type: number
                    description: COD amount
                    example: 0
                  PromisedDeliveryDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Promised delivery date
                    example: null
                  PickupLocation:
                    type: string
                    nullable: true
                    description: Pickup location
                    example: null
                  OriginRecieveDate:
                    type: string
                    format: date-time
                    nullable: true
                    description: Origin receive date
                    example: null
                  Ewaybill:
                    type: array
                    items:
                      type: string
                    description: E-waybill information
                    example: []

    PackageTrackingErrorResponse:
      type: object
      properties:
        rmk:
          type: string
          description: Error remark message
          example: "Some error has occurred. Please contact client.support@delhivery.com with error message- Data does not exists for provided Waybill(s)"
        Success:
          type: boolean
          description: Success status
          example: false
        Error:
          type: string
          description: Error message
          example: "Data does not exists for provided Waybill(s)"

paths:
  /api/v1/packages/json/:
    get:
      tags:
        - Package Tracking
      summary: Get package tracking information
      description: |
        Retrieves the current status and detailed history of scans applied to a shipment by waybill number or reference ID / order ID.
        Supports tracking up to 50 waybills (comma-separated) in a single request. At least one of waybill or ref_ids must be provided.
      operationId: getPackageTracking
      security:
        - TokenAuth: []
      parameters:
        - name: waybill
          in: query
          required: true
          description: Waybill Number(s). Supports up to 50 waybills as comma-separated values.
          schema:
            type: string
          example: "1122345678722"
        - name: ref_ids
          in: query
          required: false
          description: Reference ID / Order ID
          schema:
            type: string
          example: ""
      responses:
        '200':
          description: Successful response with package tracking information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackageTrackingResponse'
              example:
                ShipmentData:
                  - Shipment:
                      PickUpDate: "2026-01-21T16:07:22.009"
                      Destination: ""
                      DestRecieveDate: null
                      Scans:
                        - ScanDetail:
                            ScanDateTime: "2026-01-21T16:07:22.024"
                            ScanType: "UD"
                            Scan: "Manifested"
                            StatusDateTime: "2026-01-21T16:07:22.024"
                            ScannedLocation: "HQ (Haryana)"
                            StatusCode: "X-UCI"
                            Instructions: "Manifest uploaded"
                        - ScanDetail:
                            ScanDateTime: "2026-01-25T12:28:18.655"
                            ScanType: "UD"
                            Scan: "Not Picked"
                            StatusDateTime: "2026-01-25T12:28:18.655"
                            ScannedLocation: "HQ (Haryana)"
                            StatusCode: "X-PNP"
                            Instructions: "Shipment not received from client"
                        - ScanDetail:
                            ScanDateTime: "2026-02-03T12:52:56.16"
                            ScanType: "UD"
                            Scan: "Not Picked"
                            StatusDateTime: "2026-02-03T12:52:56.16"
                            ScannedLocation: "HQ (Haryana)"
                            StatusCode: "DTUP-210"
                            Instructions: "Seller cancelled the order"
                      Status:
                        Status: "Not Picked"
                        StatusLocation: "HQ (Haryana)"
                        StatusDateTime: "2026-02-03T12:52:56.16"
                        RecievedBy: ""
                        StatusCode: "DTUP-210"
                        StatusType: "UD"
                        Instructions: "Seller cancelled the order"
                      ReturnPromisedDeliveryDate: null
                      Ewaybill: []
                      InvoiceAmount: 12931
                      ChargedWeight: null
                      PickedupDate: null
                      DeliveryDate: null
                      SenderName: "ZIPYPOST10B2BC-B2B"
                      AWB: "84649910000011"
                      DispatchCount: 0
                      OrderType: "Pre-paid"
                      ReturnedDate: null
                      ExpectedDeliveryDate: null
                      RTOStartedDate: null
                      Extras: ""
                      FirstAttemptDate: null
                      ReverseInTransit: false
                      Quantity: ""
                      Origin: null
                      Consignee:
                        City: ""
                        Name: "testing-1"
                        Address1: []
                        Address2: []
                        Address3: ""
                        PinCode: 122018
                        State: "Haryana"
                        Telephone2: ""
                        Country: "India"
                        Telephone1: ""
                      ReferenceNo: "300222"
                      OutDestinationDate: null
                      CODAmount: 0
                      PromisedDeliveryDate: null
                      PickupLocation: null
                      OriginRecieveDate: null
        '400':
          description: Bad Request - Data does not exist for provided Waybill(s)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackageTrackingErrorResponse'
              example:
                rmk: "Some error has occurred. Please contact client.support@delhivery.com with error message- Data does not exists for provided Waybill(s)"
                Success: false
                Error: "Data does not exists for provided Waybill(s)"
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Query Parameters

| Parameter | In | Required | Type | Description |
|-----------|----|----------|------|-------------|
| `waybill` | query | Yes | string | Waybill number(s) — supports up to 50 comma-separated waybills |
| `ref_ids` | query | No | string | Reference ID / Order ID — alternative lookup |

At least one of `waybill` or `ref_ids` must be provided.

---

## CRITICAL: Supports Up to 50 Waybills Per Request

You can track up to **50 waybills** in a single request by passing them as **comma-separated values** in the `waybill` parameter:

```
GET /api/v1/packages/json/?waybill=WB001,WB002,WB003,...
```

The response `ShipmentData` array will contain one entry per waybill. Do not exceed 50 waybills per request.

---

## Response Structure — Key Fields

The response is deeply nested: `ShipmentData[].Shipment.*`

### Top-Level Shipment Fields

| Field | Type | Description |
|-------|------|-------------|
| `AWB` | string | Waybill number |
| `ReferenceNo` | string | Reference ID / Order ID |
| `OrderType` | string | `"Pre-paid"` or `"COD"` |
| `SenderName` | string | Sender/client name |
| `InvoiceAmount` | number | Invoice amount |
| `CODAmount` | number | COD amount |
| `ChargedWeight` | number \| null | Charged weight |
| `DispatchCount` | integer | Number of dispatch attempts |
| `ReverseInTransit` | boolean | Whether in reverse transit |
| `Quantity` | string | Quantity |
| `Extras` | string | Extra info |
| `Origin` | string \| null | Origin location |
| `Destination` | string | Destination location |
| `PickupLocation` | string \| null | Pickup location |

### Date Fields (all nullable `date-time` or null)

| Field | Description |
|-------|-------------|
| `PickUpDate` | Pickup date |
| `PickedupDate` | Actually picked up date |
| `DeliveryDate` | Delivery date |
| `ExpectedDeliveryDate` | Expected delivery date |
| `PromisedDeliveryDate` | Promised delivery date |
| `ReturnPromisedDeliveryDate` | Return promised delivery date |
| `FirstAttemptDate` | First delivery attempt date |
| `RTOStartedDate` | RTO started date |
| `ReturnedDate` | Returned date |
| `DestRecieveDate` | Destination receive date |
| `OriginRecieveDate` | Origin receive date |
| `OutDestinationDate` | Out destination date |

### `Status` Object

| Field | Type | Description |
|-------|------|-------------|
| `Status` | string | Current status text (e.g., `"Not Picked"`, `"In Transit"`, `"Delivered"`) |
| `StatusLocation` | string | Location of current status |
| `StatusDateTime` | date-time | Timestamp of current status |
| `RecievedBy` | string | Receiver name (on delivery) |
| `StatusCode` | string | Status code (e.g., `"DTUP-210"`, `"X-UCI"`) |
| `StatusType` | string | Status type (e.g., `"UD"`) |
| `Instructions` | string | Status instructions/remarks |

### `Scans[]` Array — Each item has `ScanDetail`

| Field | Type | Description |
|-------|------|-------------|
| `ScanDateTime` | date-time | Scan timestamp |
| `ScanType` | string | Scan type |
| `Scan` | string | Scan description (e.g., `"Manifested"`) |
| `StatusDateTime` | date-time | Status timestamp |
| `ScannedLocation` | string | Scan location |
| `StatusCode` | string | Status code |
| `Instructions` | string | Scan instructions |

### `Consignee` Object

| Field | Type | Description |
|-------|------|-------------|
| `Name` | string | Consignee name |
| `City` | string | City |
| `State` | string | State |
| `Country` | string | Country |
| `PinCode` | integer | Pincode |
| `Address1` | **array** of strings | Address line 1 |
| `Address2` | **array** of strings | Address line 2 |
| `Address3` | string | Address line 3 |
| `Telephone1` | string | Primary phone |
| `Telephone2` | string | Secondary phone |

### `Ewaybill` Field

| Field | Type | Description |
|-------|------|-------------|
| `Ewaybill` | array of strings | E-waybill numbers |

---

## CRITICAL: `Address1` and `Address2` Are Arrays, Not Strings

```json
"Address1": [],
"Address2": []
```

These are **arrays of strings**, not plain strings. Code that does `consignee["Address1"]` expecting a string will break.

---

## CRITICAL: `StatusCode` Is a String, Not Numeric

Status codes like `"X-UCI"`, `"X-PNP"`, `"DTUP-210"` are **alphanumeric strings**, not integers. Do not parse them as numbers.

---

## Error Response (400)

When a waybill is not found, the API returns HTTP **400** (not 404):

```json
{
  "rmk": "Some error has occurred. Please contact client.support@delhivery.com with error message- Data does not exists for provided Waybill(s)",
  "Success": false,
  "Error": "Data does not exists for provided Waybill(s)"
}
```

This is **data-not-found**, NOT a transient error. Do NOT retry. See `tracking/retry.md`.

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Treating 400 as a server error and retrying | 400 = data not found — don't retry |
| Expecting `Address1`/`Address2` to be strings | They're arrays of strings |
| Parsing `StatusCode` as an integer | It's an alphanumeric string |
| Not handling `null` for date fields | Many date fields are nullable — check before parsing |
| Accessing `Shipment` directly | Response is `ShipmentData[0].Shipment` — it's nested in an array |
| Assuming all fields are always present | Use safe access with defaults for every field |
