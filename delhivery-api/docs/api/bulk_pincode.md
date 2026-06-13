# Heavy Serviceability Pincode API — Specification

> **When to load**: User asks about checking pincode serviceability for Heavy product type shipments, heavy shipment delivery checks, or whether a pincode supports heavy delivery.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/dc/fetch/serviceability/pincode` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Check pincode serviceability for Heavy product type shipments |
| **Avg Latency (Prod)** | 75.89ms |
| **P99 Latency (Prod)** | 77.77ms |
| **Rate Limit** | 3000 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Heavy Serviceability Pincode API
  description: |
    API specification for Delhivery Last Mile Express system. This API provides the serviceability of the pincode for heavy shipments. It is used to validate whether the pincodes are serviceable for the clients having product type Heavy, in Delhivery's network. An "NSZ" response means the PIN code is not serviceable. The `payment_type` in the response indicates whether the Pincode is serviceable or not for that Payment mode.

    ## Rate Limit and Latency

    | Metrics | Value |
    |---|---|
    | Average Latency (PRODUCTION) | 75.89ms |
    | P99 Latency (PRODUCTION) | 77.77ms |
    | Rate Limit (Requests/5 Minute/IP) (PRODUCTION) | 3000 |

  x-performance-metrics:
    production:
      average-latency: "75.89ms"
      p99-latency: "77.77ms"
  x-rate-limit:
    production:
      requests-per-5-minutes-per-ip: 3000

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Heavy Serviceability
    description: Operations related to pincode serviceability check for Heavy product type

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
    PostalCode:
      type: object
      properties:
        pincode:
          type: integer
          description: The postal pin code
          example: 194103
      required:
        - pincode

    HeavyServiceabilitySuccessResponse:
      type: object
      properties:
        b2b_fail_on_demand_pincodes:
          type: array
          items:
            type: string
          description: List of B2B fail-on-demand pincodes
        data:
          type: array
          items:
            type: object
          description: Serviceability data for the pincode
        success:
          type: boolean
          description: Whether the request was successful
        error:
          type: string
          description: Error message (empty string on success)
      required:
        - b2b_fail_on_demand_pincodes
        - data
        - success
        - error

    HeavyServiceabilityErrorResponse:
      type: object
      properties:
        b2b_fail_on_demand_pincodes:
          type: array
          items:
            type: string
          description: List of B2B fail-on-demand pincodes
        data:
          type: array
          items:
            type: object
          description: Empty data array on error
        success:
          type: boolean
          description: false when the pincode is invalid
        error:
          type: string
          description: Error message describing the issue
      required:
        - b2b_fail_on_demand_pincodes
        - data
        - success
        - error

    UnauthorizedResponse:
      type: object
      properties:
        detail:
          type: string
          description: Error detail message
      required:
        - detail

paths:
  /api/dc/fetch/serviceability/pincode:
    get:
      tags:
        - Heavy Serviceability
      summary: Check pincode serviceability for Heavy product type
      description: |
        Checks whether a given pincode is serviceable for Heavy product type shipments by Delhivery. Pass one pincode at a time.
      operationId: getHeavyServiceabilityPincode
      security:
        - TokenAuth: []
      parameters:
        - name: pincode
          in: query
          required: true
          description: |
            Pincode for which the serviceability needs to be checked. Pass one pincode at a time.
          schema:
            type: integer
            minimum: 100000
            maximum: 999999
          example: 400086
        - name: product_type
          in: query
          required: true
          description: |
            Product type of the account. Pass "Heavy" for heavy product type serviceability check.
          schema:
            type: string
            enum:
              - Heavy
          example: "Heavy"
      responses:
        '200':
          description: Response for serviceability check
          headers:
            X-RateLimit-Limit:
              description: Maximum number of requests allowed per 5 minutes per IP
              schema:
                type: integer
                example: 3000
            X-RateLimit-Remaining:
              description: Number of requests remaining in the current rate limit window
              schema:
                type: integer
            X-RateLimit-Reset:
              description: Time in seconds until the rate limit window resets
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HeavyServiceabilitySuccessResponse'
              examples:
                serviceable_pincode:
                  summary: Pincode is serviceable
                  value:
                    b2b_fail_on_demand_pincodes: []
                    data: []
                    success: true
                    error: ""
                invalid_pincode:
                  summary: Invalid pincode provided
                  value:
                    b2b_fail_on_demand_pincodes: []
                    data: []
                    success: false
                    error: "40008e is not valid pin"
        '429':
          description: Too Many Requests - Rate limit exceeded (3000 requests per 5 minutes per IP)
          headers:
            Retry-After:
              description: Time in seconds until the rate limit window resets
              schema:
                type: integer
          content:
            application/json:
              example:
                error: Rate limit exceeded. Please retry after some time.
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedResponse'
              examples:
                invalid_token:
                  summary: Invalid authentication token
                  value:
                    detail: "Invalid token"
```

---

## Query Parameters

| Parameter | In | Required | Type | Description |
|-----------|----|----------|------|-------------|
| `pincode` | query | Yes | integer (6-digit) | Pincode to check. One pincode at a time. |
| `product_type` | query | Yes | string | Must be `"Heavy"` |

---

## CRITICAL: One Pincode at a Time

Unlike the regular Pincode Serviceability API, this API only accepts **one pincode per request**. Do not pass multiple pincodes.

---

## CRITICAL: `product_type` Must Be `"Heavy"`

The `product_type` parameter is required and must be exactly `"Heavy"` (capital H).

---

## Response Interpretation

| Field | Serviceable | Invalid Pincode / NSZ |
|-------|-------------|----------------------|
| `success` | `true` | `false` |
| `error` | `""` (empty string) | Error message (e.g., `"40008e is not valid pin"`) or `"NSZ"` |
| `data` | `[]` | `[]` |
| `b2b_fail_on_demand_pincodes` | `[]` | `[]` |

- **"NSZ"** in the response means the PIN code is **Not Serviceable Zone** — the pincode is not serviceable.
- The **`payment_type`** in the response indicates whether the Pincode is serviceable or not for that specific Payment mode.

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `b2b_fail_on_demand_pincodes` | array of string | List of B2B fail-on-demand pincodes |
| `data` | array of object | Serviceability data for the pincode |
| `success` | boolean | `true` = serviceable, `false` = invalid or not serviceable |
| `error` | string | Empty string on success, error message on failure |

---

## 401 Response

The 401 response uses a different structure from most other Delhivery APIs:

```json
{
  "detail": "Invalid token"
}
```

Note: uses `"detail"` key, not `"error"`.

---

## Known Error Scenarios

| Error | Cause |
|-------|-------|
| `"40008e is not valid pin"` | Non-numeric or invalid pincode |
| `"NSZ"` | Pincode is in a Non-Serviceable Zone |
| `{"detail": "Invalid token"}` | Missing or invalid auth token |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Passing multiple pincodes | Only one pincode per request |
| Missing `product_type` parameter | Must pass `product_type=Heavy` |
| Wrong case for `product_type` | Must be `"Heavy"` (capital H) |
| Expecting `error` key in 401 | 401 uses `"detail"` key, not `"error"` |
| Assuming `data: []` means not serviceable | Check `success` field — `data` can be empty even on success |
