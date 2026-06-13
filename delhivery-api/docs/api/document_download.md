# Fetch Package Document API — Specification

> **When to load**: User asks about downloading shipment document, fetching signature image, EPOD or QC images.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/api/rest/fetch/pkg/document/` |
| **Auth** | `Authorization: Token <your-token>` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Fetch package documents (signatures, QC images, EPOD, seller return images) by waybill number |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Fetch Package Document API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to fetch documents associated with B2C orders such as signatures, QC images, EPOD, and seller return images by waybill number. Only non-archived documents can be retrieved.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Document
    description: Operations related to fetching package documents

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
    FetchDocumentResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: true
        message:
          type: string
          description: Response message (empty string when successful)
          example: ""
        data:
          type: object
          additionalProperties:
            type: array
            items:
              type: string
              format: uri
          description: |
            Object containing document type as key and array of document URLs as value.
            The key name matches the doc_type parameter passed in the request.
          example:
            RVP_QC_IMAGE:
              - "https://api-dev-dms-k8.delhivery.com/resource/getFile/self_signed_v2/signature.jpg?token=...&signature=rCMN4ekWBqaqGWjca1pe9b6CGl-VnnPD0kp253z4JFM"
              - "https://api-dev-dms-k8.delhivery.com/resource/getFile/self_signed_v2/signature.jpg?token=...&signature=J7r67eVQWeSHkkM6J3Q6iq-BOtw-WbAfnhe7YMqWyNA"

    FetchDocumentErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the operation was successful
          example: false
        message:
          type: string
          description: Error message
          example: "Invalid waybill passed"
        data:
          type: object
          description: Empty data object when error occurs
          example: {}

paths:
  /api/rest/fetch/pkg/document/:
    get:
      tags:
        - Document
      summary: Fetch package document
      description: |
        Fetches documents associated with B2C orders such as signatures, QC images, EPOD, and seller return images by waybill number.
        Only non-archived documents can be retrieved. The document type determines what kind of document will be returned.
      operationId: fetchPackageDocument
      security:
        - TokenAuth: []
      parameters:
        - name: doc_type
          in: query
          required: true
          description: |
            The type of document to fetch. Allowed values: SIGNATURE_URL, RVP_QC_IMAGE, EPOD, SELLER_RETURN_IMAGE
          schema:
            type: string
            enum:
              - SIGNATURE_URL
              - RVP_QC_IMAGE
              - EPOD
              - SELLER_RETURN_IMAGE
          example: "RVP_QC_IMAGE"
        - name: waybill
          in: query
          required: true
          description: Delhivery waybill number
          schema:
            type: integer
          example: 227410150021
      responses:
        '200':
          description: Successful response with document URLs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FetchDocumentResponse'
              example:
                success: true
                message: ""
                data:
                  RVP_QC_IMAGE:
                    - "https://api-dev-dms-k8.delhivery.com/resource/getFile/self_signed_v2/signature.jpg?token=...&signature=rCMN4ekWBqaqGWjca1pe9b6CGl-VnnPD0kp253z4JFM"
                    - "https://api-dev-dms-k8.delhivery.com/resource/getFile/self_signed_v2/signature.jpg?token=...&signature=J7r67eVQWeSHkkM6J3Q6iq-BOtw-WbAfnhe7YMqWyNA"
        '400':
          description: Bad Request - Invalid waybill or parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FetchDocumentErrorResponse'
              example:
                success: false
                message: "Invalid waybill passed"
                data: {}
        '401':
          description: Unauthorized - Invalid or missing authentication token
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
        '404':
          description: Not Found - Document or waybill not found
          content:
            application/json:
              schema:
                type: string
              example: "There has been an error but we were asked to not let you see that. Please contact the dev team."
```

---

## Allowed Document Types

| `doc_type` Value | Description |
|-----------------|-------------|
| `SIGNATURE_URL` | Delivery signature image |
| `RVP_QC_IMAGE` | Reverse pickup QC images |
| `EPOD` | Electronic proof of delivery |
| `SELLER_RETURN_IMAGE` | Seller return images |

Only non-archived documents can be retrieved. If a document has been archived in the Delhivery system, it will not be available through this API.

---

## Required Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `doc_type` | string | Document type to fetch — must be one of: `SIGNATURE_URL`, `RVP_QC_IMAGE`, `EPOD`, `SELLER_RETURN_IMAGE` |
| `waybill` | integer | Delhivery waybill number |

---

## Response Structure

### Success Response

```json
{
  "success": true,
  "message": "",
  "data": {
    "RVP_QC_IMAGE": [
      "https://...signed-url-1...",
      "https://...signed-url-2..."
    ]
  }
}
```

- `success` — boolean, `true` on success
- `message` — empty string on success
- `data` — object where the **key matches the `doc_type` you requested** and the value is an **array of signed URLs**

### Error Response

```json
{
  "success": false,
  "message": "Invalid waybill passed",
  "data": {}
}
```

---

## CRITICAL: `data` Key Name Is Dynamic

The key inside `data` matches whatever `doc_type` you passed in the request. If you request `doc_type=SIGNATURE_URL`, the response will have `data.SIGNATURE_URL`, not `data.RVP_QC_IMAGE`. Always use the same `doc_type` value to access the response data.

---

## CRITICAL: URLs Are Signed and Expire After 7 Days

The returned URLs contain authentication tokens and signatures. They are **pre-signed URLs** that expire after **7 days**. Download/use them within this window; they will stop working after expiry.

---

## CRITICAL: `waybill` Parameter Is Integer

The spec defines `waybill` as `type: integer`, not string. Pass it as a number:

```
/api/rest/fetch/pkg/document/?doc_type=RVP_QC_IMAGE&waybill=227410150021
```

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Accessing wrong key in `data` | Key matches your `doc_type` parameter exactly |
| Storing signed URLs permanently | URLs expire after 7 days — download content within that window |
| Passing waybill as string | Spec defines it as `integer` |
| Not checking `success` field | Always check `success` before accessing `data` |
| Assuming single URL in response | `data[doc_type]` is an **array** — may contain multiple URLs |
| Not handling 404 | Document may not exist for the waybill — handle gracefully |
