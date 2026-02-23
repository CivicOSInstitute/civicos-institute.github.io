#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/*
Generic task runner for navigate/click/fill/scrape/screenshot.
Usage:
  node scripts/run_task.js config/task.example.json

Added:
- persistent context support (userDataDir + channel)
- preflight steps: ensureUrlContains / ensureSelector / ensureLoggedIn
- storageState save at end
*/

async function runStep(page, step, out) {
  if (step.type === 'goto') {
    await page.goto(step.url, { waitUntil: step.waitUntil || 'domcontentloaded', timeout: step.timeoutMs || 60000 });
    return;
  }
  if (step.type === 'ensureUrlContains') {
    const u = page.url();
    if (!u.includes(step.value)) throw new Error(`Preflight failed: URL missing '${step.value}' :: ${u}`);
    return;
  }
  if (step.type === 'ensureSelector') {
    const el = page.locator(step.selector).first();
    await el.waitFor({ timeout: step.timeoutMs || 15000 });
    return;
  }
  if (step.type === 'ensureLoggedIn') {
    // If loggedOutSelector exists, fail if visible.
    const lo = step.loggedOutSelector ? page.locator(step.loggedOutSelector).first() : null;
    if (lo && await lo.count()) {
      throw new Error(`Preflight failed: appears logged out (selector: ${step.loggedOutSelector})`);
    }
    // If loggedInSelector exists, require it.
    if (step.loggedInSelector) {
      await page.locator(step.loggedInSelector).first().waitFor({ timeout: step.timeoutMs || 15000 });
    }
    return;
  }
  if (step.type === 'click') {
    await page.locator(step.selector).first().click({ timeout: step.timeoutMs || 30000 });
    return;
  }
  if (step.type === 'fill') {
    await page.locator(step.selector).first().fill(step.value, { timeout: step.timeoutMs || 30000 });
    return;
  }
  if (step.type === 'wait') {
    if (step.selector) await page.locator(step.selector).first().waitFor({ timeout: step.timeoutMs || 30000 });
    else await page.waitForTimeout(step.ms || 1000);
    return;
  }
  if (step.type === 'screenshot') {
    const p = path.join(out, step.name || `shot-${Date.now()}.png`);
    await page.screenshot({ path: p, fullPage: step.fullPage ?? true });
    return { screenshot: p };
  }
  if (step.type === 'scrapeText') {
    const text = await page.locator(step.selector).first().innerText({ timeout: step.timeoutMs || 30000 });
    return { key: step.key || 'text', value: text.trim() };
  }
  throw new Error(`Unsupported step type: ${step.type}`);
}

(async () => {
  const cfgPath = process.argv[2];
  if (!cfgPath) throw new Error('Pass config JSON path');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));

  const outDir = cfg.outDir || path.resolve(process.cwd(), 'artifacts');
  fs.mkdirSync(outDir, { recursive: true });

  let browser = null;
  let context = null;
  if (cfg.userDataDir) {
    context = await chromium.launchPersistentContext(cfg.userDataDir, {
      headless: cfg.headless ?? true,
      slowMo: cfg.slowMo ?? 0,
      channel: cfg.channel || undefined
    });
  } else {
    browser = await chromium.launch({ headless: cfg.headless ?? true, slowMo: cfg.slowMo ?? 0, channel: cfg.channel || undefined });
    context = await browser.newContext(cfg.storageStatePath ? { storageState: cfg.storageStatePath } : {});
  }

  const page = context.pages()[0] || await context.newPage();
  const result = { ok: true, data: {}, screenshots: [], finalUrl: '' };

  try {
    for (const step of cfg.steps || []) {
      const r = await runStep(page, step, outDir);
      if (r?.screenshot) result.screenshots.push(r.screenshot);
      if (r?.key) result.data[r.key] = r.value;
    }
    result.finalUrl = page.url();

    if (cfg.saveStorageStatePath) {
      await context.storageState({ path: cfg.saveStorageStatePath });
      result.savedStorageStatePath = cfg.saveStorageStatePath;
    }

    console.log(JSON.stringify(result, null, 2));
  } catch (e) {
    const failShot = path.join(outDir, `task-fail-${Date.now()}.png`);
    await page.screenshot({ path: failShot, fullPage: true }).catch(() => {});
    console.error(JSON.stringify({ ok: false, error: String(e), screenshot: failShot, finalUrl: page.url() }, null, 2));
    process.exitCode = 1;
  } finally {
    await context.close();
    if (browser) await browser.close();
  }
})();
