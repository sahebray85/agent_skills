# Update NDR API — Specification

> **When to load**: User asks about reattempting NDR shipments or rescheduling RVP pickups.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/p/update` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Reattempt NDR shipments (RE-ATTEMPT) or reschedule RVP pickups (PICKUP_RESCHEDULE) |
| **Avg Latency (Prod)** | 93.77ms |
| **P99 Latency (Prod)** | 126.38s |
| **Rate Limit** | NA |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Update NDR API
  description: |
    API specification for Delhivery Last Mile Express system. Used to reattempt NDR shipments (RE-ATTEMPT) or reschedule RVP pickups (PICKUP_RESCHEDULE). This is an asynchronous API — it returns a UPL ID (request_id) confirming the update request was received. The UPL ID is then used in the GET NDR Status API to check the status of the NDR update.

    **Important Notes:**
    - A maximum of 1000 shipments can be updated in a single API call. Split the request into multiple calls if needed.
    - The "data" field in the payload must be a list format.
    - Both "waybill" and "act" fields are mandatory in each item of the data array.

    **RE-ATTEMPT Action Requirements:**
    - The package should be in Pending state.
    - The current NSL code for the shipment must be in the list: `EOD-74`, `EOD-15`, `EOD-104`, `EOD-43`, `EOD-86`, `EOD-11`, `EOD-69`, `EOD-6`.

    **PICKUP_RESCHEDULE Action Requirements:**
    - The package status should be CN and the shipment status should be "Canceled".
    - The shipment attempt count must be 1 or 2.
    - The waybill must belong to the client's account.
    - The shipment must not be part of an open dispatch.
    - Allowed only when the package has the current NSL as "EOD-777 (RVP QC Fail)" or "EOD-21 (Pickup request canceled)", where "EOD-21" must be non-OTP verified.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: NDR Update
    description: Reattempt NDR shipments or reschedule RVP pickups

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
    NDRUpdateItem:
      type: object
      properties:
        waybill:
          type: string
          description: Waybill for which NDR needs to be applied
          example: "13163116xxxxxx"
        act:
          type: string
          description: |
            Action needs to be passed here.
            - RE-ATTEMPT: Can be taken on the AWB if AWB is in Pending state and the current NSL code is in: EOD-74, EOD-15, EOD-104, EOD-43, EOD-86, EOD-11, EOD-69, EOD-6.
            - PICKUP_RESCHEDULE: Allowed only when package status is CN (Canceled), attempt count is 1 or 2, and current NSL is EOD-777 (RVP QC Fail) or EOD-21 (Pickup request canceled, non-OTP verified).
          enum: [RE-ATTEMPT, PICKUP_RESCHEDULE]
          example: "RE-ATTEMPT"
      required:
        - waybill
        - act

    UpdateNDRRequest:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/NDRUpdateItem'
          description: Array of NDR update items. Maximum 1000 items per request.
          minItems: 1
          maxItems: 1000
      required:
        - data

    UpdateNDRResponse:
      type: object
      properties:
        message:
          type: string
          description: Success message
          example: "Request submitted successfully!"
        request_id:
          type: string
          description: UPL ID — use this in the GET NDR Status API to check the status of the NDR update
          example: "UPL17749083484755923441"

paths:
  /api/p/update:
    post:
      tags:
        - NDR Update
      summary: Reattempt NDR shipments or reschedule RVP pickups
      description: |
        Reattempt NDR shipments (RE-ATTEMPT) or reschedule RVP pickups (PICKUP_RESCHEDULE). This is an asynchronous API — it returns a UPL ID (request_id) confirming the update request was received. Use the GET NDR Status API with the UPL ID to check the status of the update.
        Multiple waybills can be updated in a single request by passing multiple items in the data array.
        A maximum of 1000 shipments can be updated in a single API call.
      operationId: updateNDR
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateNDRRequest'
            example:
              data:
                - waybill: "13163116xxxxxx"
                  act: "RE-ATTEMPT"
      responses:
        '200':
          description: Successful response indicating the request was submitted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateNDRResponse'
              examples:
                success:
                  summary: Request submitted successfully
                  value:
                    message: "Request submitted successfully!"
                    request_id: "UPL17749083484755923441"
        '403':
          description: Forbidden - Insufficient permissions or invalid request
          content:
            application/json:
              schema:
                type: string
              examples:
                forbidden:
                  summary: Forbidden error
                  value: "There has been an error but we were asked to not let you see that. Please contact the dev team."
                unauthorized_client:
                  summary: Unauthorized client/user
                  value: "Unauthorized client/user"
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
              examples:
                invalid_data:
                  summary: Invalid data format - data field is not a list
                  value: "Invalid data provided"
                max_records_exceeded:
                  summary: More than 1000 records in data array
                  value: "Can not update more than 1000 records"
                missing_waybill:
                  summary: Waybill field is missing in data payload
                  value: "\"waybill\" is missing"
                invalid_action:
                  summary: Action is not valid
                  value: "Action is not valid"
                incorrect_status:
                  summary: Package in incorrect status for NDR action
                  value: "Package in incorrect status"
                action_in_progress:
                  summary: Package action is currently being performed
                  value: "Package action is being performed"
                package_not_canceled:
                  summary: Package should be in Canceled status for PICKUP_RESCHEDULE
                  value: "Package should be in Canceled status"
                max_attempt_reached:
                  summary: Shipment has reached maximum attempt count
                  value: "Shipment has reached max attempt count"
                incorrect_waybill:
                  summary: Waybill does not match client account
                  value: "Incorrect waybill"
                part_of_dispatch:
                  summary: Package is part of an open dispatch
                  value: "Package is part of dispatch. Cannot update the information now"
                rescheduling_not_allowed:
                  summary: Package does not meet conditions for PICKUP_RESCHEDULE
                  value: "Rescheduling is not allowed as package should be in canceled status"
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              examples:
                unauthorized:
                  summary: Invalid or missing token
                  value: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Request Structure

```json
POST /api/p/update

{
  "data": [
    {
      "waybill": "13163116xxxxxx",
      "act": "RE-ATTEMPT"
    }
  ]
}
```

### Required Fields Per Item

| Field | Type | Enum Values | Description |
|-------|------|-------------|-------------|
| `waybill` | string | — | Waybill number for the NDR |
| `act` | string | `RE-ATTEMPT`, `PICKUP_RESCHEDULE` | Action to take |

---

## Available Actions

| Action | Description |
|--------|-------------|
| `RE-ATTEMPT` | Request another delivery attempt for a NPR shipment |
| `PICKUP_RESCHEDULE` | Reschedule the pickup for a canceled RVP shipment |

---

## RE-ATTEMPT Action Requirements

The `RE-ATTEMPT` action can only be applied when **both** conditions are met:

1. The package must be in **Pending** state.
2. The current NSL (Non-delivery Status Label) code must be one of:

| NSL Code |
|----------|
| `EOD-74` |
| `EOD-15` |
| `EOD-104` |
| `EOD-43` |
| `EOD-86` |
| `EOD-11` |
| `EOD-69` |
| `EOD-6` |

If the package is not in Pending state or the NSL code is not in the above list, the API returns: `"Package in incorrect status"`.

**Best Practices for RE-ATTEMPT:**
- It is recommended to apply `RE-ATTEMPT` **late in the evening (after 9 PM)** to ensure all NDR AWBs are back in the facility and all dispatches are closed.
- Always **verify the current NSL** of the AWB before applying NDR.
- The **attempt count** for the shipment should be either **1 or 2**.

---

## PICKUP_RESCHEDULE Action Requirements

The `PICKUP_RESCHEDULE` action can only be applied when **all** of the following conditions are met:

| Condition | Requirement |
|-----------|-------------|
| Package status | Must be **CN** (Canceled) |
| Shipment status | Must be **"Canceled"** |
| Attempt count | Must be **1 or 2** |
| Waybill ownership | Must belong to the **client's account** |
| Dispatch status | Shipment must **not** be part of an open dispatch |
| NSL code | Must be **EOD-777** (RVP QC Fail) or **EOD-21** (Pickup request canceled, non-OTP verified) |

**Best Practices for PICKUP_RESCHEDULE:**
- Apply `PICKUP_RESCHEDULE` **after 9 PM** to ensure that all open dispatches in the facility are closed by that time.
- The shipment must be **Non OTP Cancelled** (i.e., the cancellation should not be OTP-verified).
- The **attempt count** for the shipment should be either **1 or 2**.

---

## CRITICAL: Maximum 1000 Shipments Per Request

A maximum of **1000 shipments** can be updated in a single API call. If you need to update more, **split the request into multiple calls**. Exceeding 1000 items returns: `"Can not update more than 1000 records"`.

---

## Response Structure

### Success

```json
{
  "message": "Request submitted successfully!",
  "request_id": "UPL17749083484755923441"
}
```

- `message` — confirmation string
- `request_id` — **UPL ID** — a unique confirmation that the update request was received

---

## CRITICAL: Request Is Asynchronous — UPL ID and NDR Status API

This is an **asynchronous API**. The response `"Request submitted successfully!"` means the NDR action has been **queued**, not necessarily executed yet.

The response includes a **UPL ID** (`request_id` field, e.g. `"UPL17749083484755923441"`). This UPL ID is then used in the **GET NDR Status API** to check the status of the NDR update for which the action was taken.

**Flow:**
1. Call **Update NDR API** → receive `request_id` (UPL ID)
2. Call **GET NDR Status API** with the UPL ID → check if the NDR action was successfully applied

---

## CRITICAL: `act` Values Are Case-Sensitive

The `act` field only accepts exact enum values:

```
"act": "RE-ATTEMPT"          // ✅ correct
"act": "re-attempt"          // ❌ wrong
"act": "REATTEMPT"           // ❌ wrong (missing hyphen)
"act": "PICKUP_RESCHEDULE"   // ✅ correct
"act": "pickup_reschedule"   // ❌ wrong
```

---

## CRITICAL: Supports Batch Updates

The `data` array supports multiple NDR items in a single request — update multiple waybills at once (up to 1000 per request).

---

## CRITICAL: 403 Forbidden

Unlike most other Delhivery APIs that only return 401 for auth issues, this API can also return **403 Forbidden** — indicating the token is valid but lacks permission for this operation. It may also return `"Unauthorized client/user"` with a 403 status.

---

## Common API Errors and Solutions

| Error Remark | Reason | Solution |
|---|---|---|
| Package in incorrect status | Trying to apply NDR on a shipment that is not in the correct status. | For `RE-ATTEMPT`, the package should be in Pending state with NSL code in: `EOD-74`, `EOD-15`, `EOD-104`, `EOD-43`, `EOD-86`, `EOD-11`, `EOD-69`, `EOD-6`. |
| Invalid data provided | The "data" field in the payload is not in list format. | Ensure the payload format is correct. The "data" field must be a JSON array. |
| Can not update more than 1000 records | The "data" list contains more than 1000 items. | Split the request into multiple calls with ≤1000 items each. |
| Unauthorized client/user | The user is not authorized. | Verify that you are using the correct authorization token. |
| Package action is being performed | The request is currently being processed. | The request is in progress. Please check again after some time. |
| Action is not valid | The "act" field does not contain a valid action. | Ensure that the action is set to `RE-ATTEMPT` or `PICKUP_RESCHEDULE`. |
| "waybill" is missing | The "waybill" field is missing in the "data" payload. | The "waybill" key is mandatory. Include it in the payload. |
| Package should be in Canceled status | `PICKUP_RESCHEDULE` is allowed only for canceled shipments. | Package status should be CN and shipment status should be "Canceled". |
| Shipment has reached max attempt count | `PICKUP_RESCHEDULE` is allowed only if attempt count is 1 or 2. | Contact Delhivery account POC if `PICKUP_RESCHEDULE` is required. |
| Incorrect waybill | The provided waybill does not match the client's account. | Verify that the waybill is correct before applying `PICKUP_RESCHEDULE`. |
| Package is part of dispatch | `PICKUP_RESCHEDULE` is not allowed as shipment is part of an open dispatch. | Try again later or contact Delhivery account POC. |
| Rescheduling is not allowed as \<Reason\> | Package does not meet conditions for `PICKUP_RESCHEDULE`. | Allowed only when NSL is `EOD-777` (RVP QC Fail) or `EOD-21` (Pickup request canceled, non-OTP verified). |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Wrong case for `act` value | Must be exact: `RE-ATTEMPT` or `PICKUP_RESCHEDULE` |
| Missing hyphen in `RE-ATTEMPT` | Include the hyphen: `RE-ATTEMPT`, not `REATTEMPT` |
| Assuming immediate execution | Response is async — use UPL ID with GET NDR Status API to verify |
| Not wrapping items in `data` array | Request body must be `{"data": [...]}` |
| Ignoring `request_id` (UPL ID) | Store it — required for GET NDR Status API to check update status |
| Applying NDR actions during the day | Apply both `RE-ATTEMPT` and `PICKUP_RESCHEDULE` after 9 PM when dispatches are closed |
| Not verifying current NSL before applying | Always verify the current NSL code of the AWB before applying NDR |
| Not handling 403 | This API can return 403 in addition to 401 |
| Exceeding 1000 items in `data` | Maximum 1000 shipments per request — split into multiple calls |
| Applying `RE-ATTEMPT` without checking NSL code | Package must be Pending with a valid NSL code (see RE-ATTEMPT section) |
| Applying `PICKUP_RESCHEDULE` on non-canceled shipments | Package must be CN/Canceled with attempt count ≤2 and valid NSL |
| `PICKUP_RESCHEDULE` on shipment in open dispatch | Shipment must not be part of an open dispatch |
