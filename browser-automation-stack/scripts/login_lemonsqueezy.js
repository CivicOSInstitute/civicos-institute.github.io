const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('https://app.lemonsqueezy.com/', { waitUntil: 'domcontentloaded' });
  console.log('\nLog in manually in the opened browser.');
  console.log('When you can see your dashboard, press ENTER in this terminal.\n');

  process.stdin.resume();
  await new Promise(resolve => process.stdin.once('data', resolve));

  const statePath = path.resolve(__dirname, '../.ls_storage_state.json');
  await context.storageState({ path: statePath });
  console.log(`Saved login session to ${statePath}`);

  await browser.close();
})();
