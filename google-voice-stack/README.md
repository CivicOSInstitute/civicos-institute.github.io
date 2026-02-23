# Google Voice Stack (Browser Automation)

This stack provides practical browser automation for Google Voice on macOS.

## Features
- Save Google Voice login session
- Send text message
- Fetch recent thread snippets
- Fetch voicemail list/transcript snippets

## Setup
```bash
cd ~/.openclaw/workspace/google-voice-stack
npm install
npm run setup
```

## 1) Login once
```bash
npm run login
```
- Browser opens at voice.google.com
- Log in + complete any prompts
- Press Enter in terminal
- Session is saved to `.gv_storage_state.json`

## 2) Send text
```bash
npm run send -- "+15551234567" "Test message from Burt"
```

## 3) Read recent threads
```bash
npm run inbox -- 10
cat output_threads.json
```

## 4) Read voicemail snippets
```bash
npm run voicemail -- 10
cat output_voicemail.json
```

## Notes
- This is UI automation, not official API integration.
- If Google re-prompts login/MFA, rerun `npm run login`.
- Keep `.gv_storage_state.json` local and private.
