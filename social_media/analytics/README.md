# CivicOS Social Analytics (Zero-Budget Stack)

This stack is designed for **$0 software cost** and quick daily operation.

## What it tracks
- Posting output by platform (X, Facebook, YouTube)
- Reach/impressions/views
- Engagement (likes, comments, shares, saves)
- Growth (followers/subscribers delta)
- Link clicks (if available)
- Outreach effectiveness (DMs started, meaningful conversations)

## Files
- `metrics_daily.csv` → daily manual input (2–5 minutes/day)
- `scripts/social_analytics_report.py` → generates weekly scorecard markdown
- `generated/social_analytics_weekly.md` → report output

## Daily workflow (2–5 min)
1. Open platform analytics (X, Facebook, YouTube Studio)
2. Enter one row per platform in `metrics_daily.csv`
3. Run:
   ```bash
   python3 scripts/social_analytics_report.py
   ```
4. Review `generated/social_analytics_weekly.md`

## Core effectiveness KPIs
- Engagement Rate = engagements / reach
- Conversation Rate = meaningful_conversations / posts
- Follower Conversion = follower_delta / reach
- Outreach Yield = meaningful_conversations / outreach_actions

## Recommended targets (first 30 days)
- Engagement Rate: >2.0% (X/FB), >3.5% for Shorts
- Conversation Rate: >=0.5 meaningful conversations/post
- Outreach Yield: >=10%
- Weekly follower growth: positive and accelerating

## Why this works on zero budget
- Uses only native platform analytics + local files/scripts
- No paid social tools required
- Automatable later by adding API or scraper ingestors
