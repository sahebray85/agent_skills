# Workflow — Marketing campaign (template + media header + receipts)

> **Scope**: Sending one approved marketing template to many recipients and tracking outcomes. Load when the user builds a bulk/campaign sender, a drain or an outbox over the Cloud API.

---

## 1. Rules that shape the design

| Rule | Consequence for the sender |
|---|---|
| Marketing needs an **APPROVED MARKETING template**; free-form text is never allowed outside the 24 h window | Check the template's status before the run, not per message |
| **Per-user marketing limits** (error 131049): Meta caps how many marketing templates one person receives from all businesses | Treat 131049 as "defer this recipient 24 h", not as a failure and not as a channel problem |
| **Rapid messaging to one recipient** (131056) | Defer that recipient about an hour |
| **Messaging tier**: unique recipients per 24 h per number (250 unverified → 1k → 10k → 100k → unlimited) | A daily cap in config that mirrors the tier; the tier rises with quality and volume |
| **Throughput**: 80 messages per second per number by default | Pace sends; a burst earns 130429 |
| **Marketing to US (+1) numbers paused since 2025-04-01** | Suppress +1 at list build time; the API returns 131026-style failures otherwise |
| **Media ids expire after 30 days** | Upload the leaflet once per campaign and re-upload after about 29 days |
| **Quality rating** drops with blocks and reports; a RED rating lowers the tier and can pause the template | Honour opt-outs before each send, cap frequency, make STOP easy |
| **India billing in INR** by 2026-12-31 | Owner task; not a code change |

---

## 2. Sequence

```
build list ──► suppress opt-outs, +1, duplicates
           ──► template check (APPROVED, param count, header format matches leaflet)
           ──► upload media once → media id (cache; TTL 29 d)
           ──► for each recipient (paced, under the daily cap, inside the send window you choose):
                 POST /messages type=template
                 200 → store wamid, mark SENT
                 4xx → bucket the code:
                       AUTH/ACCOUNT/TEMPLATE/QUOTA → pause the whole channel (systemic)
                       131049 → defer 24 h      131056 → defer 1 h
                       131026/131047/131051/131052 → fail this recipient only
                       transport / 5xx / unknown → retry later
           ──► webhooks statuses[]: delivered / read / failed(errors[].code) move the row forward only
```

Buckets and the full code table: `common/errors.md`. Send body: `messaging/send_template.md`. Media: `media/upload.md`. Receipts: `webhooks/statuses.md`.

---

## 3. Template check before a run

```
GET /{WABA_ID}/message_templates?fields=name,language,status,components,parameter_format&limit=100
  page with paging.cursors.after until the (name, language) pair is found or paging.next is absent
```

Verify: `status == APPROVED`; the BODY placeholder count equals the parameters you will send (positional `{{1}}..{{n}}`, or NAMED with `parameter_name`); the HEADER `format` matches the asset (IMAGE for JPG/PNG, DOCUMENT for PDF, VIDEO for MP4). The current reference documents only `fields, limit, after, before` as query params, so do not rely on a `name=` filter.

---

## 4. Template send with an image header and positional body params

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "919999999999",
  "type": "template",
  "template": {
    "name": "exhibition_invite",
    "language": { "code": "en" },
    "components": [
      { "type": "header", "parameters": [ { "type": "image", "image": { "id": "<MEDIA_ID>" } } ] },
      { "type": "body", "parameters": [
          { "type": "text", "text": "Priya" },
          { "type": "text", "text": "Saturday 12 October" }
      ] }
    ]
  }
}
```

For a PDF leaflet use `{ "type": "document", "document": { "id": "<MEDIA_ID>", "filename": "leaflet.pdf" } }` in the header. Exact field rules and the response: `messaging/send_template.md`.

---

## 5. Outcome handling

| Signal | Where | Meaning | Do |
|---|---|---|---|
| 200 `messages[0].id` | send response | accepted by Meta | store wamid, status SENT |
| 200 with `message_status: held_for_quality_assessment` | send response | Meta is evaluating the template | treat as SENT; watch the template webhook |
| `statuses[].status = delivered / read` | webhook | reached the phone / opened | DELIVERED / READ, forward only |
| `statuses[].status = failed`, `errors[0].code = 131026` | webhook | not a WhatsApp user | BOUNCED, do not retry |
| `statuses[].status = failed`, other code | webhook | asynchronous failure | FAILED, consult `common/errors.md` |
| no webhook for days | — | normal for `sent` (never-online phones) | leave as SENT |

---

## 6. Opt-out and consent

- Every marketing template should make opting out obvious (a quick-reply "Stop" button or "reply STOP" in the body). Treat the reply as an opt-out and never message that number again on that purpose.
- Keep consent keyed on the normalised address, not the customer record, so a shared number is honoured for everyone using it.
- Meta's own block/report is invisible to you except as a falling quality rating.

Inbound handling: `workflows/inbound_chat_and_optout.md`.

---

## Sources

- Per-user marketing limits: https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-limits (verified 2026-10-04)
- Template API query params: https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api (verified 2026-10-04)
- Error codes: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes (verified 2026-10-04)
- Pricing and INR dates: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing (verified 2026-10-04)
- Throughput and tier numbers: see `common/rate_limits.md` and `account/messaging_limits_tiers.md` for the verification status of each figure.
