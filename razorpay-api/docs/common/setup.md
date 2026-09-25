# Connecting the Razorpay MCP server

> **When to load**: user wants to install/connect the Razorpay MCP, gets 401 / "no Razorpay tools",
> needs a tool the hosted server lacks, or wants read-only / limited toolsets.

## Pick a deployment

| Need | Use |
|---|---|
| Read data, create orders/links/QRs, capture | **Remote** `https://mcp.razorpay.com/mcp` (streamable HTTP; `/sse` is deprecated) |
| `create_refund`, `close_qr_code`, `create_instant_settlement`, `create_registration_link` | **Local** (Docker image `razorpay/mcp` or Go binary) — remote does not expose these |
| Guarantee no money-moving calls | Local with `READ_ONLY=true`, or remote via OAuth (only scope is `read_only`) |
| Limit surface area | Local with `TOOLSETS=payments,orders,...` (default `all`) |

Toolset names: `payments`, `orders`, `payment_links`, `refunds`, `qr_codes`, `settlements`,
`payouts`, `registration_links`, `checkout_integration`.

Test vs live is decided **only by the key pair** (`rzp_test_…` vs `rzp_live_…`); same URL, same
tools. Objects created in one mode don't exist in the other.

## Build the merchant token (remote)

Token = base64 of `KEY_ID:KEY_SECRET` with **no trailing newline**. Razorpay's own docs show
`echo KEY:SECRET | base64`, which also encodes the `\n` that `echo` appends — if auth fails with
401, this is the first thing to check.

```bash
# bash / git-bash / macOS
printf '%s:%s' "$RAZORPAY_KEY_ID" "$RAZORPAY_KEY_SECRET" | base64 | tr -d '\n'
```
```powershell
# PowerShell
[Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($env:RAZORPAY_KEY_ID):$($env:RAZORPAY_KEY_SECRET)"))
```

Never paste the secret or token into chat, commits, or `.mcp.json` literals.

## Claude Code — remote

```bash
export RZP_MCP_TOKEN=$(printf '%s:%s' "$RAZORPAY_KEY_ID" "$RAZORPAY_KEY_SECRET" | base64 | tr -d '\n')
claude mcp add --transport http razorpay https://mcp.razorpay.com/mcp \
  --header "Authorization: Basic $RZP_MCP_TOKEN"
```

`claude mcp add` stores the header value in user config. For a shared project `.mcp.json`, keep the
secret out of git with env-var expansion:

```json
{ "mcpServers": { "razorpay": {
    "type": "http", "url": "https://mcp.razorpay.com/mcp",
    "headers": { "Authorization": "Basic ${RZP_MCP_TOKEN}" } } } }
```

Clients without native HTTP transport (Claude Desktop, Cursor) use the bridge:
`npx mcp-remote https://mcp.razorpay.com/mcp --header "Authorization: Basic <token>"`.

## Claude Code — local (all 45 tools)

```bash
claude mcp add razorpay-local \
  -e RAZORPAY_KEY_ID=rzp_test_xxx -e RAZORPAY_KEY_SECRET=xxx \
  -e TOOLSETS=all -e READ_ONLY=false \
  -- docker run --rm -i -e RAZORPAY_KEY_ID -e RAZORPAY_KEY_SECRET -e TOOLSETS -e READ_ONLY razorpay/mcp
```

Local uses the raw key/secret (no base64). Binary alternative:
`razorpay-mcp-server stdio --key … --secret … --toolsets … --read-only --log-file …`.

## Verify

1. `claude mcp list` → server shows **connected**.
2. Call `fetch_all_payments` with `{"count": 1}` — cheapest authenticated read.
3. Compare the tool list to [REFERENCE.md](../../REFERENCE.md): missing W tools means remote
   restriction, `READ_ONLY`, OAuth `read_only`, or `TOOLSETS` filtering.
