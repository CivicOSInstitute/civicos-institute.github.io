#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const outDir = '/Users/AI-OPS/.openclaw/workspace/skills/browser-automation/artifacts';
  fs.mkdirSync(outDir, { recursive: true });

  const meta = JSON.parse(fs.readFileSync('/Users/AI-OPS/.openclaw/workspace/the_open_source_student_distribution/platforms/amazon-kdp/kdp_metadata.json', 'utf8'));

  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const context = await browser.newContext();
  const page = await context.newPage();

  const log = (m) => console.log(`[kdp] ${m}`);

  try {
    log('Opening KDP Bookshelf...');
    await page.goto('https://kdp.amazon.com/en_US/bookshelf', { waitUntil: 'domcontentloaded', timeout: 120000 });

    log('Waiting for login/bookshelf access (complete sign-in/MFA in the opened browser if prompted)...');
    await page.waitForURL(/kdp\.amazon\.com\/.+/, { timeout: 15 * 60 * 1000 });
    await page.waitForTimeout(2000);

    // If still on public page/sign-in, wait for bookshelf markers.
    const shelfMarker = page.getByText(/Bookshelf|Create|Kindle eBook/i).first();
    await shelfMarker.waitFor({ timeout: 5 * 60 * 1000 }).catch(() => {});

    log('Trying to open existing draft for "The Open Source Student"...');
    const titleLocator = page.getByText(/The Open Source Student/i).first();
    if (await titleLocator.count()) {
      await titleLocator.click({ timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(1500);
      const continueBtn = page.getByRole('button', { name: /Continue setup|Continue/i }).first();
      if (await continueBtn.count()) await continueBtn.click({ timeout: 15000 }).catch(() => {});
    } else {
      log('Draft not found quickly. Trying to start Kindle eBook flow...');
      const createBtn = page.getByRole('button', { name: /Create|\+ Create/i }).first();
      if (await createBtn.count()) await createBtn.click({ timeout: 15000 }).catch(() => {});
      const kindleEbook = page.getByText(/Kindle eBook/i).first();
      if (await kindleEbook.count()) await kindleEbook.click({ timeout: 15000 }).catch(() => {});
    }

    await page.waitForTimeout(2500);

    // Best-effort metadata fill on details page.
    const fillIfEmpty = async (labelRe, value) => {
      const input = page.getByLabel(labelRe).first();
      if (await input.count()) {
        const existing = (await input.inputValue().catch(() => '')) || '';
        if (!existing.trim()) await input.fill(String(value));
      }
    };

    await fillIfEmpty(/Book title/i, meta.title);
    await fillIfEmpty(/Subtitle/i, meta.subtitle);
    await fillIfEmpty(/Author/i, meta.author);

    const desc = page.getByLabel(/Description/i).first();
    if (await desc.count()) {
      const existing = (await desc.inputValue().catch(() => '')) || '';
      if (!existing.trim()) await desc.fill(meta.description);
    }

    const shot = path.join(outDir, `kdp-progress-${Date.now()}.png`);
    await page.screenshot({ path: shot, fullPage: true });

    log(`Progress screenshot: ${shot}`);
    log(`Current URL: ${page.url()}`);
    log('Left browser open for final manual checks/publish. Close it when done.');

    // Keep session open for operator.
    await new Promise(() => {});
  } catch (e) {
    const fail = path.join(outDir, `kdp-fail-${Date.now()}.png`);
    await page.screenshot({ path: fail, fullPage: true }).catch(() => {});
    console.error(`[kdp] ERROR: ${String(e)}`);
    console.error(`[kdp] Failure screenshot: ${fail}`);
    process.exit(1);
  }
})();
