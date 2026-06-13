# Client Warehouse Creation API — Specification

> **When to load**: User asks about registering pickup locations or adding warehouses in Delhivery's system.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/backend/clientwarehouse/create/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Success Status** | **201** Created |
| **Purpose** | Register a pickup location (client warehouse) in Delhivery's system, which is further used to create orders |
| **Avg Latency (Prod)** | 172.45ms |
| **P99 Latency (Prod)** | 396.51ms |
| **Rate Limit** | 10/min/IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Create Client Warehouse API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to register a pickup location (client warehouse) in Delhivery's system, which is further used to create orders. The client's pickup locations or warehouses must be registered in the Delhivery system beforehand.

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
    CreateClientWarehouseRequest:
      type: object
      properties:
        name:
          type: string
          description: Name the warehouse. It will be considered as your pickup location.
          example: "test_name"
        registered_name:
          type: string
          description: Pass your registered account name
          example: "registered_account_name"
        phone:
          type: string
          description: Contact number of the POC of the warehouse
          example: "9999999999"
        email:
          type: string
          format: email
          description: Email address of the POC of the warehouse
          example: "abc@gmail.com"
        address:
          type: string
          description: Complete address of the warehouse
          example: "address"
        city:
          type: string
          description: City in which warehouse is located
          example: "Kota"
        pin:
          type: string
          description: Pincode of the area where the warehouse is located
          example: "110042"
        country:
          type: string
          description: Country where the warehouse is located
          example: "India"
        return_address:
          type: string
          description: Complete return address of the warehouse. It can be the same as the pickup address as well
          example: "return_address"
        return_city:
          type: string
          description: City where the shipment will be returned
          example: "Kota"
        return_pin:
          type: string
          description: Pincode of the city where the shipment will be returned
          example: "110042"
        return_state:
          type: string
          description: State where the shipment will be returned
          example: "Delhi"
        return_country:
          type: string
          description: Country where the shipment will be returned
          example: "India"
      required:
        - name
        - phone
        - pin
        - return_address

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

    CreateClientWarehouseResponse:
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
              example: "test_name"
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
              example: "9999999999"
            client:
              type: string
              description: Client identifier
              example: "0080e1-KPChashmaGhar-do-cdp"
            address:
              type: string
              description: Warehouse address
              example: "address"
            active:
              type: boolean
              description: Whether the warehouse is active
              example: true
            message:
              type: string
              description: Success message
              example: "A new client warehouse has been created in HQ(Delhivery)."
            largest_vehicle_constraint:
              type: string
              nullable: true
              description: Largest vehicle constraint
              example: null
            secondary_phone:
              type: string
              nullable: true
              description: Secondary phone number
              example: null
            other_phone:
              type: string
              nullable: true
              description: Other phone number
              example: null

    CreateClientWarehouseErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: false
        error:
          type: array
          items:
            type: string
          description: Array of error messages
          example: ["Transaction Failed: client-warehouse of client: cms::client::ef9132d1-4f45-11ef-b394-0ec32c24f407 with name: test_name already exists CLIENT_STORES_CREATE"]
        error_code:
          type: array
          items:
            type: integer
          description: Array of error codes
          example: [2000]
        data:
          type: object
          properties:
            name:
              type: string
              description: Warehouse name
              example: "test_name"
            phone:
              type: string
              nullable: true
              description: Contact phone number
              example: null
            address:
              type: string
              nullable: true
              description: Warehouse address
              example: null
            secondary_phone:
              type: string
              nullable: true
              description: Secondary phone number
              example: null
            other_phone:
              type: string
              nullable: true
              description: Other phone number
              example: null
            message:
              type: string
              description: Error message
              example: "some error while creating/updating warehouse"
            business_hours:
              $ref: '#/components/schemas/BusinessHours'
            business_days:
              type: array
              items:
                type: string
              description: Business days
              example: ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
            pincode:
              type: string
              description: Pincode
              example: "110042"

paths:
  /api/backend/clientwarehouse/create/:
    post:
      tags:
        - Client Warehouse
      summary: Register client warehouse (pickup location)
      description: |
        Registers a pickup location (client warehouse) in Delhivery's system with address details, contact information, and return address.
        The warehouse name will be used as the pickup location name in shipment creation and pickup requests.
      operationId: createClientWarehouse
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateClientWarehouseRequest'
            example:
              phone: "9999999999"
              city: "Kota"
              name: "test_name"
              pin: "110042"
              address: "address"
              country: "India"
              email: "abc@gmail.com"
              registered_name: "registered_account_name"
              return_address: "return_address"
              return_pin: "110042"
              return_city: "Kota"
              return_state: "Delhi"
              return_country: "India"
      responses:
        '201':
          description: Successful response with created warehouse details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateClientWarehouseResponse'
              example:
                success: true
                error: ""
                data:
                  business_hours:
                    WED: { start_time: "09:30", close_time: "18:30" }
                    THU: { start_time: "09:30", close_time: "18:30" }
                    TUE: { start_time: "09:30", close_time: "18:30" }
                    MON: { start_time: "09:30", close_time: "18:30" }
                    FRI: { start_time: "09:30", close_time: "18:30" }
                    SAT: { start_time: "09:30", close_time: "18:30" }
                  name: "test_name"
                  business_days: ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
                  pincode: 110042
                  type_of_clientwarehouse: null
                  phone: "9999999999"
                  client: "0080e1-KPChashmaGhar-do-cdp"
                  address: "address"
                  active: true
                  message: "A new client warehouse has been created in HQ(Delhivery)."
                  largest_vehicle_constraint: null
        '400':
          description: Bad Request - Validation errors or duplicate warehouse
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateClientWarehouseErrorResponse'
              examples:
                duplicateWarehouse:
                  summary: Warehouse already exists
                  value:
                    error_code: [2000]
                    data:
                      business_hours:
                        WED: { start_time: "09:30", close_time: "18:30" }
                        THU: { start_time: "09:30", close_time: "18:30" }
                        TUE: { start_time: "09:30", close_time: "18:30" }
                        MON: { start_time: "09:30", close_time: "18:30" }
                        FRI: { start_time: "09:30", close_time: "18:30" }
                        SAT: { start_time: "09:30", close_time: "18:30" }
                      name: "test_name"
                      pincode: "110042"
                      phone: "9999999999"
                      address: "address"
                      secondary_phone: null
                      message: "some error while creating/updating warehouse"
                      other_phone: null
                      business_days: ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
                    success: false
                    error: ["Transaction Failed: client-warehouse of client: cms::client::ef9132d1-4f45-11ef-b394-0ec32c24f407 with name: test_name already exists CLIENT_STORES_CREATE"]
                missingRequiredFields:
                  summary: Missing required fields
                  value:
                    error_code: [1000]
                    data:
                      name: "test_name12"
                      phone: null
                      address: null
                      secondary_phone: null
                      message: "some error while creating/updating warehouse"
                      other_phone: null
                    success: false
                    error: ["address: address is required", "pin: pin is required", "return_address: return_address is required", "return_pin: return_pin is required"]
                invalidFieldTypes:
                  summary: Invalid field types
                  value:
                    error_code: [1000]
                    data:
                      name: "test_name12"
                      phone: null
                      address: null
                      secondary_phone: null
                      message: "some error while creating/updating warehouse"
                      other_phone: null
                    success: false
                    error: ["address: address must be a string", "pin: pin must be a string", "return_address: return_address must be a string", "return_pin: return_pin must be a string"]
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

### Warehouse Name is the Identifier
The `name` field is how you reference this warehouse across all other APIs. When creating a shipment or scheduling a pickup, the `pickup_location` must match the warehouse `name` **exactly** (case-sensitive). A mismatch causes: `"Invalid Pickup Location ClientWarehouse matching query does not exist."`

### Error Codes

| Code | Meaning |
|------|---------|
| 2000 | Duplicate — warehouse with this name already exists |
| 1000 | Validation — missing required fields or invalid field types |

### Error Format
The `error` field is an **array of strings** (not a single string). Each string is a separate validation error. The `error_code` field is also an array.

---

## Important Notes

| Note | Detail |
|------|--------|
| **Must register before creating orders** | The client's pickup locations or warehouses, where shipments will be physically picked up, must be registered in the Delhivery system beforehand. |
| **Warehouse name is case-sensitive** | Whatever name you register with this API, make sure the exact same warehouse name is used while creating orders or scheduling pickups. |
| **Return address is required** | A return address must be configured for each warehouse, which can either be the warehouse itself or some other address. |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Missing `return_address` | Required field even if same as warehouse address |
| Warehouse name collision | Error code `2000` = already exists. Use a unique name. |
| Expecting 200 on success | Create returns **201**, not 200 |
| Treating `error` as a string | It's an **array of strings** — iterate over it |
| Warehouse name mismatch in other APIs | Name must match exactly (case-sensitive) in Shipment Creation and Pickup Request |
