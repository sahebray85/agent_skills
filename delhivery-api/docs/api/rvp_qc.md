# Create Shipment with RVP QC 3.0 API — Specification

> **When to load**: User asks about reverse pickups with quality checks, RVP QC shipments, return verification, custom QC questions, or creating reverse shipments with item-level inspection.

---

## Overview

RVP QC 3.0 is used to perform Quality Check (QC) at the consignee's doorstep for an RVP (Reverse Pickup) shipment.

This is an updated version of the RVP QC that gives the flexibility of a question-based model. It will allow a set of questions against each item to be picked on the ground by FE from the end customer. Pickup will only be made once all the mandatory questions have been answered correctly.

---

## Steps of Integration

### 1. QC Question Mapping

A one-time QC mapping is required on Delhivery's end to enable this feature. Based on the client's QC requirements, the Delivery BD team will share the relevant Delhivery QC question IDs to their end-customer IDs. The client must then map these Delhivery question IDs to their own question IDs in the specified format, as it can be configured in the Delhivery system.

### 2. Order Creation

When creating an RVP order via API, 2 keys must be included in the manifest payload:

- **`qc_type`**: Set this key to the hardcoded value `"param"` to indicate Parametric QC.
- **`custom_qc`**: Include the QC data in the manifest payload within this array. Refer to the sample payload in the request section.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/api/cmu/create.json` |
| **Auth** | `Authorization: Token <your-token>` |
| **Content-Type** | `application/json` |
| **Staging** | `https://staging-express.delhivery.com` |
| **Production** | `https://track.delhivery.com` |
| **Purpose** | Create shipments (SPS/MPS) with RVP Quality Check parameters, custom QC questions, and item-level inspection |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| **Average Latency (Production)** | 366.03 ms |
| **P99 Latency (Production)** | 916.17 ms |
| **Rate Limit (Requests/5 Minute/IP)** | 20000 |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Create Shipment with RVP QC API
  description: |
    API specification for Delhivery Last Mile Express system. It's used to create shipments (SPS/MPS) with RVP (Return Verification Process) Quality Check (QC) parameters, including custom QC questions and items.

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Shipment Creation
    description: Operations related to shipment creation with RVP QC (SPS/MPS)

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
    QCQuestion:
      type: object
      properties:
        questions_id:
          type: string
          description: This will be the client question id and against this ID Delhivery will map one question at their end
          example: "client Question id"
        options:
          type: array
          items:
            type: string
          description: Available options for the question
          example: ["Black", "other"]
        value:
          type: array
          items:
            type: string
          description: Currently only the first element is chosen as the correct option
          example: ["Black"]
        required:
          type: boolean
          description: |
            False: Question will still be asked but the answer will not affect the QC result, i.e. If FE chooses any available answer to the given QC question, QC will always be Passed.
            True: Question will be asked and the answer will affect QC result, i.e. If FE chooses the incorrect answer to the given QC question, QC will be Failed
          example: true
        type:
          type: string
          description: |
            Type == 'varchar': FE will type the answer
            Type == 'multi': FE will select one of the given options
          enum: [varchar, multi]
          example: "multi"
        ques_images:
          type: array
          items:
            type: string
            format: uri
          description: |
            This is a non-mandatory field and completely optional for a client to pass.
            The client has to pass the image URL, which will be visible to the FE for a specific question for which QC is performed
          example: ["http://ecx.images-amazon.com/images/I/414yumheSAS._AC_.jpg"]
      required:
        - questions_id
        - options
        - value
        - required
        - type

    CustomQCItem:
      type: object
      properties:
        item:
          type: string
          description: Item name
          example: "mobile"
        description:
          type: string
          description: Item description
          example: "Mi note 1 pro"
        images:
          type: array
          items:
            type: string
            format: uri
          description: Comma-separated multiple strings can be passed. Array of image URLs
          example: ["https://fdn2.gsmarena.com/vv/pics/xiaomi/xiaomi-note-pro-2.jpg"]
        return_reason:
          type: string
          description: Return reason
          example: "Damaged"
        quantity:
          type: integer
          description: Quantity. Default value is 1, if quantity is not present
          default: 1
          example: 1
        brand:
          type: string
          description: Brand name
          example: "Mi"
        product_category:
          type: string
          description: Product category
          example: "mobile"
        questions:
          type: array
          items:
            $ref: '#/components/schemas/QCQuestion'
          description: List of QC questions
      required:
        - description
        - images
        - quantity
        - questions

    RVPShipment:
      type: object
      properties:
        client:
          type: string
          description: Pass the registered client name
          example: "pass the registered client name"
        return_name:
          type: string
          description: Return name
          example: "test_designs"
        order:
          type: string
          description: Order ID
          example: "1234567890"
        return_country:
          type: string
          description: Return country
          example: "India"
        weight:
          type: string
          description: Weight of the shipment
          example: "150.0 gm"
        city:
          type: string
          description: City of the consignee
          example: "Meerjapuram"
        pin:
          type: integer
          description: Pincode of the consignee
          example: 521111
        return_state:
          type: string
          description: Return state
          example: "Gujarat"
        products_desc:
          type: string
          description: Product Description
          example: "NEW EI PIKOK (PURPAL-ORANGE)"
        shipping_mode:
          type: string
          description: Shipping mode (Surface/Express)
          example: "Express"
        state:
          type: string
          description: State of the consignee
          example: "Andhra Pradesh"
        quantity:
          type: integer
          description: Quantity
          example: 1
        waybill:
          type: string
          description: Waybill number
          example: "123455678910"
        phone:
          type: array
          items:
            type: string
          description: Consignee phone number
          example: ["1234567890"]
        add:
          type: string
          description: Address of the consignee
          example: "7 106 abc road, 2020 bulding "
        payment_mode:
          type: string
          description: Payment mode (Prepaid/COD/Pickup)
          example: "Pickup"
        order_date:
          type: string
          description: Order date
          example: "29-06-2023"
        seller_gst_tin:
          type: string
          description: Seller GST TIN number
          example: "ABCD1234F"
        name:
          type: string
          description: Name of the consignee
          example: "Jitendra Singh"
        return_add:
          type: string
          description: Return address
          example: " SHOP NO 218,ABC Road, Mumbai"
        total_amount:
          type: number
          format: float
          description: Total amount
          example: 749
        seller_name:
          type: string
          description: Seller name
          example: "ABC Design"
        return_city:
          type: string
          description: Return city
          example: "SURAT"
        country:
          type: string
          description: Country
          example: "India"
        return_pin:
          type: string
          description: Return pincode
          example: "394101"
        return_phone:
          type: array
          items:
            type: string
          description: Return phone number
          example: ["1234567890"]
        qc_type:
          type: string
          description: QC type
          example: "param"
        custom_qc:
          type: array
          items:
            $ref: '#/components/schemas/CustomQCItem'
          description: Custom QC (Quality Check) items array
      required:
        - name
        - order
        - phone
        - add
        - pin
        - client
        - custom_qc

    CreateRVPQCRequest:
      type: object
      properties:
        shipments:
          type: array
          items:
            $ref: '#/components/schemas/RVPShipment'
          description: Array of shipment objects with RVP QC
        pickup_location:
          type: object
          properties:
            name:
              type: string
              description: Name should be exactly the same as the name of the WH registered. It is case/space sensitive.
              example: "pass the registered pickup WH name"
          required:
            - name
      required:
        - shipments
        - pickup_location

    PackageResponse:
      type: object
      properties:
        status:
          type: string
          description: Status of package creation
          example: "Success"
        client:
          type: string
          description: Client name
          example: "madura"
        sort_code:
          type: string
          nullable: true
          description: Sort code
          example: "1209"
        remarks:
          type: array
          items:
            type: string
          description: Remarks
          example: [""]
        waybill:
          type: string
          description: Generated waybill number
          example: "227410150032"
        cod_amount:
          type: number
          format: float
          description: COD amount
          example: 0.0
        payment:
          type: string
          description: Payment mode
          example: "Pre-paid"
        serviceable:
          type: boolean
          description: Whether the location is serviceable
          example: true
        refnum:
          type: string
          description: Reference number (Order ID)
          example: "1234567890"

    CreateRVPQCResponse:
      type: object
      properties:
        cash_pickups_count:
          type: number
          format: float
          description: Cash pickups count
          example: 0.0
        package_count:
          type: integer
          description: Number of packages created
          example: 1
        upload_wbn:
          type: string
          nullable: true
          description: Upload waybill number
          example: "UPL15809598291576112229"
        replacement_count:
          type: integer
          description: Replacement count
          example: 0
        pickups_count:
          type: integer
          description: Pickups count
          example: 0
        packages:
          type: array
          items:
            $ref: '#/components/schemas/PackageResponse'
          description: Array of created packages
        cash_pickups:
          type: number
          format: float
          description: Cash pickups
          example: 0.0
        cod_count:
          type: integer
          description: COD count
          example: 0
        success:
          type: boolean
          description: Whether the operation was successful
          example: true
        prepaid_count:
          type: integer
          description: Prepaid count
          example: 1
        cod_amount:
          type: number
          format: float
          description: Total COD amount
          example: 0.0
        rmk:
          type: string
          description: Remarks or error message (only present when success is false)
          example: "An internal Error has occurred, Please get in touch with client.support@delhivery.com"
        error:
          type: boolean
          description: Error flag (only present when success is false)
          example: false

paths:
  /api/cmu/create.json:
    post:
      tags:
        - Shipment Creation
      summary: Create shipment(s) with RVP QC
      description: |
        Creates one or more shipments (SPS/MPS) with RVP (Return Verification Process) Quality Check parameters.
        Includes custom QC items with questions, images, and validation rules.
        For SPS: Waybill can be passed in the payload or can be skipped.
        For MPS: Waybill needs to be passed for each box explicitly in the API.
      operationId: createShipmentRVPQC
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateRVPQCRequest'
            example:
              shipments:
                - client: "pass the registered client name"
                  return_name: "test_designs"
                  order: "1234567890"
                  return_country: "India"
                  weight: "150.0 gm"
                  city: "Meerjapuram"
                  pin: 521111
                  return_state: "Gujarat"
                  products_desc: "NEW EI PIKOK (PURPAL-ORANGE)"
                  shipping_mode: "Express"
                  state: "Andhra Pradesh"
                  quantity: 1
                  waybill: "123455678910"
                  phone: ["1234567890"]
                  add: "7 106 abc road, 2020 bulding "
                  payment_mode: "Pickup"
                  order_date: "29-06-2023"
                  seller_gst_tin: "ABCD1234F"
                  name: "Jitendra Singh"
                  return_add: " SHOP NO 218,ABC Road, Mumbai"
                  total_amount: 749
                  seller_name: "ABC Design"
                  return_city: "SURAT"
                  country: "India"
                  return_pin: "394101"
                  return_phone: ["1234567890"]
                  qc_type: "param"
                  custom_qc:
                    - item: "mobile"
                      description: "Mi note 1 pro"
                      images:
                        - "https://fdn2.gsmarena.com/vv/pics/xiaomi/xiaomi-note-pro-2.jpg"
                      return_reason: "Damaged"
                      quantity: 1
                      brand: "Mi"
                      product_category: "mobile"
                      questions:
                        - questions_id: "client Question id"
                          options: [""]
                          value: ["123456543"]
                          required: true
                          type: "varchar"
                          ques_images:
                            - "http://ecx.images-amazon.com/images/I/414yumheSAS._AC_.jpg"
                    - item: "mobile"
                      description: "Mi note 2 pro"
                      images:
                        - "https://static.toiimg.com/photo/55073523/Xiaomi-Mi-Note-2.jpg"
                      return_reason: "Damaged"
                      quantity: 2
                      brand: "Mi"
                      product_category: "apparel"
                      questions:
                        - questions_id: "client question id"
                          options: ["Black", "other"]
                          value: ["Black"]
                          required: true
                          type: "multi"
                          ques_images:
                            - "http://ecx.images-amazon.com/images/I/414yumheSAS._AC_.jpg"
              pickup_location:
                name: "pass the registered pickup WH name"
      responses:
        '200':
          description: Response indicating success or failure of shipment creation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateRVPQCResponse'
              examples:
                success:
                  summary: Successful shipment creation with RVP QC
                  value:
                    cash_pickups_count: 0.0
                    package_count: 1
                    upload_wbn: "UPL15809598291576112229"
                    replacement_count: 0
                    pickups_count: 0
                    packages:
                      - status: "Success"
                        client: "madura"
                        sort_code: "1209"
                        remarks: [""]
                        waybill: "227410150032"
                        cod_amount: 0.0
                        payment: "Pre-paid"
                        serviceable: true
                        refnum: "1234567890"
                    cash_pickups: 0.0
                    cod_count: 0
                    success: true
                    prepaid_count: 1
                    cod_amount: 0.0
                errorPackageCreation:
                  summary: Package creation error
                  value:
                    cash_pickups_count: 0
                    package_count: 0
                    upload_wbn: null
                    replacement_count: 0
                    rmk: "Package creation API error.Package might be saved.Please contact tech.admin@delhivery.com. Error message is 'NoneType' object has no attribute 'end_date' . Quote this error message while reporting."
                    pickups_count: 0
                    packages: []
                    cash_pickups: 0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    error: true
                    cod_amount: 0
                errorEmptyShipmentList:
                  summary: Empty shipment list error
                  value:
                    cash_pickups_count: 0
                    package_count: 0
                    upload_wbn: null
                    replacement_count: 0
                    rmk: "shipment list contains no data."
                    pickups_count: 0
                    packages: []
                    cash_pickups: 0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    error: true
                    cod_amount: 0
                errorInvalidWarehouse:
                  summary: Invalid warehouse error
                  value:
                    cash_pickups_count: 0
                    package_count: 0
                    upload_wbn: null
                    replacement_count: 0
                    rmk: "ClientWarehouse matching query does not exist."
                    pickups_count: 0
                    packages: []
                    cash_pickups: 0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    error: true
                    cod_amount: 0
                errorDuplicateWaybill:
                  summary: Duplicate waybill error
                  value:
                    cash_pickups_count: 0.0
                    package_count: 1
                    upload_wbn: "UPL2140142649026496454"
                    replacement_count: 0
                    rmk: "An internal Error has occurred, Please get in touch with client.support@delhivery.com"
                    pickups_count: 0
                    packages:
                      - status: "Fail"
                        client: "madura"
                        sort_code: null
                        remarks: ["Duplicate waybill"]
                        waybill: "227410150021"
                        cod_amount: 0.0
                        payment: "Pickup"
                        serviceable: false
                        refnum: "1234567890"
                    cash_pickups: 0.0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    cod_amount: 0.0
                errorWrongClient:
                  summary: Wrong client specified error
                  value:
                    cash_pickups_count: 0.0
                    package_count: 1
                    upload_wbn: "UPL16421742549891565175"
                    replacement_count: 0
                    rmk: "An internal Error has occurred, Please get in touch with client.support@delhivery.com"
                    pickups_count: 0
                    packages:
                      - status: "Fail"
                        client: "madura"
                        sort_code: null
                        remarks: ["u'Unable to consume waybill 227410150022 for madura, Hint: Check if the right client is specified for this manifest'"]
                        waybill: "227410150022"
                        cod_amount: 0.0
                        payment: "Pickup"
                        serviceable: false
                        refnum: "1234567890"
                    cash_pickups: 0.0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    cod_amount: 0.0
                errorPackageTypeNotServiceable:
                  summary: Package type not serviceable error
                  value:
                    cash_pickups_count: 0.0
                    package_count: 1
                    upload_wbn: "UPL6979090879560764201"
                    replacement_count: 0
                    rmk: "An internal Error has occurred, Please get in touch with client.support@delhivery.com"
                    pickups_count: 0
                    packages:
                      - status: "Fail"
                        client: "madura"
                        sort_code: null
                        remarks: ["Crashing while saving package due to exception 'Package type Pickup not serviceable for madura'. Package might have been partially saved."]
                        waybill: ""
                        cod_amount: 0.0
                        payment: "Pickup"
                        serviceable: false
                        refnum: "1234567890"
                    cash_pickups: 0.0
                    cod_count: 0
                    success: false
                    prepaid_count: 0
                    cod_amount: 0.0
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

## CRITICAL: Same Endpoint as Shipment Creation

This API uses the **same endpoint** (`/api/cmu/create.json`) as the regular Shipment Creation API. The difference is the presence of `client`, `qc_type`, and `custom_qc` fields in the shipment payload.

---

## Required Shipment Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Consignee name |
| `order` | string | Order ID |
| `phone` | array of strings | Consignee phone number(s) |
| `add` | string | Consignee address |
| `pin` | integer | Consignee pincode |
| `client` | string | **Registered client name** (required for RVP QC) |
| `custom_qc` | array | **QC items array** (required for RVP QC) |

---

## QC Question Types

| `type` | Behavior |
|--------|----------|
| `varchar` | Field Executive (FE) **types** the answer |
| `multi` | FE **selects** from provided `options` |

### `required` Field Behavior

| Value | Effect |
|-------|--------|
| `true` | Incorrect answer → QC **Failed** |
| `false` | Any answer accepted → QC always **Passed** (question still asked) |

### `value` Array

Only the **first element** is used as the correct answer. Even if multiple values are passed, only `value[0]` matters for QC validation.

---

## Custom QC Item Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Item description |
| `images` | array of URIs | Product images for FE reference |
| `quantity` | integer | Quantity (defaults to 1) |
| `questions` | array | QC questions for this item |

---

## CRITICAL: `payment_mode` for RVP Is `"Pickup"`

For reverse pickup shipments, use `"Pickup"` as the payment mode — not `"Prepaid"` or `"COD"`. If the client is not enabled for Pickup type, you'll get:

```
"Package type Pickup not serviceable for {client}"
```

---

## Known Error Scenarios (6 documented in spec)

| Error (`rmk` / `remarks`) | Cause |
|---------------------------|-------|
| `"ClientWarehouse matching query does not exist."` | Warehouse name doesn't match |
| `"shipment list contains no data."` | Empty `shipments` array |
| `"Package creation API error.Package might be saved..."` | Internal error — package may exist |
| `"Duplicate waybill"` (in `remarks`) | Waybill already used |
| `"Unable to consume waybill ... Hint: Check if the right client is specified"` (in `remarks`) | Wrong `client` name for the waybill |
| `"Package type Pickup not serviceable for {client}"` (in `remarks`) | Client not enabled for Pickup/RVP |

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Missing `client` field | Required for RVP QC — not needed for regular shipment creation |
| Missing `custom_qc` array | Required — the QC items define the inspection |
| Using `"Prepaid"` or `"COD"` for payment_mode | Use `"Pickup"` for RVP shipments |
| Wrong client name for waybill | Client must match the account the waybill belongs to |
| Assuming `value` array uses all elements | Only `value[0]` is the correct answer |
| Not providing `ques_images` | Optional but recommended — helps FE during inspection |
| Phone as string instead of array | Use `["1234567890"]`, not `"1234567890"` |
| Not checking per-package `status` in response | Batch can partially fail — check each package's `status` and `remarks` |
