const { chromium } = require('playwright');
const path = require('path');

const to = process.argv[2];
const message = process.argv.slice(3).join(' ');
if (!to || !message) {
  console.error('Usage: npm run send -- "+15551234567" "message text"');
  process.exit(1);
}

(async () => {
  const statePath = path.resolve(__dirname, '../.gv_storage_state.json');
  const browser = await chromium.launch({ headless: false, slowMo: 60 });
  const context = await browser.newContext({ storageState: statePath });
  const page = await context.newPage();
  await page.goto('https://voice.google.com/u/0/messages', { waitUntil: 'domcontentloaded' });

  await page.getByRole('button', { name: /send a message|new message|message/i }).first().click();
  await page.locator('input[aria-label*="To"], input[placeholder*="name or number"], input[type="text"]').first().fill(to);
  await page.keyboard.press('Enter');

  const box = page.locator('textarea, div[contenteditable="true"]').first();
  await box.click();
  await box.fill(message).catch(async ()=> { await page.keyboard.type(message); });

  await page.getByRole('button', { name: /^send$/i }).first().click();
  console.log('SENT', to, message.slice(0, 60));

  await context.storageState({ path: statePath });
  await browser.close();
})();
