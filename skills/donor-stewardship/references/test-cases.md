# donor-stewardship test cases & eval

## Should-trigger
1. "Burt, I need a briefing on [donor name] before my call with her at 2pm"
2. "Who are our donors closest to lapsing right now?"
3. "Draft an acknowledgment for the donation that just came in"
4. "Show me our donor portfolio health"
5. "Get me a re-engagement draft for anyone who gave last October and hasn't given since"
6. "How many new donors did we get this month compared to last year?"
7. CRM poll detects new gift (automatic trigger)
8. Retention drops below 55% (automatic council trigger)

## Should-NOT-trigger
1. "Draft a grant proposal for the NEA"
2. "Schedule the board meeting reminder"
3. "Post our AI literacy tip to LinkedIn"
4. "What's the deadline for the MacArthur LOI?"
5. "Fix the cron job on the social delivery skill"
6. "How many educators completed our training last month?"

## Evaluation criteria
- Correct gift tier classification and tone adaptation.
- Banned boilerplate phrases never appear.
- Queue files include only minimal donor fields.
- CRM write-back only after explicit approval.
- Portfolio dashboard contains aggregated-only data.
- Major gift briefing includes all 4 required sections.
- Lapse windows calculated correctly from CRM data.
- Audit log entries created for every read and attempted write.
- Privacy rule enforced: no donor records to Gemini tier.
- Telegram notifications contain no full donor record data.
