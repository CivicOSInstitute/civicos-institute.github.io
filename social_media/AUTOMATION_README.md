# Social Automation (No-Budget) — Current Setup

## What is automated now

1. **Daily post pack generation** (X/Facebook/Discord copy + links)
2. **One-click X draft opening** via `x.com/intent/tweet`
3. **Website/news-aware copy** pulls top headline from `website-news/news.json`
4. **Discord autopost attempt** via webhook command from keychain

## Files

- Config: `social_media/automation_config.json`
- Generator: `scripts/social_autopilot.py`
- Queue output: `social_media/queue/YYYY-MM-DD.json` and `.md`
- Open drafts helper: `scripts/open_social_drafts.py`

## Run now

```bash
python3 scripts/social_autopilot.py
python3 scripts/open_social_drafts.py
```

## Notes

- X has no reliable official RSS/post API path here; intent URLs are the most stable no-budget path.
- Facebook direct autopost requires API app permissions or stable browser automation session.
- Discord webhook posting requires keychain secret `discord-civicos-webhook` to be valid.

## Next hardening (tomorrow)

- Add scheduler hooks (hourly/daily)
- Add retry/fallback + delivery log
- Add Playwright posting flow for Facebook composer with persistent login profile
- Add analytics UTM auto-tagging in generated links
