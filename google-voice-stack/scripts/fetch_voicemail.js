const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const limit = Number(process.argv[2] || 10);

(async () => {
  const statePath = path.resolve(__dirname, '../.gv_storage_state.json');
  const outPath = path.resolve(__dirname, '../output_voicemail.json');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState: statePath });
  const page = await context.newPage();
  await page.goto('https://voice.google.com/u/0/voicemail', { waitUntil: 'domcontentloaded' });

  const data = await page.evaluate((lim) => {
    const candidates = Array.from(document.querySelectorAll('a, div[role="row"], li, article'));
    return candidates
      .map(el => (el.textContent || '').trim().replace(/\s+/g, ' '))
      .filter(t => t.length > 20)
      .slice(0, lim)
      .map(text => ({ text: text.slice(0, 280) }));
  }, limit);

  fs.writeFileSync(outPath, JSON.stringify({ fetchedAt: new Date().toISOString(), voicemail: data }, null, 2));
  console.log(JSON.stringify({ ok: true, count: data.length, outPath }, null, 2));
  await browser.close();
})();
