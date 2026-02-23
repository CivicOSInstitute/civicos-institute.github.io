#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const COMMON_SELECTORS_PATH = path.resolve(__dirname, '../config/selectors/common.json');
/*
Usage:
  node scripts/login_flow.js config/login.example.json

Added:
- persistent profile support via userDataDir/channel
- optional preflight check: if already authenticated, skip credential input
*/

function mergeSelectors(cfg) {
  let common = {};
  try {
    common = JSON.parse(fs.readFileSync(COMMON_SELECTORS_PATH, 'utf8'));
  } catch {}
  return {
    username: [...(cfg?.selectors?.username || []), ...((common.login || {}).username || [])],
    password: [...(cfg?.selectors?.password || []), ...((common.login || {}).password || [])],
    submit: [...(cfg?.selectors?.submit || []), ...((common.login || {}).submit || [])],
    mfaCode: [...(cfg?.selectors?.mfaCode || []), ...((common.mfa || {}).code_input || [])],
    mfaVerify: [...(cfg?.selectors?.mfaVerify || []), ...((common.mfa || {}).verify_button || [])],
    cookieAccept: [...(cfg?.selectors?.cookieAccept || []), ...((common.cookie_banners || {}).accept || [])],
  };
}

async function tryFill(page, selectors, value) {
  for (const s of selectors) {
    const el = page.locator(s).first();
    if (await el.count()) {
      try { await el.fill(value); return true; } catch {}
    }
  }
  return false;
}

async function tryClick(page, selectors) {
  for (const s of selectors) {
    const el = page.locator(s).first();
    if (await el.count()) {
      try { await el.click(); return true; } catch {}
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
  const selectors = mergeSelectors(cfg);

  let context;
  if (cfg.userDataDir) {
    context = await chromium.launchPersistentContext(cfg.userDataDir, {
      headless: cfg.headless ?? false,
      slowMo: cfg.slowMo ?? 50,
      channel: cfg.channel || undefined
    });
  } else {
    const browser = await chromium.launch({ headless: cfg.headless ?? false, slowMo: cfg.slowMo ?? 50, channel: cfg.channel || undefined });
    context = await browser.newContext();
  }

  const page = context.pages()[0] || await context.newPage();

  try {
    await page.goto(cfg.loginUrl, { waitUntil: 'domcontentloaded', timeout: cfg.timeoutMs ?? 60000 });

    // Optional preflight: already authenticated?
    if (cfg.alreadyLoggedInSelector) {
      const ok = page.locator(cfg.alreadyLoggedInSelector).first();
      if (await ok.count()) {
        await context.storageState({ path: storageStatePath });
        const shot = path.join(outDir, `login-already-auth-${Date.now()}.png`);
        await page.screenshot({ path: shot, fullPage: true }).catch(() => {});
        console.log(JSON.stringify({ ok: true, already_logged_in: true, storageStatePath, screenshot: shot, url: page.url() }, null, 2));
        await context.close();
        return;
      }
    }

    await tryClick(page, selectors.cookieAccept);
    await tryFill(page, selectors.username, cfg.username);
    await tryFill(page, selectors.password, cfg.password);
    await tryClick(page, selectors.submit);

    if (cfg.pauseForMfa) {
      const mfaShot = path.join(outDir, `mfa-prompt-${Date.now()}.png`);
      await page.screenshot({ path: mfaShot, fullPage: true }).catch(() => {});
      console.log(JSON.stringify({ ok: true, mfa_required: true, screenshot: mfaShot, message: 'Complete MFA in browser, then press ENTER in terminal to continue.' }, null, 2));
      process.stdin.resume();
      await new Promise(resolve => process.stdin.once('data', resolve));

      if (cfg.mfaCode) {
        await tryFill(page, selectors.mfaCode, cfg.mfaCode);
        await tryClick(page, selectors.mfaVerify);
      }
    }

    if (cfg.successUrlContains) {
      await page.waitForURL(new RegExp(cfg.successUrlContains), { timeout: cfg.timeoutMs ?? 60000 });
    } else {
      await page.waitForLoadState('networkidle', { timeout: cfg.timeoutMs ?? 60000 });
    }

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
    await context.close();
  }
})();
