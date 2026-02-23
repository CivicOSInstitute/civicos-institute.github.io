# donor-stewardship templates

## Acknowledgment queue file
Filename:
- `ack-[donor_id]-[YYYY-MM-DD].md`

YAML header schema:
```yaml
id: ack-[donor_id]-[gift_date]
type: acknowledgment_letter
destination_type: email
destination: [donor email]
donor_first_name: [first name only]
gift_amount: [amount]
gift_date: [date]
gift_tier: [1-4]
priority: standard # high if >$500, urgent if >$2500
crm_gift_id: [CRM gift record ID]
status: pending
created: [ISO timestamp]
model: [local/qwen-14b or openai/codex]
```

Body template guidance:
- Explicitly reference amount + date
- Mention one concrete impact statement tied to program config
- Avoid banned boilerplate phrases
- Keep to tier word-length limits

## Telegram alert template (privacy-safe)
`📬 Acknowledgment draft ready — [FirstName], $[amount], Tier [N]. Reply APPROVE [id] / EDIT [id] / HOLD [id] / REJECT [id]`

No full donor record details in message body.

## Morning brief stewardship block
```
DONOR STEWARDSHIP ALERTS
Acknowledgment queue: [N] pending
Lapse prevention — act this week: [N]
Lapse prevention — 60-90 day window: [N]
Recurring payment issues: [N]
Major donor attention needed: [N]
```

## Portfolio health dashboard format
Use aggregated-only output:
- Acquisition
- Retention rate + risk signal
- Revenue vs budget
- Major donor count only
- Recurring counts + MRR
- Queue and pipeline counts
