# Update E-Waybill API — Specification

> **When to load**: User asks about updating e-waybill numbers, attaching EWB to shipments, or updating invoice numbers (DCN) on existing shipments.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | PUT |
| **Path** | `/api/rest/ewaybill/{waybill}/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Update e-waybill (EWB) numbers and invoice numbers (DCN) for a shipment |
| **Avg Latency (Prod)** | 327.6ms |
| **P99 Latency (Prod)** | 501.68ms |
| **Rate Limit** | 250/5 min/IP |

---

## What Is an E-Way Bill?

An **E-Way Bill** is an electronic document (having details such as the goods being transported, their value, the sender, the receiver, and the route) that is **required for the transportation of goods having shipment value > ₹50k** as per Indian government laws.

- Use this API to update the e-waybill of shipments having value > ₹50k.
- This API updates the **forward E-waybill** when the shipment is in the forward flow, and updates the **return E-waybill** when the shipment is in the return flow.

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Update E-waybill API
  description: |
    API specification for Delhivery Last Mile Express system. An E-Way Bill is an electronic document (having details such as the goods being transported, their value, the sender, the receiver, and the route) that is required for the transportation of goods having shipment value > ₹50k as per Indian government laws. This API is used to update e-waybill (EWB) numbers and invoice numbers (DCN) for shipments. It updates the forward E-waybill when the shipment is in the forward flow, and updates the return E-waybill when the shipment is in the return flow.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: E-waybill
    description: Operations related to e-waybill management and updates

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
    EwaybillUpdateItem:
      type: object
      properties:
        dcn:
          type: string
          description: Pass the invoice number
          example: "pass the invoice number"
        ewbn:
          type: string
          description: Pass the e-waybill (EWB) number that needs to be updated
          example: "pass the ewb number"
      required:
        - dcn
        - ewbn

    UpdateEwaybillRequest:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/EwaybillUpdateItem'
          description: Array of e-waybill update items
          minItems: 1
      required:
        - data

    UpdateEwaybillSuccessResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: true
        message:
          type: string
          description: Success message
          example: "Ewaybills updated successfully"

    UpdateEwaybillErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: false
        message:
          type: string
          description: Error message
          example: "Package not found"

paths:
  /api/rest/ewaybill/{waybill}/:
    put:
      tags:
        - E-waybill
      summary: Update e-waybill
      description: |
        Updates e-waybill (EWB) number and invoice number (DCN) for a shipment identified by waybill number.
        Multiple e-waybill updates can be provided in the data array.
      operationId: updateEwaybill
      security:
        - TokenAuth: []
      parameters:
        - name: waybill
          in: path
          required: true
          description: Delhivery waybill number
          schema:
            type: string
          example: "XXXXXXXXXX"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateEwaybillRequest'
            example:
              data:
                - dcn: "pass the invoice number"
                  ewbn: "pass the ewb number"
      responses:
        '201':
          description: Successful response indicating e-waybills were updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateEwaybillSuccessResponse'
              example:
                success: true
                message: "Ewaybills updated successfully"
        '200':
          description: Response indicating failure or validation errors
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateEwaybillErrorResponse'
              examples:
                packageNotFound:
                  summary: Package not found
                  value:
                    success: false
                    message: "Package not found"
                invalidEwaybill:
                  summary: Invalid e-waybill pattern
                  value:
                    success: false
                    message: "Following EWBNs are invalid: 123456789123456 - invalid ewaybill pattern; "
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

## Request Structure

```json
PUT /api/rest/ewaybill/{waybill}/

{
  "data": [
    {
      "dcn": "INV-2026-001",
      "ewbn": "123456789012"
    }
  ]
}
```

### Required Parameters

| Parameter | Location | Type | Description |
|-----------|----------|------|-------------|
| `waybill` | path | string | Delhivery waybill number |
| `data` | body | array | Array of e-waybill update items (min 1) |
| `data[].dcn` | body | string | Invoice number |
| `data[].ewbn` | body | string | E-waybill (EWB) number |

Both `dcn` and `ewbn` are **required** in each item.

---

## CRITICAL: Success Returns 201, Business Errors Return 200

| HTTP Status | `success` | Meaning |
|-------------|-----------|---------|
| **201** | `true` | E-waybills updated successfully |
| **200** | `false` | Business logic error (package not found, invalid pattern) |
| **401** | — | Auth failure |
| **400** | — | Bad request |

This is unusual — **errors come back as HTTP 200** with `success: false`. Always check the `success` field, not just the HTTP status code.

---

## CRITICAL: E-Waybill Pattern Validation

The API validates e-waybill numbers against an expected pattern. Invalid patterns return:

```json
{
  "success": false,
  "message": "Following EWBNs are invalid: 123456789123456 - invalid ewaybill pattern; "
}
```

Ensure e-waybill numbers conform to the GST e-waybill format before sending.

---

## CRITICAL: Supports Batch Updates

The `data` array supports multiple e-waybill updates in a single request. Each item needs both `dcn` (invoice number) and `ewbn` (e-waybill number).

---

## Known Error Scenarios

| Error (`message`) | Cause |
|-------------------|-------|
| `"Package not found"` | Waybill in the URL path doesn't match any existing shipment |
| `"Following EWBNs are invalid: ... - invalid ewaybill pattern; "` | E-waybill number doesn't match expected format |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Checking only HTTP status for success | HTTP 200 can mean failure — always check `success` field |
| Assuming 201 for errors | 201 = success, 200 = business error |
| Missing `dcn` field | Both `dcn` (invoice) and `ewbn` (e-waybill) are required per item |
| Invalid e-waybill format | Validate e-waybill pattern before sending |
| Not wrapping items in `data` array | Request body must be `{"data": [...]}`, not a flat object |
| Forgetting trailing slash in URL | Path is `/api/rest/ewaybill/{waybill}/` — note the trailing slash |
