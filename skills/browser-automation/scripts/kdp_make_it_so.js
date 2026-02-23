#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const EPUB = '/Users/AI-OPS/Desktop/The_Open_Source_Student/launch-output/20260222-211926/core/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN.epub';
const COVER = '/Users/AI-OPS/Desktop/The_Open_Source_Student/Internal Documents/Marketing/exports/CivicOS_Founders_Hardcover_v2_Cream_6x9.jpg';
const outDir = '/Users/AI-OPS/.openclaw/workspace/skills/browser-automation/artifacts';
fs.mkdirSync(outDir, { recursive: true });

const meta = {
  title: 'The Open Source Student',
  subtitle: 'Practical AI & Open-Source Skills for Real-World Execution',
  author: 'Nick Cerbone',
  description: `The Open Source Student is a practical guide for learners, educators, and builders who want to apply AI and open-source tools in real workflows.\n\nThis book is designed to help readers build real-world digital capability with implementation-first methods.\n\nAll proceeds from this title go directly to funding the CivicOS Institute.`
};

async function shot(page, name){
  const p = path.join(outDir, `${Date.now()}-${name}.png`);
  await page.screenshot({path:p, fullPage:true}).catch(()=>{});
  console.log(`[kdp] screenshot ${p}`);
}

(async()=>{
  const browser = await chromium.launch({ headless:false, slowMo:80 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('https://kdp.amazon.com/en_US/bookshelf', {waitUntil:'domcontentloaded', timeout:120000});
    console.log('[kdp] Please complete login/MFA if prompted in opened browser.');
    await page.waitForTimeout(7000);

    // Enter Kindle eBook create flow
    let clicked = false;
    for (const txt of ['\\+ Create', 'Create', 'Create a Kindle eBook', 'Kindle eBook']) {
      const el = page.getByRole('button', { name: new RegExp(txt, 'i') }).first();
      if (await el.count()) { await el.click().catch(()=>{}); clicked = true; await page.waitForTimeout(1000); }
    }
    if (!clicked) {
      const any = page.getByText(/Create a Kindle eBook|Kindle eBook|Create/i).first();
      if (await any.count()) await any.click().catch(()=>{});
    }

    await page.waitForTimeout(3000);
    await shot(page, 'kdp-entry');

    // Fill details page best effort
    const fillByLabel = async (re, value) => {
      const loc = page.getByLabel(re).first();
      if (await loc.count()) {
        await loc.fill('');
        await loc.fill(value).catch(()=>{});
        return true;
      }
      return false;
    };

    await fillByLabel(/Book title/i, meta.title);
    await fillByLabel(/Subtitle/i, meta.subtitle);
    await fillByLabel(/Author/i, meta.author);

    const desc = page.getByLabel(/Description/i).first();
    if (await desc.count()) {
      await desc.fill('').catch(()=>{});
      await desc.fill(meta.description).catch(()=>{});
    }

    const keywords = [
      'open source', 'ai literacy', 'digital skills', 'student toolkit',
      'terminal skills', 'workflow automation', 'civicos institute'
    ];
    for (let i=1;i<=7;i++) {
      await fillByLabel(new RegExp(`Keyword\\s*${i}`, 'i'), keywords[i-1]);
    }

    await shot(page, 'kdp-details-filled');

    // Save & continue to content
    for (const txt of ['Save and Continue', 'Save and continue', 'Continue']) {
      const btn = page.getByRole('button', {name: new RegExp(txt, 'i')}).first();
      if (await btn.count()) { await btn.click().catch(()=>{}); await page.waitForTimeout(4000); break; }
    }

    await shot(page, 'kdp-content-page');

    // Upload files (best effort on first two file inputs)
    const fileInputs = page.locator('input[type="file"]');
    const count = await fileInputs.count();
    if (count > 0) {
      await fileInputs.nth(0).setInputFiles(EPUB).catch(()=>{});
      if (count > 1) await fileInputs.nth(1).setInputFiles(COVER).catch(()=>{});
    }

    // Also try chooser buttons if available
    const manuscriptBtn = page.getByRole('button', {name:/Upload eBook manuscript|Upload manuscript|Upload/i}).first();
    if (await manuscriptBtn.count()) {
      const [chooser] = await Promise.all([
        page.waitForEvent('filechooser').catch(()=>null),
        manuscriptBtn.click().catch(()=>{})
      ]);
      if (chooser) await chooser.setFiles(EPUB).catch(()=>{});
    }

    const coverBtn = page.getByRole('button', {name:/Upload your cover|Upload cover|Upload a cover/i}).first();
    if (await coverBtn.count()) {
      const [chooser2] = await Promise.all([
        page.waitForEvent('filechooser').catch(()=>null),
        coverBtn.click().catch(()=>{})
      ]);
      if (chooser2) await chooser2.setFiles(COVER).catch(()=>{});
    }

    await page.waitForTimeout(5000);
    await shot(page, 'kdp-content-uploaded');

    // Move toward pricing, but do NOT publish.
    for (const txt of ['Save and Continue', 'Save and continue', 'Continue']) {
      const btn = page.getByRole('button', {name: new RegExp(txt, 'i')}).first();
      if (await btn.count()) { await btn.click().catch(()=>{}); await page.waitForTimeout(5000); break; }
    }

    await fillByLabel(/List Price|USD|US\$/i, '19.00');
    await shot(page, 'kdp-pricing-before-publish');

    console.log('[kdp] Reached pricing/publish stage (best effort). Stopping before final Publish click.');
    console.log(`[kdp] EPUB: ${EPUB}`);
    console.log(`[kdp] COVER: ${COVER}`);

    await browser.close();
  } catch (e) {
    console.error('[kdp] ERROR', String(e));
    await shot(page, 'kdp-error');
    await browser.close();
    process.exit(1);
  }
})();
