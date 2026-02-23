#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const outDir = process.argv[2] || path.resolve(process.cwd(), 'artifacts');
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 45000 });
  const shot = path.join(outDir, `launch-check-${Date.now()}.png`);
  await page.screenshot({ path: shot, fullPage: true });

  console.log(JSON.stringify({ ok: true, screenshot: shot }, null, 2));
  await browser.close();
})();
