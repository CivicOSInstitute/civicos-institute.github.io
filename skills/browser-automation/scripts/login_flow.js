#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/*
Usage:
  node scripts/login_flow.js config/login.example.json
*/

async function tryFill(page, selectors, value) {
  for (const s of selectors) {
    const el = page.locator(s).first();
    if (await el.count()) {
      try { await el.fill(value); return true; } catch {}
    }
  }
  return false;
}

(async () => {
  const cfgPath = process.argv[2];
  if (!cfgPath) throw new Error('Pass config JSON path');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));

  const outDir = cfg.outDir || path.resolve(process.cwd(), 'artifacts');
  fs.mkdirSync(outDir, { recursive: true });
  const storageStatePath = cfg.storageStatePath || path.join(outDir, 'storage-state.json');

  const browser = await chromium.launch({ headless: cfg.headless ?? false, slowMo: cfg.slowMo ?? 50 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(cfg.loginUrl, { waitUntil: 'domcontentloaded', timeout: cfg.timeoutMs ?? 60000 });

    await tryFill(page, cfg.selectors.username, cfg.username);
    await tryFill(page, cfg.selectors.password, cfg.password);

    for (const clickSel of cfg.selectors.submit) {
      const btn = page.locator(clickSel).first();
      if (await btn.count()) {
        await btn.click();
        break;
      }
    }

    // handle OAuth / redirects by waiting on final URL pattern if provided
    if (cfg.successUrlContains) {
      await page.waitForURL(new RegExp(cfg.successUrlContains), { timeout: cfg.timeoutMs ?? 60000 });
    } else {
      await page.waitForLoadState('networkidle', { timeout: cfg.timeoutMs ?? 60000 });
    }

    // cookie/session persistence
    await context.storageState({ path: storageStatePath });

    const shot = path.join(outDir, `login-success-${Date.now()}.png`);
    await page.screenshot({ path: shot, fullPage: true });
    console.log(JSON.stringify({ ok: true, storageStatePath, screenshot: shot, url: page.url() }, null, 2));
  } catch (e) {
    const failShot = path.join(outDir, `login-fail-${Date.now()}.png`);
    await page.screenshot({ path: failShot, fullPage: true }).catch(() => {});
    console.error(JSON.stringify({ ok: false, error: String(e), screenshot: failShot, url: page.url() }, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
