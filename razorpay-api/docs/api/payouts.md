# Payouts toolset (RazorpayX, read-only)

> **When to load**: looking up RazorpayX payouts (money sent *out* to vendors/employees).

## Usage notes

- Payouts belong to **RazorpayX** (business banking), not the payment gateway. Calls fail unless
  RazorpayX is active for the key.
- `fetch_all_payouts` requires your RazorpayX `account_number` (the business account payouts are
  made from — shown in the RazorpayX Dashboard), not a customer's bank account.
- The MCP only reads payouts. Creating payouts, contacts and fund accounts is RazorpayX REST
  (`/v1/payouts`, `/v1/contacts`, `/v1/fund_accounts`) — outside this skill's MCP scope.
- Docs name `fetch_payout_by_id`; code registers `fetch_payout_with_id`.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `fetch_payout_with_id`

**Read** · remote ✅ · `GET /v1/payouts/{id}` (RazorpayX)

> Fetch a payout's details using its ID

| Param | Type | Constraints | Description |
|---|---|---|---|
| `payout_id` | string | REQUIRED | The unique identifier of the payout. For example, 'pout_00000000000001' |

## `fetch_all_payouts`

**Read** · remote ✅ · `GET /v1/payouts?account_number=` (RazorpayX)

> Fetch all payouts for a bank account number

| Param | Type | Constraints | Description |
|---|---|---|---|
| `account_number` | string | REQUIRED | The account from which the payouts were done.For example, 7878780080316316 |
| `count` | number | Min=1 | Number of payouts to be fetched. Default value is 10.Maximum value is 100. This can be used for pagination,in combination with the skip parameter |
| `skip` | number | Min=0 | Numbers of payouts to be skipped. Default value is 0.This can be used for pagination, in combination with count |
