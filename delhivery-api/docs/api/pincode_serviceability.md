# Pincode Serviceability API — Specification

> **When to load**: User asks about pincode checks, serviceability validation, "is this pincode deliverable?", or pre-shipment validation.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/c/api/pin-codes/json/?filter_codes={pincode}` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Check whether the consignee's pincode is serviceable by Delhivery (B2C). Must be checked before order creation. |
| **Avg Latency (Prod)** | 86.02ms |
| **P99 Latency (Prod)** | 98.22ms |
| **Rate Limit** | 4500 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Pincode Serviceability API
  description: |
    API specification for Delhivery Last Mile Express system. This API provides the serviceability of the consignee's pin code (B2C). If the pin code is serviceable, only then should order creation or any further API be used.

    ## Rate Limit and Latency

    | Metrics | Value |
    |---|---|
    | Average Latency (PRODUCTION) | 86.02ms |
    | P99 Latency (PRODUCTION) | 98.22ms |
    | Rate Limit (Requests/5 Minute/IP) (PRODUCTION) | 4500 |

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Pin Codes
    description: Operations related to postal pin codes and serviceability

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

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Error message
      example:
        error: Invalid Client name

paths:
  /c/api/pin-codes/json/?filter_codes={pincode}:
    get:
      tags:
        - Pin Codes
      summary: Get serviceable delivery pin codes
      description: |
        Provides the serviceability of the consignee's pin code (B2C). If `filter_codes` is provided, returns only the specified pin code if serviceable. If not passed, returns both serviceable and embargoed pincodes.
      operationId: getServiceableDeliveryPinCodes
      security:
        - TokenAuth: []
      parameters:
        - name: filter_codes
          required: false
          description: |
            Pincode for which the serviceability needs to be checked. Pass one pincode at a time.
            Only serviceable pin codes that support delivery will be returned.
            Invalid pin codes will be ignored.
            If not passed, the API returns both serviceable and embargoed pincodes.
          schema:
            type: integer
          example: 194103
      responses:
        '200':
          description: Successful response with serviceable delivery codes
          content:
            application/json:
              examples:
                serviceable:
                  summary: Serviceable pincode
                  type: object
                  value:
                    delivery_codes:
                      - postal_code:
                          - remark: ""
                temporaryDisable:
                  summary: Temporarily disabled (Embargo)
                  type: object
                  value:
                    delivery_codes:
                      - postal_code:
                          - remark: "Embargo"
                nonServiceable:
                  summary: Non-serviceable pincode
                  type: object
                  value:
                    delivery_codes: []
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              example:
                error: There has been an error but we were asked to not let you see that. Please contact the dev team.
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              example:
                error: There has been an error but we were asked to not let you see that. Please contact the dev team.
```

---

## Response Interpretation Guide

### Determining Serviceability

1. Check HTTP status = 200
2. Parse response body → get `delivery_codes` array
3. If array is **empty** → Pincode is **Non-Serviceable Zone (NSZ)**
4. If array has entries → check `remark` field:
   - Empty string (`""`) → **Serviceable** — order creation and further APIs can proceed
   - `"Embargo"` → **Temporary NSZ** — pincode is temporarily non-serviceable

### When `filter_codes` Is Not Passed

If `filter_codes` is omitted, the API returns **both serviceable and embargoed** pincodes. Always pass a specific pincode to check its serviceability.

---

## Important Notes

- This is a **pre-check API** — if the pin code is serviceable, only then should order creation or any further API be used.
- Pass **one pincode at a time** in `filter_codes`.
- If `filter_codes` is not passed, the API returns both serviceable and embargoed pincodes.
- In the response, `remark` as `"Embargo"` indicates **temporary NSZ** (Non-Serviceable Zone), while a blank remark means the pincode is serviceable.

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Not handling empty `delivery_codes` array | Empty array = non-serviceable, not an error |
| Assuming non-empty array = serviceable | Also check `remark` for `"Embargo"` |
| Not validating pincode format before API call | Validate: 6-digit numeric (100000–999999) |
| Skipping serviceability check before order creation | Always check serviceability first — only proceed with order creation if pincode is serviceable |
| Not passing `filter_codes` | Without it, API returns all serviceable + embargoed pincodes — always pass specific pincode |

---

## Related APIs

| API | Difference |
|-----|-----------|
| **Bulk Client Pincode Serviceability** | Uses query parameter `?filter_codes=`. For enterprise/bulk checks. Returns different service type format. |
