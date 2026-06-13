# Get NDR / Bulk Upload Status API — Specification

> **When to load**: User asks about checking the status of an NDR update using the UPL ID (request_id) received from the NDR Update API.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/cmu/get_bulk_upl/{request_id}` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Get the status of the request_id (i.e. UPL ID) received from the NDR Update API |
| **Avg Latency (Prod)** | 75.03ms |
| **P99 Latency (Prod)** | 88.03s |
| **Rate Limit** | NA |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Get Bulk Upload Status API
  description: |
    API specification for Delhivery Last Mile Express system. This API is used to get the status of the request_id (i.e. UPL ID) received from the NDR Update API, including details of successful and failed waybills.

    ## Rate Limit and Latency

    | Metrics | Value |
    |---|---|
    | Average Latency (PRODUCTION) | 75.03ms |
    | P99 Latency (PRODUCTION) | 88.03s |
    | Rate Limit (Requests/5 Minute/IP) (PRODUCTION) | NA |

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Bulk Upload Status
    description: Check the status of a UPL ID (request_id) received from the NDR Update API

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
    FailedWaybill:
      type: object
      properties:
        action:
          type: string
          description: Action that was attempted
          example: "PICKUP_RESCHEDULE"
        waybill:
          type: string
          description: Waybill number that failed
          example: "227410150021"
        message:
          type: string
          description: Error message explaining why the waybill failed
          example: "Rescheduling is not allowed as package should be in canceled status"

    SuccessWaybill:
      type: object
      properties:
        waybill:
          type: string
          description: Waybill number that succeeded
          example: "13163116xxxxxx"
        action:
          type: string
          description: Action that was successfully applied
          example: "RE-ATTEMPT"

    BulkUploadStatusResponse:
      type: object
      properties:
        status:
          type: string
          description: Overall status of the bulk upload request (Success/Failure)
          example: "Failure"
        remark:
          type: string
          description: Remark or summary message about the request status
          example: "Zero waybills affected"
        failed_wbns:
          type: array
          items:
            $ref: '#/components/schemas/FailedWaybill'
          description: Array of waybills that failed with error details
          example: []
        success_wbns:
          type: array
          items:
            $ref: '#/components/schemas/SuccessWaybill'
          description: Array of waybills that succeeded
          example: []
        request_id:
          type: string
          description: UPL ID — the same request_id received from the NDR Update API
          example: "UPL17749083484755923441"

paths:
  /api/cmu/get_bulk_upl/{request_id}:
    get:
      tags:
        - Bulk Upload Status
      summary: Get NDR update status by UPL ID
      description: |
        Retrieves the status of the request_id (i.e. UPL ID) received from the NDR Update API, including details of successful and failed waybills.
        When verbose=true, additional details about successful and failed waybills are included in the response.
      operationId: getBulkUploadStatus
      security:
        - TokenAuth: []
      parameters:
        - name: request_id
          in: path
          required: true
          description: UPL ID (request_id) received from the NDR Update API
          schema:
            type: string
          example: "UPL17749083484755923441"
        - name: verbose
          in: query
          required: false
          description: If true, returns detailed information about successful and failed waybills
          schema:
            type: boolean
          example: true
      responses:
        '200':
          description: Successful response with bulk upload status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkUploadStatusResponse'
              example:
                status: "Failure"
                remark: "Zero waybills affected"
                failed_wbns:
                  - action: "PICKUP_RESCHEDULE"
                    waybill: "227410150021"
                    message: "Rescheduling is not allowed as package should be in canceled status"
                success_wbns: []
                request_id: "UPL17749083484755923441"
        '403':
          description: Forbidden - Insufficient permissions or invalid request
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
        '404':
          description: Not Found - Request ID not found
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `request_id` | path | string | Yes | UPL ID (request_id) received from the NDR Update API |
| `verbose` | query | boolean | No | If `true`, includes detailed per-waybill success/failure info |

---

## Response Structure

```json
{
  "status": "Failure",
  "remark": "Zero waybills affected",
  "failed_wbns": [
    {
      "action": "PICKUP_RESCHEDULE",
      "waybill": "227410150021",
      "message": "Rescheduling is not allowed as package should be in canceled status"
    }
  ],
  "success_wbns": [],
  "request_id": "UPL17749083484755923441"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"Success"` or `"Failure"` — overall outcome |
| `remark` | string | Summary message (e.g., `"Zero waybills affected"`) |
| `failed_wbns` | array | Waybills that failed — each with `action`, `waybill`, and `message` |
| `success_wbns` | array | Waybills that succeeded — each with `waybill` and `action` |
| `request_id` | string | Echo of the UPL ID queried |

---

## CRITICAL: Use `verbose=true` for Per-Waybill Details

Without `verbose=true`, the response may only include the overall `status` and `remark`. Always pass `verbose=true` when you need to know which specific waybills succeeded or failed.

---

## CRITICAL: This Is the Companion to NDR Update API

This API is used to get the status of the **UPL ID** (`request_id`) received from the NDR Update API (`/api/p/update`). The typical flow is:

1. **POST** `/api/p/update` → receive `request_id` (UPL ID) confirming the NDR update request was received
2. **GET** `/api/cmu/get_bulk_upl/{request_id}?verbose=true` → check per-waybill results using the UPL ID

---

## CRITICAL: `status: "Failure"` Can Mean Partial Failure

Even when `status` is `"Failure"`, check both `failed_wbns` and `success_wbns` — a batch can have some waybills succeed and others fail. The `status` reflects the overall outcome, not individual results.

---

## Known Error Messages (in `failed_wbns[].message`)

| Error | Cause |
|-------|-------|
| `"Rescheduling is not allowed as package should be in canceled status"` | Trying to reschedule a package that's not in the right state |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Not passing `verbose=true` | Without it, per-waybill details may be missing |
| Treating `"Failure"` as total failure | Check both arrays — partial success is possible |
| Not storing UPL ID from NDR update | Save the `request_id` (UPL ID) immediately after the NDR Update API call |
| Polling immediately after NDR update | Allow some processing time before checking status |
| Not handling 404 | Invalid or expired UPL ID returns 404 |
