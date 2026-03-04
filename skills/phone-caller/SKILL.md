---
name: phone-caller
description: Place outbound phone calls using a configurable telephony provider (Twilio first) with explicit user approval, call logging, and dry-run support.
---

# phone-caller

Use this skill when the user asks to place a real phone call from the agent.

## Safety rules (mandatory)

1. Require explicit approval in the current thread before any live dial.
2. Repeat back destination number and call purpose before dialing.
3. Default to `--dry-run` unless user explicitly confirms live call.
4. Never place emergency calls (911/112/etc.) through this skill.
5. Log each attempt to `logs/phone-calls.jsonl` with timestamp, target, mode, and status.

## Input contract

Required:
- `to_number` (E.164 format, e.g. `+15615551234`)
- `message` (text to speak during call, or brief call purpose)

Optional:
- `from_number` (E.164; defaults to `TWILIO_FROM_NUMBER`)
- `voice` (default: `alice`)
- `dry_run` (default: true)

## Execution flow

1. Validate E.164 number format.
2. Validate telephony env vars exist:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER` (unless provided)
3. If `dry_run=true`, return payload preview and do not dial.
4. If `dry_run=false`, execute `scripts/twilio_call.py`.
5. Return concise result with `status`, `provider`, `to_number`, `call_sid` (if live), and `timestamp`.

## Live conversation mode (beta)

This skill now includes `scripts/live_voice_assistant.py` for turn-based live calls:

- Twilio receives call webhook at `/voice`
- Captures user speech with `<Gather input="speech">`
- Responds with natural TTS voice and loops

Run locally:

```bash
# Terminal 1: start voice webhook server
./.venv/bin/python scripts/live_voice_assistant.py

# Terminal 2: expose public URL for Twilio webhook
# (example with ngrok)
ngrok http 8787
```

Set Twilio phone number Voice webhook to:

- `https://<your-ngrok-domain>/voice` (HTTP POST)

Recommended voice:
- `TWILIO_TTS_VOICE=Polly.Joanna-Neural`

## Command examples

```bash
# Dry run preview
python3 scripts/twilio_call.py \
  --to "+15615551234" \
  --message "Hi Nick, this is Burt testing outbound calling." \
  --dry-run

# Live call (only after explicit user approval)
python3 scripts/twilio_call.py \
  --to "+15615551234" \
  --message "Hi Nick, this is Burt with your requested call." \
  --live
```

## Edge cases

- Invalid phone format -> fail with example of valid E.164.
- Missing env vars -> fail with exact missing keys.
- Provider API failure -> return error details + retry guidance.
- User asks to call without explicit approval -> refuse and request confirmation.
