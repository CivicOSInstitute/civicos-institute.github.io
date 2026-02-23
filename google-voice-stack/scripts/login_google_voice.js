const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('https://voice.google.com', { waitUntil: 'domcontentloaded' });
  console.log('\nLog into Google Voice in the browser window.');
  console.log('When inbox is visible, press ENTER here.\n');

  process.stdin.resume();
  await new Promise(resolve => process.stdin.once('data', resolve));

  const statePath = path.resolve(__dirname, '../.gv_storage_state.json');
  await context.storageState({ path: statePath });
  console.log(`Saved session: ${statePath}`);
  await browser.close();
})();
