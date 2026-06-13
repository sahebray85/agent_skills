# Create Shipment API — Specification

> **When to load**: User asks about creating shipments, manifesting orders, SPS (Single Piece Shipment), MPS (Multi-Piece Shipment), or booking consignments.

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
| **Purpose** | Generate a B2C shipment (SPS/MPS) in the Delhivery system with consignee details, pickup location, and shipment parameters |
| **Avg Latency (Prod)** | 283.57ms |
| **P99 Latency (Prod)** | 1.59s |
| **Rate Limit** | 20,000/5 min/IP |

---

## Full OpenAPI Specification

```yaml
info:
  title: Delhivery Create Shipment API
  description: |
    API specification for Delhivery Last Mile Express system. This API is used to generate a B2C shipment in the Delhivery system. The order creation process is the same for both forward flow (client warehouse → end customer) and reverse flow (customer → client warehouse), differing only in the `payment_mode` key: `Pickup` for reverse packages, `COD` or `Prepaid` for forward packages, and `REPL` for replacement shipments.

    **Important Notes:**
    - The request payload must include `format=json&data=` prefix before the JSON data
    - Phone numbers can have the following prefixes: `91`, `+91`, `91-`, `+91-`, `0`
    - Order ID (order field) must be less than 50 characters
    - Special characters `&`, `%`, `#`, `;`, `\` are not allowed in the API
    - For duplicate order validation, if 6 fields match (client name, order id, total amount, product description, payment mode, consignee name), the order will be rejected

    ## Rate Limit and Latency

    | Metrics | Value |
    |---|---|
    | Average Latency (PRODUCTION) | 283.57ms |
    | P99 Latency (PRODUCTION) | 1.59s |
    | Rate Limit (Requests/5 Minute/IP) (PRODUCTION) | 20,000/5 min/IP |

  x-performance-metrics:
    production:
      average-latency: "283.57ms"
      p99-latency: "1.59s"
  x-rate-limit:
    production:
      requests-per-5-minutes-per-ip: 20,000

servers:
  - url: https://staging-express.delhivery.com
    description: Staging environment
  - url: https://track.delhivery.com
    description: Production environment

tags:
  - name: Shipment Creation
    description: Operations related to shipment creation (SPS/MPS)

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
    Shipment: 
      type: object
      properties:
        name:
          type: string
          description: Name of the consignee
          example: "Consignee name"
        order:
          type: string
          description: Order ID
          example: "Test Order 01"
        phone:
          type: string
          description: Consignee phone number
          example: "9999999999"
        add:
          type: string
          description: Address of the consignee
          example: "Huda Market, Haryana"
        pin:
          type: integer
          description: Pincode of the consignee
          example: 110042
        address_type:
          type: string
          description: Address type (home/office)
          example: "home"
        ewbn:
          type: string
          description: Ewaybill number (for packages ≥ 50k)
          example: ""
        hsn_code:
          type: string
          description: HSN Code for e-waybill; more than one HSN can be passed if the quantity is > 1
          example: ""
        shipping_mode:
          type: string
          description: Shipping mode (Surface/Express)
          example: "Surface"
        seller_inv:
          type: string
          description: Seller invoice
          example: ""
        city:
          type: string
          description: City of the consignee
          example: "Gurugram"
        weight:
          type: number
          format: float
          description: Weight of the shipment (gms)
          example: 100
        return_name:
          type: string
          description: Return name
          example: ""
        return_address:
          type: string
          description: Return address
          example: ""
        return_city:
          type: string
          description: Return city
          example: ""
        return_phone:
          type: string
          description: Return phone number
          example: ""
        return_state:
          type: string
          description: Return state
          example: ""
        return_country:
          type: string
          description: Return country
          example: ""
        return_pin:
          type: integer
          description: Return pincode
          example: null
        seller_name:
          type: string
          description: Seller name
          example: ""
        fragile_shipment:
          type: boolean
          description: Indicates if the shipment contains fragile items (true/false)
          example: false
        shipment_height:
          type: number
          format: float
          description: Height of the shipment in cm
          example: 100
        shipment_width:
          type: number
          format: float
          description: Width of the shipment in cm
          example: 100
        shipment_length:
          type: number
          format: float
          description: Length of the shipment in cm
          example: null
        cod_amount:
          type: number
          format: float
          description: Cash on Delivery (COD) amount
          example: 0
        products_desc:
          type: string
          description: Product Description
          example: ""
        state:
          type: string
          description: State of the consignee (e.g., Rajasthan)
          example: "Haryana"
        dangerous_good:
          type: boolean
          description: Dangerous goods flag (true/false)
          example: false
        waybill:
          type: string
          description: |
            SPS: Waybill can be passed in the payload or can be skipped as well.
            MPS: Waybill needs to be passed for each box explicitly in the API.
          example: ""
        total_amount:
          type: number
          format: float
          description: Total amount
          example: 0
        seller_add:
          type: string
          description: Seller address
          example: ""
        country:
          type: string
          description: Country (mandatory for Bangladesh, 'BD' value)
          example: "India"
        plastic_packaging:
          type: boolean
          description: Plastic packaging flag (true/false)
          example: false
        quantity:
          type: string
          description: Quantity
          example: ""
        transport_speed:
          type: string
          description: |
            By passing the transport_speed field in the manifest request, you can choose:
            F – Next Day Delivery (NDD)
            OR
            D – Standard delivery (regular TAT)
          enum: [F, D]
          example: "D"
        payment_mode:
          type: string
          description: The value should be: Pickup for reverse shipments, COD or Prepaid for forward shipments and REPL for replacement shipments
          example: "Prepaid"
        order_date:
          type: string
          format: date
          nullable: true
          description: Order date
          example: null
        shipment_type:
          type: string
          description: |
            Shipment type. Use "MPS" for Multi-Piece Shipments.
          enum:
            - MPS
          example: "MPS"
        mps_amount:
          type: integer
          description: |
            Sum of all package amounts for COD. It will be zero in case of prepaid.
          example: 0
        mps_children:
          type: integer
          description: |
            Total number of packages including master and child packages.
          example: 2
        master_id:
          type: integer
          description: |
            This will master waybill and need to be passed with every box
          example: "xxxxxxxxxxxxx"
      required:
        - name
        - order
        - phone
        - add
        - pin
        - payment_mode

    CreateShipmentRequest:
      type: object
      properties:
        shipments:
          type: array
          items:
            $ref: '#/components/schemas/Shipment'
          description: Array of shipment objects
        pickup_location:
          type: object
          properties:
            name:
              type: string
              description: Name should be exactly the same as the name of the WH registered. It is case/space sensitive.
              example: "warehouse_name"
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
          example: "00c85f-HYPRCOM-do-cdp"
        sort_code:
          type: string
          description: Sort code
          example: "342"
        remarks:
          type: array
          items:
            type: string
          description: Remarks
          example: [""]
        waybill:
          type: string
          description: Generated waybill number
          example: "7160510000431"
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
          example: "Test Order 01"

    CreateShipmentResponse:
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
          example: "UPL1431491104292619890"
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
          example: "ClientWarehouse matching query does not exist."
        error:
          type: boolean
          description: Error flag (only present when success is false)
          example: false

paths:
  /api/cmu/create.json:
    post:
      tags:
        - Shipment Creation
      summary: Create shipment(s)
      description: |
        Generates a B2C shipment (SPS/MPS) in the Delhivery system. The order creation process is the same for forward flow (Prepaid/COD), reverse flow (Pickup), and replacement flow (REPL), differing only in the payment_mode key.
        For SPS: Waybill can be passed in the payload or can be skipped.
        For MPS: Waybill needs to be passed for each box explicitly in the API.
      operationId: createShipment
      x-common-remarks:
        - error: "Authentication credentials were not provided"
          reason: "This error comes when we do not pass the Authorization Token in the API Header."
          solution: "Need to pass correct Authorization Token under API Header."

        - error: "shipment list contains no data"
          reason: "This error comes when we do not pass the correct client name under the 'client' payload in the API."
          solution: "You will have to pass the exact client name registered with us (Please note that client name is case sensitive)."

        - error: "Unterminated string starting at: line … column … (char …)"
          reason: "This error means that the special character you are using in the mentioned API line is not allowed in our API."
          solution: "Please do not pass the below-mentioned special characters in the API: & % # ; \\"

        - error: "format key missing in the post"
          reason: "That means you are missing JSON format static value on top of the API body."
          solution: "'format=json&data=' (without quotes) is mandatory to pass in the request payload in order creation in our system."

        - error: "Unable to consume waybill XXXX"
          reason: "This issue only occurs if there is a mismatch in the allocated waybill series or the waybill is already consumed."
          solution: "Please validate the Waybill before passing in the waybill and fetch the waybill in advance before passing that in API. You can fetch the waybill using our fetch waybill API."

        - error: "ClientWarehouse matching query does not exist."
          reason: "This error comes when we do not pass the correct warehouse name in the 'name' field of the 'pickup_location' dictionary."
          solution: "Please pass the correct warehouse/Pickup_location name under 'pickup_location', 'name' OR use warehouse creation API to create a new warehouse for your account."

        - error: "Client-Warehouse is not active."
          reason: "This means the warehouse name that you are using under the 'pickup_location', 'name' field is currently Inactive at our end."
          solution: "Please connect with your Delhivery account POC (Spokesperson) to get this activated or for further discussion on it."

        - error: "Crashing while saving package due to exception suspicious order/consignee"
          reason: "The shipment manifestation has failed because the consignee is Suspicious."
          solution: "Please connect with your Delhivery business account POC to discuss this further."

        - error: "Crashing while saving package due to exception PUR (shipment pickup from seller) failure rate of the seller is very high."
          reason: "The error comes because the PUR failure rate of the seller is very high."
          solution: "Please connect with your Delhivery account POC to discuss this further."

        - error: "Duplicate Order Id"
          reason: |
            This error comes when we pass the same Order ID which is already created for the same account.
            If the following 6 fields are the same for 2 orders then the 2nd order will fail:
              - client name
              - order id
              - total amount
              - product description
              - payment mode
              - consignee name
          solution: "Use a unique combination of the above 6 fields for each order."

        - error: "Crashing while saving package due to exception 'client manifest charge API failed due to insufficient balance'. Package might have been partially saved."
          reason: "This error occurs while Manifesting the Shipment OR generating the Pickup Request due to insufficient wallet balance."
          solution: "Recharge your wallet with a minimum of 500 to Manifest the shipment and raise the Pickup request."

        - error: "Error message is 'unicode' object has no attribute 'get'"
          reason: "This error comes when you do not pass shipment as a list."
          solution: "Please pass shipment as a list in the Manifestation API's Payload."

        - error: "Crashing while saving package due to exception 'Package type Pickup/COD/REPL/Prepaid not serviceable for this account'. Package might have been partially saved."
          reason: "This error comes when the service 'payment_mode' you are using in API is not enabled for your account."
          solution: "Please connect with your Delhivery POC to get the required service enabled for your account."

        - error: "Crashing while saving package due to exception 'XXXXXX is non serviceable pincode'. Package might have been partially saved."
          reason: "This error comes when we use Non-serviceable Pincode in Manifestation API."
          solution: "Please use a serviceable PIN code and try to manifest the shipment. You can use Pincode serviceability API to check the serviceability of Pincodes."

        - error: "Incorrect phone number(s) for order *****"
          reason: "The Phone number you have passed under the 'phone' payload in API has some Ambiguity."
          solution: |
            Please pass the correct phone number. Phone numbers passed during manifestation undergo format checks.
            The number can have the below prefixes: 91, +91, +91-, 91-, 0

        - error: "Duplicate waybill"
          reason: "This error comes when we use the same waybill in the Manifestation API which has been already manifested earlier."
          solution: "Use a different waybill number."

        - error: "oid does not pass the validator <lambda>.check if there any extra character or dots in column"
          reason: "This error comes when we use the Order ID value as more than 50 characters. The max character allowed in the 'order' field is 50."
          solution: "Use less than 50 characters and test again."

        - error: "Crashing while saving package due to exception Manifestation failed as the total shipment volume has exceeded the available capacity of this pincode. Package might have been partially saved."
          reason: "You have exceeded the daily shipment manifestation capacity for this pincode."
          solution: "You may try again after midnight. Alternatively, for urgent shipment manifestation, please get in touch with your Delhivery account point of contact (POC)."
      security:
        - TokenAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateShipmentRequest'
            examples:
              sps_shipment:
                summary: Single Piece Shipment (SPS)
                value:
                  pickup_location:
                    name: "warehouse_name"
                  shipments:
                    - name: "Consignee name"
                      add: "Huda Market, Haryana"
                      pin: "110042"
                      city: "Gurugram"
                      state: "Haryana"
                      country: "India"
                      phone: "9999999999"
                      order: "Test Order 01"
                      payment_mode: "Prepaid"
                      return_pin: ""
                      return_city: ""
                      return_phone: ""
                      return_add: ""
                      return_state: ""
                      return_country: ""
                      products_desc: ""
                      hsn_code: ""
                      cod_amount: ""
                      order_date: null
                      total_amount: ""
                      seller_add: ""
                      seller_name: ""
                      seller_inv: ""
                      quantity: ""
                      waybill: ""
                      shipment_width: "100"
                      shipment_height: "100"
                      weight: ""
                      shipping_mode: "Surface"
                      address_type: ""
              mps_shipment:
                summary: Multi-Piece Shipment (MPS)
                value:
                  pickup_location:
                    name: "warehouse_name"
                  shipments:
                    - order: "123456"
                      weight: "100"
                      mps_amount: "0"
                      mps_children: "2"
                      pin: "122002"
                      products_desc: "Toys, ToyCar"
                      add: "Test Address"
                      shipment_type: "MPS"
                      state: "TAMIL NADU"
                      master_id: "xxxxxxxxxxxxx"
                      city: "CHENNAI"
                      waybill: "xxxxxxxxxxxxx"
                      phone: "9999888800"
                      payment_mode: "Prepaid"
                      name: "Test Name"
                      total_amount: "4250"
                      country: "India"
                    - order: "orderiod"
                      weight: "100"
                      mps_amount: "0"
                      mps_children: "2"
                      pin: "600063"
                      products_desc: "product description"
                      add: "Consignee Address"
                      shipment_type: "MPS"
                      state: "TAMIL NADU"
                      master_id: "xxxxxxxxxxxxx"
                      city: "CHENNAI"
                      waybill: "xxxxxxxxxxxxx"
                      phone: "9999888800"
                      payment_mode: "Prepaid"
                      name: "Consignee Naame"
                      total_amount: "4250"
                      country: "India"
      
      responses:
        '200':
          description: Response indicating success or failure of shipment creation
          headers:
            X-RateLimit-Limit:
              description: Maximum number of requests allowed per 5 minutes per IP
              schema:
                type: integer
            X-RateLimit-Remaining:
              description: Number of requests remaining in the current rate limit window
              schema:
                type: integer
            X-RateLimit-Reset:
              description: Time in seconds until the rate limit window resets
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateShipmentResponse'
              examples:
                success:
                  summary: Successful shipment creation
                errorPackageCreation:
                  summary: Package creation error
                errorInvalidWarehouse:
                  summary: Invalid warehouse error
        '429':
          description: Too Many Requests - Rate limit exceeded
          headers:
            Retry-After:
              description: Time in seconds until the rate limit window resets
              schema:
                type: integer
          content:
            application/json:
              example:
                error: Rate limit exceeded. Please retry after some time.
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

## CRITICAL: Payload Must Use `format=json&data=` Prefix

The request payload must include the `format=json&data=` prefix before the JSON data. This is a Delhivery-specific requirement.

---

## CRITICAL: `phone` Is a String (NOT Array)

Phone numbers must be passed as plain strings:

```json
"phone": "9999999999"       // ✅ correct
"phone": ["9999999999"]     // ❌ wrong
```

Phone numbers can have prefixes: `91`, `+91`, `91-`, `+91-`, `0`

---

## CRITICAL: Order ID Restrictions

- Must be **less than 50 characters**

---

## CRITICAL: Duplicate Order Validation

If **all 6 fields** match an existing order, the new order will be **rejected**:
1. Client name
2. Order ID
3. Total amount
4. Product description
5. Payment mode
6. Consignee name

---

## CRITICAL: `pickup_location.name` Is Case/Space Sensitive

The warehouse name must **exactly match** the registered warehouse name — including case and spaces.

---

## Forward, Reverse (RVP), and Replacement (REPL) Flows

The order creation process is the same for all flows — only the `payment_mode` key differs:

| Flow | `payment_mode` | Direction |
|------|---------------|-----------|
| **Forward** | `Prepaid` or `COD` | Client warehouse → End customer |
| **Reverse (RVP)** | `Pickup` | Customer → Client warehouse |
| **Replacement (REPL)** | `REPL` | Exchange flow (pickup + delivery in one waybill) |

---

## Key Changes in Order Creation for RVP

- Set `payment_mode` as `"Pickup"` in the manifest payload.
- When `"Pickup"` is used, the **customer information** will be treated as the **pickup location**. The `return_add` and other return-related fields will be used to define the **drop/delivery address**.
- If both a return address and a pickup location are provided for a pickup shipment, the system will **prioritize the return address**, and the shipment will be delivered there.

---

## Key Changes in Order Creation for REPL

- Set `payment_mode` as `"REPL"` in the manifest payload.
- A **single waybill** will be generated, and the entire exchange journey will be executed using this one waybill.
- The **pickup location** will serve as the pickup address, **customer address** as the exchange location, and **return address** will be treated as the final delivery address for the REPL shipment after successful exchange.
- If the return address is not provided, the **pickup location** will be used as the final delivery address for the exchange shipment.

---

## SPS vs MPS Shipments

- **Single Piece Shipment (SPS):** One waybill represents a package that can contain multiple items (e.g., an order with t-shirts, shoes, and shampoo packed together).
- **Multi Piece Shipment (MPS):** Contains multiple boxes within one order. Each box should have its own waybill number.

| Feature | SPS (Single Piece Shipment) | MPS (Multi-Piece Shipment) |
|---------|----------------------------|---------------------------|
| **Waybill** | Optional — can be passed or skipped | **Required** — must be passed for each box explicitly |
| **`shipment_type`** | Not required | Must be set to `"MPS"` |
| **`mps_children`** | Not applicable | Total number of packages (master + child) |
| **`mps_amount`** | Not applicable | Sum of all package amounts for COD (0 for prepaid) |
| **`master_id`** | Not applicable | Master waybill number — must be passed with every box |

---

## Transport Speed Options

| Value | Description |
|-------|-------------|
| `F` | Next Day Delivery (NDD) |
| `D` | Standard delivery (regular TAT) |

---

## Required Shipment Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Consignee name |
| `order` | string | Order ID (< 50 chars, no `&%#;\`) |
| `phone` | string | Consignee phone number |
| `add` | string | Consignee address |
| `pin` | integer | Consignee pincode |
| `pickup_location` | string | Name should be exactly the same as the name of the WH registered. It is case/space sensitive. |
| `payment_mode` | string | The value should be: Pickup for reverse shipments, COD or Prepaid for forward shipments and REPL for replacement shipments |

---

## Additional MPS-Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `shipment_type` | string | Must be `"MPS"` |
| `mps_children` | integer | It is sum of master and child package |
| `mps_amount` | integer | Sum of all package amounts for cod. It will be zero in case of prepaid |
| `master_id` | integer | This will master waybill and need to be passed with every box |
| `waybill` | string | **Required** for each box in MPS |

---

## Known Error Scenarios

| Error | Cause | Solution |
|-------|-------|----------|
| `"Authentication credentials were not provided"` | Missing Authorization Token in header | Pass correct `Authorization: Token <your-token>` header |
| `"shipment list contains no data"` | Incorrect client name in payload | Pass the exact registered client name (case sensitive) |
| `"Unterminated string starting at..."` | Special characters in payload | Remove `&`, `%`, `#`, `;`, `\` characters |
| `"format key missing in the post"` | Missing `format=json&data=` prefix | Add `format=json&data=` before JSON data |
| `"Unable to consume waybill XXXX"` | Waybill mismatch or already consumed | Validate waybill before passing; use Bulk Waybill API to fetch |
| `"ClientWarehouse matching query does not exist."` | Incorrect warehouse name | Pass exact warehouse name or create one via Warehouse Create API |
| `"Client-Warehouse is not active."` | Warehouse is inactive | Contact Delhivery account POC to activate |
| `"Crashing...suspicious order/consignee"` | Consignee flagged as suspicious | Contact Delhivery business account POC |
| `"Crashing...PUR failure rate of the seller is very high."` | High PUR failure rate | Contact Delhivery account POC |
| `"Duplicate Order Id"` | Same 6-field combination already exists | Use a unique combination of client name, order ID, total amount, product description, payment mode, consignee name |
| `"...insufficient balance..."` | Insufficient wallet balance | Recharge wallet with minimum ₹500 |
| `"'unicode' object has no attribute 'get'"` | Shipments not passed as a list | Pass `shipments` as an array |
| `"Package type ... not serviceable for this account"` | Payment mode not enabled for account | Contact Delhivery POC to enable the service |
| `"XXXXXX is non serviceable pincode"` | Non-serviceable pincode | Check serviceability via Pincode Serviceability API |
| `"Incorrect phone number(s) for order..."` | Invalid phone number format | Use valid phone number with allowed prefixes: `91`, `+91`, `+91-`, `91-`, `0` |
| `"Duplicate waybill"` | Waybill already used | Use a different waybill number |
| `"oid does not pass the validator..."` | Order ID > 50 characters | Keep order ID under 50 characters |
| `"...total shipment volume has exceeded the available capacity..."` | Daily pincode capacity exceeded | Retry after midnight or contact Delhivery account POC |

---

## Important Notes

- Try to include **all fields** mentioned in the sample payload, even if they are not mandatory. These fields are considered good to have for **optimal processing**.
- The raw JSON body does not accept special characters: `&`, `#`, `%`, `;`, `\`. Use URL-encoded payloads instead.
- The **Order ID** must be unique for each new order.

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Missing `format=json&data=` prefix | Must prefix payload with `format=json&data=` |
| Phone as array | Use plain string `"9999999999"`, not array |
| Order ID ≥ 50 chars | Must be under 50 characters |
| Using `&`, `%`, `#`, `;`, `\` in fields | These special characters are forbidden |
| Wrong warehouse name casing | Must be **exact** match — case and space sensitive |
| Skipping waybill for MPS | MPS requires pre-generated waybills per box |
| Not checking per-package `status` | Batch can succeed overall but individual packages may fail |
| Assuming `"Package might be saved"` means failure | Package may actually exist — verify before retrying to avoid duplicates |
| Using non-serviceable pincode | Check serviceability via Pincode Serviceability API before creating |
| Insufficient wallet balance | Ensure minimum ₹500 balance before manifesting |
| Using wrong `payment_mode` for RVP | Use `"Pickup"` for reverse, `"REPL"` for replacement |
| Not providing return address for REPL | If missing, pickup location becomes final delivery address |
