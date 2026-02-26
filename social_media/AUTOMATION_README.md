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

## Reddit automation (compliant near-autonomous)

Added:
- Runner: `scripts/reddit_autopilot.py`
- Config template: `social_media/reddit_automation_config.example.json`
- Queue sample: `social_media/queue/reddit_queue.sample.json`
- Pause state: `social_media/queue/reddit_state.json`
- Logs: `social_media/analytics/reddit_autopilot_*.json`

Behavior:
- Uses official Reddit OAuth + API endpoints.
- Supports queued `post` and `comment` actions.
- Enforces spacing (`min_seconds_between_actions`) to reduce anti-spam triggers.
- Automatically pauses on auth/challenge-style errors (no CAPTCHA bypass attempts).

Setup:
1. Create a Reddit app and collect `client_id` + `client_secret`.
2. Obtain a `refresh_token` (one-time human auth).
3. Copy template to active config:
   ```bash
   cp social_media/reddit_automation_config.example.json social_media/reddit_automation_config.json
   ```
4. Create active queue:
   ```bash
   cp social_media/queue/reddit_queue.sample.json social_media/queue/reddit_queue.json
   ```

Run:
```bash
python3 scripts/reddit_autopilot.py --dry-run
python3 scripts/reddit_autopilot.py
```

If paused:
- Check `social_media/queue/reddit_state.json`
- Resolve required manual auth/verification on Reddit
- Re-run the script (it auto-clears pause after successful run)

## Next hardening (tomorrow)

- Add scheduler hooks (hourly/daily)
- Add retry/fallback + delivery log
- Add Playwright posting flow for Facebook composer with persistent login profile
- Add analytics UTM auto-tagging in generated links
