# Packing Slip API — Specification

> **When to load**: User asks about shipping labels, packing slips, label generation, PDF labels, or printing labels for shipments.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/p/packing_slip` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Generate shipping labels against a waybill number as JSON or PDF |
| **Avg Latency (Prod)** | 210.64ms |
| **P99 Latency (Prod)** | 61.78s |
| **Rate Limit** | 3000 requests / 5 min / IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Packing Slip API
  description: |
    API specification for Delhivery Last Mile Express system. This API is used to generate shipping labels against a waybill number. Shipping labels can also be downloaded from the One Panel. The response can be returned as JSON (for custom label rendering) or as a PDF download link based on the `pdf` parameter.

    ## Rate Limit and Latency

    | Metrics | Value |
    |---|---|
    | Average Latency (PRODUCTION) | 210.64ms |
    | P99 Latency (PRODUCTION) | 61.78s |
    | Rate Limit (Requests/5 Minute/IP) (PRODUCTION) | 3000 |

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Packing Slip
    description: Operations related to packing slip generation and retrieval

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
    PackingSlipResponse:
      type: object
      properties:
        packages:
          type: array
          items:
            type: object
            properties:
              wbn:
                type: string
                description: Waybill number
                example: "84649910000022"
              pdf_download_link:
                type: string
                format: uri
                description: S3 link to download the PDF (only present when pdf=true)
                example: "https://express-hq.s3.ap-south-1.amazonaws.com/packing-slip/84649910000022.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIARIGS3RKBNYII3R7X%2F20260203%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Date=20260203T111300Z&X-Amz-Expires=86400&X-Amz-Security-Token=IQoJb3JpZSignature=b9abd46b64e08a14a3700b2b09c070063dbc5d45e9c3d78627b3cc766dbac004"
              pdf_encoding:
                type: string
                description: PDF encoding (base64 encoded PDF content when pdf=false, or encoding identifier when pdf=true)
                example: "Jdufhbsefhbegr"
        packages_found:
          type: integer
          description: Number of packages found
          example: 1

paths:
  /api/p/packing_slip:
    get:
      tags:
        - Packing Slip
      summary: Get packing slip
      description: |
        Generates shipping labels against a waybill number. Shipping labels can also be downloaded from the One Panel.
        If pdf=true, an S3 link to the PDF will be generated which cannot be customized.
        If pdf=false, the response will be JSON that should be rendered into HTML using encoding 128, allowing flexibility in designing the layout.
      operationId: getPackingSlip
      security:
        - TokenAuth: []
      parameters:
        - name: wbns
          in: query
          required: true
          description: Waybill number(s) of the shipment(s). Can be a single waybill or comma-separated list of waybills.
          schema:
            type: string
          example: "7035xxxxxxxxxxx"
        - name: pdf
          in: query
          required: false
          description: |
            If passed True: An S3 link of the PDF will be generated which cannot be customized.
            If passed False: Response would be JSON, that should be rendered into HTML using encoding 128 for custom label design.
          schema:
            type: boolean
          example: true
        - name: pdf_size
          in: query
          required: false
          description: |
            PDF size specification. If not provided, defaults to A4.
            For size 8x11 (A4), pass: pdf_size=A4
            For size 4x6 (4R), pass: pdf_size=4R
          schema:
            type: string
            enum: [A4, 4R]
          example: "4R"
      responses:
        '200':
          description: Successful response with packing slip information
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PackingSlipResponse'
              example:
                packages:
                  - wbn: "84649910000022"
                    pdf_download_link: "https://express-hq.s3.ap-south-1.amazonaws.com/packing-slip/84649910000022.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIARIGS3RKBNYII3R7X%2F20260203%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Date=20260203T111300Z&X-Amz-Expires=86400&X-Amz-Security-Token=IQoJb3JpZSignature=b9abd46b64e08a14a3700b2b09c070063dbc5d45e9c3d78627b3cc766dbac004"
                    pdf_encoding: "Jdufhbsefhbegr"
                packages_found: 1
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

## Query Parameters

| Parameter | In | Required | Type | Description |
|-----------|----|----------|------|-------------|
| `wbns` | query | Yes | string | Waybill number(s) — single or comma-separated |
| `pdf` | query | No | boolean | `true` = S3 PDF link, `false` = JSON response |
| `pdf_size` | query | No | string (`A4` or `4R`) | PDF page size — A4 (8×11) or 4R (4×6). Defaults to A4 if not provided. |

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `packages` | array | Array of package objects |
| `packages[].wbn` | string | Waybill number |
| `packages[].pdf_download_link` | string (URI) | S3 signed URL for PDF download (when `pdf=true`) |
| `packages[].pdf_encoding` | string | PDF encoding data |
| `packages_found` | integer | Number of packages found |

---

## `pdf=true` vs `pdf=false` Behavior

| `pdf` value | Response behavior |
|-------------|-------------------|
| `true` | Returns `pdf_download_link` — a signed S3 URL to download the PDF. Cannot be customized. |
| `false` | Returns JSON data that should be **rendered into HTML using encoding 128**. This allows flexibility in designing the layout of the shipping label and adding any necessary information. |

### PDF Size Options

| `pdf_size` | Dimensions | Notes |
|------------|-----------|-------|
| `A4` | 8×11 inches | **Default** if `pdf_size` is not provided |
| `4R` | 4×6 inches | Standard label printer size |

---

## CRITICAL: S3 PDF Links Expire After 24 Hours

When `pdf=true`, the `pdf_download_link` is a **signed S3 URL** with `X-Amz-Expires=86400` (24 hours).

- Download immediately if printing now.
- If storing for later use, track the expiry and re-generate before it expires.
- Expired links return **403 Access Denied** — not a Delhivery auth error.

---

## Bulk Requests — Check Per-Package Results

When requesting labels for multiple waybills (`?wbns=wb1,wb2,wb3`):
- The `packages` array may have mixed results — some with valid data, some with errors.
- Always check `packages_found` against the number of waybills requested.
- Iterate each item in `packages` individually.

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Caching S3 PDF links indefinitely | Links expire after 24 hours — re-generate or download promptly |
| Not checking `packages_found` | May be less than number of waybills requested |
| Assuming all packages succeeded in bulk | Check each entry in `packages[]` individually |
| Not passing `pdf_size` for printing | Default may not match label printer — use `4R` for standard label printers |
