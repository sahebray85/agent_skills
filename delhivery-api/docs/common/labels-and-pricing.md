# Labels & Pricing — Common Patterns

> **Scope**: Label generation and pricing calculation patterns for Delhivery B2C APIs.

---

## 1. Shipping Label Generation

### 1.1 Label API

Use the Shipping Label API (Packing Slip API) to generate shipping labels for your shipments.

### 1.2 PDF Output

**To get a direct PDF** instead of HTML, use the `pdf` parameter:

```
GET /api/p/packing_slip?wbns=<waybill>&pdf=true
```

**Without `pdf=true`**: The API returns HTML content that you need to render/convert to PDF yourself.

**With `pdf=true`**: The API returns a direct PDF file that you can download and print.

### 1.3 Label Size Options

The Packing Slip API supports different label sizes via the `pdf_size` parameter:
- `A4`: Standard A4 paper size
- `4R`: 4x6 inch thermal label size

Choose the size based on your printer type (standard printer vs thermal printer).

---

## 2. Shipping Cost Calculation

### 2.1 Pricing API

Use the Invoice Charges API to get estimated shipping charges for your shipments.

### 2.2 Environment Differences

**Staging Environment**:
- Returns `0` for all pricing calculations
- Use staging only for integration testing, not for actual cost estimates

**Production Environment**:
- Returns real pricing based on your contract with Delhivery
- **Requires `pt` parameter**: You must specify the payment type (`Pre-paid` or `COD`)
- Pricing varies based on:
  - Origin and destination pincodes
  - Package weight and dimensions
  - Payment mode (Prepaid vs COD)
  - Your negotiated rates with Delhivery

### 2.3 Payment Type Parameter

The `pt` (payment type) parameter is **required in production**:
- `Pre-paid`: Customer paid online before shipment
- `COD`: Cash on Delivery — customer pays upon delivery

**Example**:
```
GET /api/kinko/v1/invoice/charges/.json?md=S&cgm=500&pt=Pre-paid&ss=Delivered
```

---

## 3. Bulk Waybill API

### 3.1 Purpose

The Bulk Waybill API allows you to pre-fetch waybill numbers in advance, before creating shipments.

### 3.2 Usage Limits

**Per Request**:
- Maximum: 10,000 waybills per request

**Rate Limit**:
- Maximum: 50,000 waybills every 5 minutes

### 3.3 Best Practices

**Store in Database**: 
- Pre-fetch waybills and store them in your database
- Do NOT fetch waybills and immediately use them in the same request flow
- Maintain a pool of available waybills

**Separation of Concerns**:
- Waybill fetching should be a separate background process
- Shipment creation should pull from your waybill pool
- This prevents race conditions and ensures waybill availability

**When to Pre-fetch**:
- Only pre-fetch if you need to assign waybill numbers before shipment creation
- If you don't need pre-assigned waybills, leave the waybill field blank and let Delhivery auto-generate them

---

## 4. Implementation Guidance

### 4.1 Label Generation

1. After creating a shipment, use the returned waybill number
2. Call the Packing Slip API with `pdf=true` to get the label
3. Store or immediately print the label
4. Consider caching labels to avoid regenerating them

### 4.2 Pricing Calculation

1. Always call the pricing API before showing costs to customers
2. Cache pricing for common routes (with appropriate TTL)
3. Remember that staging returns `0` — use production for real estimates
4. Include the `pt` parameter in production calls

### 4.3 Waybill Management

1. Set up a background job to maintain a waybill pool
2. Fetch waybills in batches (e.g., 5,000 at a time)
3. Mark waybills as "used" when assigned to shipments
4. Monitor your waybill pool and refill when running low
5. Respect the rate limits (50k per 5 minutes)

---

## 5. Common Issues

### 5.1 "Pricing returns 0 in production"

**Cause**: Missing `pt` parameter

**Solution**: Add `pt=Pre-paid` or `pt=COD` to your request

### 5.2 "Waybill API rate limit exceeded"

**Cause**: Fetching more than 50,000 waybills in 5 minutes

**Solution**: 
- Implement rate limiting in your waybill fetching logic
- Spread out requests over time
- Fetch in smaller batches

### 5.3 "Label generation is slow"

**Cause**: PDF generation takes time, especially for batch requests

**Solution**:
- Generate labels asynchronously
- Cache generated labels
- Consider generating labels in background jobs rather than during shipment creation
