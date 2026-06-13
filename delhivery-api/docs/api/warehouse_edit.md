# Client Warehouse Edit API — Specification

> **When to load**: User asks about updating warehouse details, changing warehouse address/phone/pincode, or modifying an existing pickup location.

---

## Overview

This API is used to edit/update an existing Warehouse.

### Important Constraints

- **Warehouse name cannot be updated.**
- You must provide the warehouse name along with the fields you wish to update.
- Only the parameters listed below can be updated for the given warehouse name.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/backend/clientwarehouse/edit/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Success Status** | **200** OK |
| **Purpose** | Update details of an existing client warehouse (pickup location) |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| **Average Latency (Production)** | 345.65 ms |
| **P99 Latency (Production)** | 61.16 s |
| **Rate Limit (Requests/5 Minute/IP)** | NA |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Edit Client Warehouse API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to update details of an existing client warehouse (pickup location) such as address, phone number, and pincode.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Client Warehouse
    description: Operations related to client warehouse creation and management

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
    EditClientWarehouseRequest:
      type: object
      properties:
        name:
          type: string
          description: Warehouse name in our system for which the details need to be updated
          example: "registered_wh_name"
        address:
          type: string
          description: Address that needs to be updated
          example: "HUDA Market, Gurugram, Haryana - 122001"
        pin:
          type: string
          description: Pincode for the warehouse that needs to be updated
          example: "110042"
        phone:
          type: string
          description: Phone number that needs to be updated
          example: "9988******"
      required:
        - name
        - pin

    BusinessHours:
      type: object
      additionalProperties:
        type: object
        properties:
          start_time:
            type: string
            format: time
            description: Start time in HH:MM format
            example: "09:30"
          close_time:
            type: string
            format: time
            description: Close time in HH:MM format
            example: "18:30"

    EditClientWarehouseResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: true
        error:
          type: string
          description: Error message (empty string when successful)
          example: ""
        data:
          type: object
          properties:
            name:
              type: string
              description: Warehouse name
              example: "test_name12"
            business_hours:
              $ref: '#/components/schemas/BusinessHours'
            business_days:
              type: array
              items:
                type: string
                enum: [MON, TUE, WED, THU, FRI, SAT, SUN]
              description: Business days
              example: ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
            pincode:
              type: integer
              description: Pincode
              example: 110042
            type_of_clientwarehouse:
              type: string
              nullable: true
              description: Type of client warehouse
              example: null
            phone:
              type: string
              description: Contact phone number
              example: "9999999966"
            client:
              type: string
              description: Client identifier
              example: "0080e1-KPChashmaGhar-do-cdp"
            address:
              type: string
              description: Warehouse address
              example: "HUDA Market, Gurugram, Haryana - 122001"
            active:
              type: boolean
              description: Whether the warehouse is active
              example: true
            message:
              type: string
              description: Success message
              example: "client warehouse has been updated in HQ(Delhivery)."
            largest_vehicle_constraint:
              type: string
              nullable: true
              description: Largest vehicle constraint
              example: null

    EditClientWarehouseErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: false
        message:
          type: string
          description: Error message
          example: "warehouse does not exists"
        result:
          type: object
          description: Result object (empty when error occurs)
          example: {}
        error:
          type: object
          description: Error object (empty when error occurs)
          example: {}

paths:
  /api/backend/clientwarehouse/edit/:
    post:
      tags:
        - Client Warehouse
      summary: Edit client warehouse
      description: |
        Updates details of an existing client warehouse (pickup location) such as address, phone number, and pincode.
        The warehouse name is required to identify which warehouse to update.
      operationId: editClientWarehouse
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EditClientWarehouseRequest'
            example:
              name: "registered_wh_name"
              phone: "9988******"
              address: "HUDA Market, Gurugram, Haryana - 122001"
      responses:
        '200':
          description: Successful response with updated warehouse details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EditClientWarehouseResponse'
              example:
                success: true
                error: ""
                data:
                  business_hours:
                    WED: { start_time: "09:30", close_time: "18:30" }
                    THU: { start_time: "09:30", close_time: "18:30" }
                    FRI: { start_time: "09:30", close_time: "18:30" }
                    MON: { start_time: "09:30", close_time: "18:30" }
                    TUE: { start_time: "09:30", close_time: "18:30" }
                    SAT: { start_time: "09:30", close_time: "18:30" }
                  name: "test_name12"
                  business_days: ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
                  pincode: 110042
                  type_of_clientwarehouse: null
                  phone: "9999999966"
                  client: "0080e1-KPChashmaGhar-do-cdp"
                  address: "HUDA Market, Gurugram, Haryana - 122001"
                  active: true
                  message: "client warehouse has been updated in HQ(Delhivery)."
                  largest_vehicle_constraint: null
        '400':
          description: Bad Request - Warehouse does not exist or validation errors
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EditClientWarehouseErrorResponse'
              example:
                message: "warehouse does not exists"
                result: {}
                success: false
                error: {}
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Key Details

### Warehouse Name Identifies the Target
The `name` field is used to look up which warehouse to update. It must match the name used during creation **exactly** (case-sensitive).

### Error Format
Different from the Create API — the edit error response uses:
- `message` as a **string** (not an array)
- `error` as an **object** (not an array of strings)
- No `error_code` field

```json
{
  "message": "warehouse does not exists",
  "result": {},
  "success": false,
  "error": {}
}
```

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Warehouse name doesn't exist | Error: `"warehouse does not exists"` — verify name matches exactly |
| Assuming same error format as Create API | Edit uses `message` (string), Create uses `error` (array) |
| Missing `pin` field | Both `name` and `pin` are required for edit |
