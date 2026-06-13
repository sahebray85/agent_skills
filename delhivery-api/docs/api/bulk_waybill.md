# Bulk Waybill Generation API — Specification

> **When to load**: User asks about generating waybills, getting tracking numbers, AWB generation, or pre-assigning waybills before shipment creation.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/waybill/api/bulk/json/` |
| **Auth** | Query parameter: `?token=<your-token>` (**NOT** header — see `bulk_waybill/auth.md`) |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Generate waybill numbers (use `count=1` for a single waybill) |
| **Avg Latency (Prod)** | 129.84ms |
| **P99 Latency (Prod)** | 154.02ms |
| **Rate Limit** | 5 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Bulk Waybill API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to generate the bulk waybill list in advance, which can be stored and used in the order creation API. For a single waybill, pass count=1.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Waybill
    description: Operations related to waybill generation

components:
  schemas:
    BulkWaybillResponse:
      type: string
      description: Comma-separated list of generated waybill numbers
      example: "6890610001002,6890610001013,6890610001024,6890610001035,6890610001046"

paths:
  /waybill/api/bulk/json/:
    get:
      tags:
        - Waybill
      summary: Generate waybills (bulk or single)
      description: |
        Generates waybills and returns them as a comma-separated string. The number of waybills to generate is specified by the count parameter (1–10,000). For a single waybill, pass count=1.
      operationId: generateBulkWaybills
      parameters:
        - name: token
          in: query
          required: true
          description: Authentication token for API access
          schema:
            type: string
          example: "xxxxxxxxxxxxxxxx"
        - name: count
          in: query
          required: true
          description: Number of waybills to generate
          schema:
            type: integer
            minimum: 1
            maximum: 10000
          example: 5
      responses:
        '200':
          description: Successful response with generated waybills as comma-separated string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkWaybillResponse'
              example: "6890610001002,6890610001013,6890610001024,6890610001035,6890610001046"
        '400':
          description: Bad Request - Invalid request, missing count parameter, or unable to fetch client name for the token
          content:
            application/json:
              schema:
                type: string
              examples:
                missingCount:
                  summary: Missing count parameter
                  value: "Bad Request! Invalid count for client 000a86-Desyncced-do-cdp"
                invalidToken:
                  summary: Unable to fetch client name for token
                  value: "Bad Request! Invalid request. Unable to fetch client name for the token."
```

---

## CRITICAL: Authentication Is Via Query Parameter

This API does **NOT** use the `Authorization` header. The token is passed as a query parameter:

```
GET /waybill/api/bulk/json/?token=<YOUR_TOKEN>&count=5
```

See `bulk_waybill/auth.md` for full details on this override.

---

## CRITICAL: Response Is a Comma-Separated String, NOT JSON Array

The 200 response body is a **plain comma-separated string**, not a JSON array:

```
"6890610001002,6890610001013,6890610001024,6890610001035,6890610001046"
```

You **must** split this string to get individual waybills:

```
waybills = response_text.split(",")
```

Do NOT attempt to `json.loads()` the response as an array — it will fail.

---

## CRITICAL: Waybills Are Generated in Batches of 25 — Do NOT Use Immediately

Waybills are generated in **batches of 25 at the backend**. Using them immediately after fetching may occasionally result in errors.

**Recommendation**: Store the fetched waybills on your end and use them later during manifest/shipment creation. Do NOT fetch and use in the same synchronous flow.

---

## Rate Limiting

| Rule | Value |
|------|-------|
| Max waybills per request | 10,000 |
| Max waybills per 5-minute window | 50,000 |
| Throttle penalty | IP throttled for 1 minute if 50,000 limit exceeded |
| Request rate limit | 5 requests / 5 min / IP |

If you need more than 50,000 waybills in a short period, space your requests across multiple 5-minute windows.

---

## Parameters

| Parameter | In | Required | Type | Description |
|-----------|----|----------|------|-------------|
| `token` | query | Yes | string | Authentication token |
| `count` | query | Yes | integer (1–10,000) | Number of waybills to generate |

---

## Error Scenarios

| HTTP Code | Error | Cause |
|-----------|-------|-------|
| 400 | `"Bad Request! Invalid count for client {name}"` | Missing or invalid `count` parameter |
| 400 | `"Bad Request! Invalid request. Unable to fetch client name for the token."` | Invalid or expired token |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Using `Authorization: Token` header | Pass token as query parameter `?token=xxx` |
| Parsing response as JSON array | Split the comma-separated string |
| Not validating `count` (1–10,000) | Validate before calling — must be between 1 and 10,000 |
| Using waybills immediately after fetching | Store first, use later — backend generates in batches of 25 |
| Exceeding 50,000 waybills in 5 minutes | Space requests across 5-min windows to avoid IP throttle |
