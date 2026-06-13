# Expected TAT API — Specification

> **When to load**: User asks about delivery time estimates, turn-around time, TAT, expected delivery dates, or transit time between pincodes.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/dc/expected_tat` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Get expected Turn Around Time (TAT) for a shipment based on origin and destination pincodes |
| **Avg Latency (Prod)** | 158.41ms |
| **P99 Latency (Prod)** | 366.49ms |
| **Rate Limit** | 750 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Expected TAT API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to get the expected Turn Around Time (TAT) for a shipment based on origin and destination pincodes.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Expected TAT
    description: Operations related to expected Turn Around Time (TAT) calculation

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
    ExpectedTATRequest:
      type: object
      properties:
        origin_pin:
          type: string
          description: The pin code of the shipment's origin location
          example: "122003"
        destination_pin:
          type: string
          description: The pin code of the shipment's destination location
          example: "136118"
        mot:
          type: string
          description: "Mode of Transport: 'S' for Surface, 'E' for Express, 'N' for NDD (Next Day Delivery)"
          enum: [S, E, N]
          example: S
        pdt:
          type: string
          description: "Product Type: 'B2B', 'B2C', or empty (defaults to B2C if not provided)"
          enum: [B2B, B2C]
          example: B2C
        expected_pickup_date:
          type: string
          description: "Datetime when pickup will be done. Based on this date, the response will show an expected delivery date considering the TAT and holidays in between. Format: YYYY-MM-DD HH:mm"
          example: "2024-05-31 10:00"
      required:
        - origin_pin
        - destination_pin
        - mot

    SuccessResponse:
      type: object
      properties:
        msg:
          type: string
          description: Response message
          example: ""
        data:
          type: object
          properties:
            tat:
              type: integer
              description: Expected Turn Around Time in days
              example: 3
            expected_delivery_date:
              type: string
              format: date
              description: Expected delivery date in YYYY-MM-DD format
              example: "2024-06-03"
        success:
          type: boolean
          description: Indicates if the request was successful
          example: true

    ErrorResponse:
      type: object
      properties:
        msg:
          type: string
          description: Error message
        data:
          type: string
          description: Error data (usually empty string)
          example: ""
        success:
          type: boolean
          description: Indicates if the request was successful
          example: false

    InvalidTokenResponse:
      type: object
      properties:
        detail:
          type: string
          description: Error detail message
          example: "Invalid token"

paths:
  /api/dc/expected_tat:
    get:
      tags:
        - Expected TAT
      summary: Get expected Turn Around Time (TAT)
      description: |
        Returns the expected Turn Around Time (TAT) for a shipment based on origin and destination pincodes, mode of transport, product type, and expected pickup date.
      operationId: getExpectedTAT
      security:
        - TokenAuth: []
      parameters:
        - name: origin_pin
          in: query
          required: true
          description: The pin code of the shipment's origin location
          schema:
            type: string
          example: "122003"
        - name: destination_pin
          in: query
          required: true
          description: The pin code of the shipment's destination location
          schema:
            type: string
          example: "136118"
        - name: mot
          in: query
          required: true
          description: "Mode of Transport: 'S' for Surface, 'E' for Express, 'N' for NDD (Next Day Delivery)"
          schema:
            type: string
            enum: [S, E, N]
          example: S
        - name: pdt
          in: query
          required: false
          description: "Product Type: 'B2B', 'B2C', or empty (defaults to B2C if not provided)"
          schema:
            type: string
            enum: [B2B, B2C]
          example: B2C
        - name: expected_pickup_date
          in: query
          required: false
          description: "Datetime when pickup will be done. Format: YYYY-MM-DD HH:mm"
          schema:
            type: string
          example: "2024-05-31 10:00"
      responses:
        '200':
          description: Successful response with expected TAT information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'
              example:
                msg: ""
                data:
                  tat: 3
                  expected_delivery_date: "2024-06-03"
                success: true
        '400':
          description: Bad Request - Invalid parameters or missing required fields
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                missingBothPins:
                  summary: Missing origin and destination pins
                  value:
                    msg: "Unable to process request. Origin pin missing. Destination pin missing."
                    data: ""
                    success: false
                missingOriginPin:
                  summary: Missing origin pin
                  value:
                    msg: "Unable to process request. Origin pin missing."
                    data: ""
                    success: false
                missingDestinationPin:
                  summary: Missing destination pin
                  value:
                    msg: "Unable to process request. Destination pin missing."
                    data: ""
                    success: false
                originPinNotServiceable:
                  summary: Origin pin not serviceable
                  value:
                    msg: "Origin pin not serviceable."
                    data: ""
                    success: false
        '403':
          description: Forbidden - Invalid authentication token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InvalidTokenResponse'
              example:
                detail: "Invalid token"
```

---

## CRITICAL: Auth Error Returns 403, Not 401

Unlike most other Delhivery APIs that return 401 for auth failures, this API returns **403 Forbidden** with:

```json
{"detail": "Invalid token"}
```

---

## Query Parameters

| Parameter | In | Required | Type | Description |
|-----------|----|----------|------|-------------|
| `origin_pin` | query | Yes | string | The pin code of the shipment's origin location |
| `destination_pin` | query | Yes | string | The pin code of the shipment's destination location |
| `mot` | query | Yes | string | Mode of Transport: `S` (Surface), `E` (Express), `N` (NDD — Next Day Delivery) |
| `pdt` | query | No | string | Product Type: `B2B`, `B2C`, or empty (defaults to `B2C`) |
| `expected_pickup_date` | query | No | string | Datetime when pickup will be done (`YYYY-MM-DD HH:mm`). Response considers TAT and holidays. |

---

## Success Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if request succeeded |
| `msg` | string | Empty on success |
| `data.tat` | integer | Expected TAT in days |
| `data.expected_delivery_date` | string (date) | Expected delivery date (`YYYY-MM-DD`) |

---

## Error Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `false` |
| `msg` | string | Error message describing the issue |
| `data` | string | Empty string on error |

---

## Known 400 Error Messages

| `msg` value | Cause |
|-------------|-------|
| `"Unable to process request. Origin pin missing. Destination pin missing."` | Both pincodes missing |
| `"Unable to process request. Origin pin missing."` | Origin pincode missing |
| `"Unable to process request. Destination pin missing."` | Destination pincode missing |
| `"Origin pin not serviceable."` | Origin pincode not in Delhivery network |

These are all **business logic results** — do NOT retry. See `expected_tat/retry.md`.

---

## Important Notes

| Note | Detail |
|------|--------|
| **TAT starts from handover** | The TAT begins from the moment the shipment is handed over to Delhivery, not from order placement |
| **TAT varies by network performance** | TAT is determined by current network performance and may vary based on persistent delays in certain lanes. Current network TAT may be faster than the promised TAT at onboarding time |
| **Lane-specific cutoffs** | Different lanes may have unique cutoffs, which can affect expected delivery times |
| **Holiday / Sunday adjustment** | If the expected delivery date falls on a holiday or Sunday, it will be adjusted to the next non-holiday working day |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Expecting 401 for invalid token | This API returns **403** with `{"detail": "Invalid token"}` |
| Retrying on `success: false` | Business logic response — pincode not serviceable, won't change on retry |
| Missing `mot` parameter | Required — API will fail without it |
| Not accounting for holidays | Expected delivery date auto-adjusts for holidays/Sundays — don't add extra buffer |
| Using wrong `expected_pickup_date` format | Must be `YYYY-MM-DD HH:mm`, not just `YYYY-MM-DD` |
