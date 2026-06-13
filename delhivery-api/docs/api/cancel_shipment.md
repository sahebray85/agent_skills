# Cancel Shipment API — Specification

> **When to load**: User asks about cancelling a shipment or order.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/p/edit` (same endpoint as Edit Shipment) |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Cancel a shipment by waybill number or order ID |
| **Avg Latency (Prod)** | 153.43ms |
| **P99 Latency (Prod)** | 318ms |
| **Rate Limit** | 12,200/5 min/IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Cancel Shipment API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to cancel a shipment by providing the waybill number or order ID and setting the cancellation parameter to true.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Shipment
    description: Operations related to shipment cancellation

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
    CancelShipmentRequest:
      type: object
      properties:
        waybill:
          type: string
          description: Waybill number of the shipment
          example: "6945XXXXXXXX"
        cancellation:
          type: string
          description: This key needs to be passed as true to cancel a shipment
          example: "true"
      required:
        - waybill
        - cancellation

    CancelShipmentResponse:
      type: object
      properties:
        status:
          type: boolean
          description: Status of the cancellation operation
          example: true
        waybill:
          type: string
          nullable: true
          description: Waybill number
          example: "84649910000011"
        remark:
          type: string
          nullable: true
          description: Cancellation remark message
          example: "Shipment has been cancelled."
        order_id:
          type: string
          nullable: true
          description: Order ID associated with the waybill
          example: "300222"
        error:
          type: string
          nullable: true
          description: Error message (only present when status is false or in error responses)
          example: "Incorrect Waybill/OrderID, please try again"

paths:
  /api/p/edit:
    post:
      tags:
        - Shipment
      summary: Cancel a shipment or order
      description: |
        Cancels a shipment by providing the waybill number or order ID and setting the cancellation parameter to true.
        Both waybill and cancellation parameters are mandatory.
      operationId: cancelShipment
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CancelShipmentRequest'
            example:
              waybill: "6945XXXXXXXX"
              cancellation: "true"
      responses:
        '200':
          description: Response indicating success or failure of shipment cancellation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CancelShipmentResponse'
              examples:
                success:
                  summary: Shipment cancelled successfully
                  value:
                    status: true
                    waybill: "84649910000011"
                    remark: "Shipment has been cancelled."
                    order_id: "300222"
                errorIncorrectWaybill:
                  summary: Incorrect waybill/OrderID
                  value:
                    status: false
                    waybill: null
                    remark: null
                    order_id: null
                    error: "Incorrect Waybill/OrderID, please try again"
                errorEmptyWaybill:
                  summary: Waybill not passed in payload
                  value:
                    status: false
                    waybill: null
                    remark: null
                    order_id: null
                    error: "Enter Waybill/OrderID, please try again"
                errorShipmentPickedUpOrReturned:
                  summary: Shipment already picked up or returned
                  value:
                    status: false
                    waybill: "84649910000011"
                    remark: null
                    order_id: "300222"
                    error: "Shipment status cannot be changed as shipment is either picked up or already in return flow"
                errorTerminalStatus:
                  summary: Shipment in terminal status
                  value:
                    status: false
                    waybill: "84649910000011"
                    remark: null
                    order_id: "300222"
                    error: "Shipment could not be updated"
                errorPartOfDispatch:
                  summary: Shipment is part of dispatch
                  value:
                    status: false
                    waybill: "84649910000011"
                    remark: null
                    order_id: "300222"
                    error: "Shipment could not be updated"
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              examples:
                missingToken:
                  summary: Token not passed
                  value: "Authentication credentials were not provided"
                invalidToken:
                  summary: Invalid token
                  value: "Invalid Token"
                genericError:
                  summary: Generic error message
                  value: "There has been an error but we were asked to not let you see that. Please contact the dev team."
        '400':
          description: Bad Request - Invalid parameters or unsupported media type
          content:
            application/json:
              schema:
                type: string
              examples:
                unsupportedMediaType:
                  summary: Unsupported media type
                  value: "Unsupported media type 'text/plain' in request."
                genericError:
                  summary: Generic error message
                  value: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Cancellation Eligibility by Shipment Type

Cancellation is allowed only on specific package statuses depending on the shipment type:

| Shipment Type | Payment Mode | Allowed Statuses for Cancellation |
|---------------|-------------|-----------------------------------|
| Forward Shipment | COD / Prepaid | Manifested, In Transit, Pending |
| RVP Shipment | Pickup | Scheduled |
| REPL Shipment | REPL | Manifested, In Transit, Pending |

If the shipment is not in one of these statuses, the cancellation will fail.

---

## Post-Cancellation Status Changes

After a successful cancellation, the shipment status changes depending on the state at the time of cancellation:

| Status at Cancellation | Resulting Status | Status Type | Meaning |
|------------------------|-----------------|-------------|---------|
| Manifested (before pickup) | Manifested | UD (Undelivered) | Stays manifested but marked undelivered |
| In Transit | In Transit | RT (Return to Origin) | Stays in transit but rerouted back to origin |
| Pending | In Transit | RT (Return to Origin) | Moves to in transit, rerouted back to origin |
| Scheduled (RVP only) | Cancelled | CN (Cancellation) | Status updates to cancelled |

---

## CRITICAL: `cancellation` Must Be String `"true"` (NOT Boolean)

| Input | Result |
|-------|--------|
| `"cancellation": true` | ❌ **Fails** — boolean, not string |
| `"cancellation": "True"` | ❌ **Fails** — wrong case |
| `"cancellation": "true"` | ✅ **Works** — lowercase string literal |

Do NOT use `str(True)` — that produces `"True"` (capitalized).

---

## CRITICAL: Same Endpoint as Edit Shipment

Both Cancel and Edit Shipment use `POST /api/p/edit`. The `cancellation: "true"` field distinguishes a cancel from an edit.

---

## Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `waybill` | string | Yes | Waybill number to cancel |
| `cancellation` | string | Yes | Must be `"true"` (string, lowercase) |

---

## Response Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `status` | boolean | No | `true` = cancellation accepted, `false` = failed |
| `waybill` | string | Yes | Waybill number |
| `remark` | string | Yes | Cancellation message (e.g., `"Shipment has been cancelled."`) |
| `order_id` | string | Yes | Associated order ID |
| `error` | string | Yes | Error message (only present when `status` is `false`) |

---

## Known Error Scenarios (5 documented in spec)

| Error | Cause |
|-------|-------|
| `"Incorrect Waybill/OrderID, please try again"` | Invalid waybill number |
| `"Enter Waybill/OrderID, please try again"` | Waybill not passed in payload |
| `"Shipment status cannot be changed as shipment is either picked up or already in return flow"` | Shipment already picked up or in return flow |
| `"Shipment could not be updated"` | Shipment in terminal status or part of a dispatch |
| `"Authentication credentials were not provided"` | Token missing from Authorization header |

---

## 401 Responses

The 401 response has multiple forms:

| Message | Cause |
|---------|-------|
| `"Authentication credentials were not provided"` | Token not passed at all |
| `"Invalid Token"` | Token is malformed or expired |
| `"There has been an error but we were asked to not let you see that..."` | Generic auth error |

---

## 400 Responses

| Message | Cause |
|---------|-------|
| `"Unsupported media type 'text/plain' in request."` | Wrong Content-Type header (must be `application/json`) |
| `"There has been an error but we were asked to not let you see that..."` | Generic bad request |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Sending `cancellation: true` (boolean) | Must be string `"true"` |
| Sending `"True"` or `"TRUE"` | Must be lowercase `"true"` |
| Using `str(True)` in Python | Produces `"True"` — hardcode `"true"` instead |
| Expecting a different endpoint from Edit Shipment | Both use `/api/p/edit` |
| Sending `text/plain` Content-Type | Must be `application/json` |
| Retrying after "picked up or already in return flow" | Not retriable — shipment state cannot be changed |
