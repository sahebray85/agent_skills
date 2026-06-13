# Pickup Request API — Specification

> **When to load**: User asks about scheduling pickups from a warehouse or creating pickup requests.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/fm/request/new/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Create a new pickup request for shipments from a specified client warehouse |
| **Avg Latency (Prod)** | 242.37ms |
| **P99 Latency (Prod)** | 885.95ms |
| **Rate Limit** | 4000 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Pickup Request API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to initiate a pickup request once an order has been manifested and is ready for collection. The pickup request is raised against a registered client warehouse, not the waybill number.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Pickup Request
    description: Operations related to pickup request creation

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
    PickupRequest:
      type: object
      properties:
        pickup_time:
          type: string
          format: time
          description: Pickup time in HH:MM:SS format
          example: "11:00:00"
        pickup_date:
          type: string
          format: date
          description: Pickup date in YYYY-MM-DD format
          example: "2023-12-29"
        pickup_location:
          type: string
          description: Registered client warehouse from where the shipment is to be picked. Also referred to as pickup location.
          example: "warehouse_name"
        expected_package_count:
          type: integer
          description: Expected number of packages for pickup
          example: 1
      required:
        - pickup_time
        - pickup_date
        - pickup_location
        - expected_package_count

    PickupRequestResponse:
      type: object
      properties:
        pickup_location_name:
          type: string
          description: Name of the pickup location
          example: "fsdfdfsdffs"
        client_name:
          type: string
          description: Client name
          example: "2cb057-Zappship-do-cdp"
        pickup_time:
          type: string
          format: time
          description: Pickup time
          example: "14:00:00"
        pickup_id:
          type: integer
          description: Unique pickup request ID
          example: 118775
        incoming_center_name:
          type: string
          description: Name of the incoming center
          example: "Mumbai MIDC"
        expected_package_count:
          type: integer
          description: Expected number of packages
          example: 1
        pickup_date:
          type: string
          format: date
          description: Pickup date
          example: "2026-02-07"

    PickupRequestErrorResponse:
      type: object
      properties:
        pickup_location:
          type: string
          description: Error message for invalid pickup location
          example: "Invalid Pickup Location ClientWarehouse matching query does not exist."

paths:
  /fm/request/new/:
    post:
      tags:
        - Pickup Request
      summary: Create new pickup request
      description: |
        Creates a new pickup request for shipments from a specified client warehouse.
        The pickup request is raised against the warehouse, not the waybill number. All parameters are mandatory.
      operationId: createPickupRequest
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PickupRequest'
            example:
              pickup_time: "11:00:00"
              pickup_date: "2023-12-29"
              pickup_location: "warehouse_name"
              expected_package_count: 1
      responses:
        '200':
          description: Successful response with pickup request details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PickupRequestResponse'
              example:
                pickup_location_name: "fsdfdfsdffs"
                client_name: "2cb057-Zappship-do-cdp"
                pickup_time: "14:00:00"
                pickup_id: 118775
                incoming_center_name: "Mumbai MIDC"
                expected_package_count: 1
                pickup_date: "2026-02-07"
        '400':
          description: Bad Request - Invalid pickup location or other validation errors
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PickupRequestErrorResponse'
              example:
                pickup_location: "Invalid Pickup Location ClientWarehouse matching query does not exist."
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

### All Parameters Are Required

Unlike most other Delhivery APIs, **every** parameter is mandatory:

| Parameter | Type | Format | Example |
|-----------|------|--------|---------|
| `pickup_time` | string | `HH:MM:SS` | `"11:00:00"` |
| `pickup_date` | string | `YYYY-MM-DD` | `"2023-12-29"` |
| `pickup_location` | string | Registered client warehouse name | `"warehouse_name"` |
| `expected_package_count` | integer | — | `1` |

### `pickup_location` Must Match an Existing Warehouse

The value must be a registered warehouse name. If it doesn't match, the API returns 400:

```json
{
  "pickup_location": "Invalid Pickup Location ClientWarehouse matching query does not exist."
}
```

This means the warehouse must be created first (via the Warehouse Create API) before a pickup can be scheduled.

### Response Returns Assigned Pickup Details

On success, the response includes:
- `pickup_id` — unique identifier for tracking the pickup request
- `incoming_center_name` — the Delhivery center assigned to handle the pickup
- `pickup_time` — may differ from the requested time (server assigns actual slot)

---

## Important Notes

| Note | Detail |
|------|--------|
| **Raised against warehouse, not waybill** | The pickup request is raised against the warehouse location, not the waybill number. One request per location covers all waybills being picked up from that location. If shipments are at two different locations, raise separate pickup requests for each. |
| **One active request per day per warehouse** | For any given day, a second pickup request can be raised for a warehouse only when the existing pickup request is closed. |
| **Create when packed and ready** | The right time to create a pickup request is when the shipment is packed and ready to be handed over to the Field Executive (FE). |
| **API is optional** | Pickup requests can also be created from the One Panel. Additionally, you can enable auto-pickup for your account with assistance from your account POC. |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Using a warehouse name that doesn't exist | Create the warehouse first via Warehouse Create API, use exact registered name |
| Wrong date format | Must be `YYYY-MM-DD`, not `DD-MM-YYYY` or `MM/DD/YYYY` |
| Wrong time format | Must be `HH:MM:SS` (24-hour), not `HH:MM` or 12-hour format |
| Assuming returned `pickup_time` matches request | Server may assign a different pickup slot |
| Omitting any parameter | All four parameters are required — omitting any will cause a validation error |
| Creating a second request for same day while one is active | A second pickup request can only be raised when the existing one for that day is closed |
| Creating request before shipment is packed | Create the pickup request only when shipment is packed and ready for FE handover |
| Creating per-waybill pickup requests | Pickup is per warehouse, not per waybill — one request covers all waybills at that location |
