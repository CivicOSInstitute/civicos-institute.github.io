---
name: browser-automation
description: Control a browser with Playwright/Puppeteer to log into websites, fill forms, take screenshots, and scrape dynamic content when API calls are not available or insufficient.
---

# browser-automation

## Use this skill for
- Interactive website login flows
- Form filling and submissions
- Dynamic page scraping (JS-rendered content)
- Screenshot capture for verification/evidence
- Repetitive browser workflows

## Workflow

1. Confirm target site and objective (login/scrape/form/screenshot).
2. Use Playwright first (preferred), Puppeteer fallback if required.
3. Run headed mode for authentication/setup; headless for repeat tasks.
4. Save session state (`storageState`) to avoid repeated login.
5. Return structured output (JSON/text + screenshot paths).

## Input contract
- Required:
  - target URL(s)
  - task intent (login, scrape, fill, screenshot)
- Optional:
  - selectors to target
  - output path
  - max pages / limits

## Output contract
- Action summary
- Result payload (parsed values)
- Artifacts (screenshots/files)
- Errors with exact failing step and retry suggestion

## Standard commands

```bash
# install
npm install playwright
npx playwright install chromium

# run script
node scripts/run.js
```

## Edge cases
- MFA/challenge pages: pause and request user input.
- Anti-bot or captchas: switch to headed + manual assist.
- Selector drift: use resilient role/text selectors and fallback chains.
- Session expiry: re-authenticate and refresh storage state.
