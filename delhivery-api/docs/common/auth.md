# Authentication — Common Patterns

> **Scope**: Authentication patterns shared across ALL Delhivery B2C APIs. Load this when writing integration code for any API.

---

## 1. Primary Scheme — Token Authentication

Most Delhivery B2C APIs use the **Token** scheme in the Authorization header.

```
Authorization: Token <YOUR_TOKEN>
```

**CRITICAL**: The prefix is `Token`, NOT `Bearer`. This is the most common authentication mistake.

### Header Construction

```
Headers:
  Authorization: Token <token_value>
  Content-Type: application/json
  Accept: application/json
```

---

## 2. Alternative Schemes

### 2.1 Bearer (JWT)

**Used by**: Expected TAT API

```
Authorization: Bearer <YOUR_JWT_TOKEN>
```

The Expected TAT API accepts both `Bearer <JWT>` and `Token <client_token>`. Check the API-specific spec for which scheme is required.

### 2.2 Query Parameter

**Used by**: Bulk Waybill Generation API

The Bulk Waybill API passes the token as a **query parameter**, NOT in the Authorization header:

```
GET /waybill/api/bulk/json/?token=<YOUR_TOKEN>&count=5
```

---

## 3. Token Management Rules

1. **Store securely**: Read the token from environment variables (`os.getenv` or equivalent). Never hardcode in source code.
2. **Centralize header construction**: Build a shared helper function that constructs headers. Accept optional parameters for token override and authentication scheme.
3. **Handle 401/403 responses**: When a 401 (Unauthorized) or 403 (Forbidden) response is received, trigger a token refresh flow — do NOT retry with the same token.
4. **Never log full tokens**: Log only a masked version (e.g., first 8 characters + `***`).

### Token Characteristics

- **Static tokens**: Delhivery B2C API tokens are static and unique per client account or sub-account.
- **No expiration**: Unlike JWT tokens, these tokens do not expire and do not need refresh flows.
- **Account-specific**: Each client account or sub-account has its own unique token.

---

## 4. CORS Restrictions

**Browser calls are blocked** due to CORS (Cross-Origin Resource Sharing) restrictions on Delhivery APIs.

**Solution**: Always make API calls from a backend server, not directly from browser JavaScript. If you need to call Delhivery APIs from a frontend application, create a backend wrapper/proxy that:
1. Receives requests from your frontend
2. Adds the authentication token
3. Forwards the request to Delhivery APIs
4. Returns the response to your frontend

**Never expose your API token in frontend code** — it would be visible to anyone inspecting the browser.

---

---

## 5. Rate Limiting & WAF Protection

### 5.1 Rate Limit

Delhivery APIs enforce rate limiting to prevent abuse:

**Limit**: 750 requests per 5 minutes per token

**403 Forbidden Response**: When you exceed the rate limit, you'll receive a `403 Forbidden` response.

**Handling**:
1. Implement request throttling in your application
2. If you receive a 403, pause for 30 seconds before retrying
3. Consider implementing a request queue with rate limiting
4. Monitor your request volume to stay well below the limit

### 5.2 WAF (Web Application Firewall)

Delhivery uses WAF protection that may trigger on suspicious patterns:
- Too many requests in a short time
- Unusual request patterns
- Invalid or malformed requests

**If blocked by WAF**:
1. Pause requests for 30 seconds
2. Review your request patterns
3. Ensure you're not sending malformed requests
4. Contact Delhivery support if the issue persists

---

## 6. Environment-Specific URLs

### Production vs Staging

- **Staging**: `https://staging-express.delhivery.com`
- **Production**: `https://track.delhivery.com` (replace `staging-express` with `track`)

**Token Mismatch Errors**: If you see errors like `NoneType...end_date`, verify that:
1. You're using the correct token for the environment
2. Your staging token is being used with staging URLs
3. Your production token is being used with production URLs

Tokens are environment-specific and will not work across environments.

---

## 7. Implementation Guidance

When helping a developer integrate authentication:

1. Check if they already have token management in their codebase.
2. If yes, extend their existing pattern.
3. If no, suggest a simple helper function that:
   - Reads the token from configuration
   - Accepts an optional scheme parameter (default: `Token`)
   - Returns a complete headers dictionary
4. Recommend storing the token in their existing secrets management system (env vars, `.env` file, secrets manager — whatever they already use).
5. Remind them about CORS restrictions if they're building a web application.
6. Implement rate limiting to stay below 750 requests per 5 minutes.
