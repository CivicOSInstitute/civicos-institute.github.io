# Browser Automation Stack (CivicOS)

Local Playwright-based automation for browser tasks that API routes can't complete.

## Use case now
Lemon Squeezy product creation via UI (since API route is read-only for products).

## Setup
```bash
cd ~/.openclaw/workspace/browser-automation-stack
npm install
npm run setup
```

## 1) Capture login session
```bash
npm run login:ls
```
- Browser opens
- Log into Lemon Squeezy manually
- Press Enter in terminal to save session state

## 2) Create products automatically
```bash
npm run create:ls
```
Uses `config/lemonsqueezy_products.json`.

## Notes
- Runs headed (visible browser) to reduce anti-bot friction.
- Selector logic is resilient but UI changes may require selector updates.
- Session file: `.ls_storage_state.json` (sensitive). Keep local only.
