const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const limit = Number(process.argv[2] || 10);

(async () => {
  const statePath = path.resolve(__dirname, '../.gv_storage_state.json');
  const outPath = path.resolve(__dirname, '../output_threads.json');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState: statePath });
  const page = await context.newPage();
  await page.goto('https://voice.google.com/u/0/messages', { waitUntil: 'domcontentloaded' });

  const data = await page.evaluate((lim) => {
    const rows = Array.from(document.querySelectorAll('a, div[role="row"], li')).filter(el =>
      /message|thread|conversation/i.test((el.getAttribute('aria-label') || '') + ' ' + (el.textContent || ''))
    );
    return rows.slice(0, lim).map(el => ({
      text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 220)
    }));
  }, limit);

  fs.writeFileSync(outPath, JSON.stringify({ fetchedAt: new Date().toISOString(), threads: data }, null, 2));
  console.log(JSON.stringify({ ok: true, count: data.length, outPath }, null, 2));
  await browser.close();
})();
