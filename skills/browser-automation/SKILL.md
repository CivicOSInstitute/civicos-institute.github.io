---
name: browser-automation
description: Control a headless browser using Playwright to navigate URLs, authenticate to websites, click through multi-step flows, fill/submit forms, take screenshots, and scrape dynamic content when curl/API access is insufficient.
---

# browser-automation

Use this skill when an agent must interact with real websites like a human.

## Capabilities
- Navigate and wait for rendered JS content
- Login flows with credential selectors
- Cookie/session persistence via `storageState`
- OAuth redirect handling with success URL checks
- Multi-step click/fill/wait workflows
- Screenshot capture to local artifacts directory
- Dynamic text scraping from rendered elements
- Robust error handling (timeouts, missing elements, blocked flows)

## Required scripts
- `scripts/launch_browser.js` — browser sanity launch + screenshot
- `scripts/login_flow.js` — reusable login/session capture helper
- `scripts/run_task.js` — generic step runner (`goto/click/fill/wait/screenshot/scrapeText`)

## Quick start

```bash
cd skills/browser-automation
npm install playwright
npx playwright install chromium
```

### 1) Validate browser stack
```bash
node scripts/launch_browser.js ./artifacts
```

### 2) Run login/session capture
Edit `config/login.example.json` and run:
```bash
node scripts/login_flow.js config/login.example.json
```

### 3) Run a task flow
Edit `config/task.example.json` and run:
```bash
node scripts/run_task.js config/task.example.json
```

## Input contract
- Required:
  - Target URL(s)
  - Task intent (login / form / scrape / screenshot)
- Optional:
  - Selector list and fallback selectors
  - `headless` mode toggle
  - `storageStatePath`
  - output directory

## Output contract
Return structured JSON including:
- `ok`
- `data` (scraped values)
- `screenshots` (local file paths)
- `finalUrl`
- `error` with failing step details (if failed)

## Error handling standards
- On timeout: capture failure screenshot and return actionable selector/url details.
- On missing element: include selector attempted and step type.
- On OAuth/cookie expiry: re-run login flow and refresh storage state.
- On captcha/MFA: pause automation and request human intervention.

## Edge cases
- Dynamic DOM updates: prefer role/text selectors and explicit waits.
- Redirect chains: use `waitForURL` with expected pattern.
- Session loss: re-create `storageState` from login flow.
- Anti-bot challenge: switch to headed mode + manual assist.
