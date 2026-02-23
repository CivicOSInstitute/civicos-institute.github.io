#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const EMAIL = 'Ncerbone@civicos-institute.org';
const PASSWORD = 'OUT)00r121275';

const EPUB = '/Users/AI-OPS/Desktop/The_Open_Source_Student/launch-output/20260222-211926/core/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN-telegram.epub';
const COVER = '/Users/AI-OPS/Desktop/The_Open_Source_Student/Internal Documents/Marketing/exports/CivicOS_Founders_Hardcover_v2_Cream_6x9.jpg';
const outDir = '/Users/AI-OPS/.openclaw/workspace/skills/browser-automation/artifacts';
fs.mkdirSync(outDir, { recursive: true });

async function shot(page, name){
  const p = path.join(outDir, `${Date.now()}-${name}.png`);
  await page.screenshot({path:p, fullPage:true}).catch(()=>{});
  console.log(`[kdp] screenshot ${p}`);
}

async function clickText(page, patterns){
  for (const pat of patterns) {
    const roleBtn = page.getByRole('button', { name: new RegExp(pat, 'i') }).first();
    if (await roleBtn.count()) { await roleBtn.click().catch(()=>{}); await page.waitForTimeout(800); return true; }
    const txt = page.getByText(new RegExp(pat, 'i')).first();
    if (await txt.count()) { await txt.click().catch(()=>{}); await page.waitForTimeout(800); return true; }
  }
  return false;
}

(async()=>{
  const browser = await chromium.launch({ headless:false, slowMo:70 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('https://kdp.amazon.com/en_US/bookshelf', { waitUntil:'domcontentloaded', timeout:120000 });
    await page.waitForTimeout(2000);

    // Login flow if Amazon Sign-In appears
    const emailInput = page.locator('input[type="email"], input[name="email"], #ap_email').first();
    if (await emailInput.count()) {
      await emailInput.fill(EMAIL);
      await clickText(page, ['Continue', 'Next']);
      await page.waitForTimeout(1000);
    }

    const passInput = page.locator('input[type="password"], input[name="password"], #ap_password').first();
    if (await passInput.count()) {
      await passInput.fill(PASSWORD);
      await clickText(page, ['Sign-In', 'Sign in', 'Sign in securely']);
      await page.waitForTimeout(2500);
    }

    // If MFA challenge appears, pause for manual code.
    if ((await page.getByText(/Enter verification code|MFA|Two-Step Verification|OTP|Authenticator/i).count()) > 0) {
      console.log('[kdp] MFA detected. Please complete MFA in the opened browser now. Waiting up to 5 minutes...');
      await page.waitForTimeout(5 * 60 * 1000);
    }

    await page.goto('https://kdp.amazon.com/en_US/bookshelf', { waitUntil:'domcontentloaded', timeout:120000 });
    await page.waitForTimeout(2500);
    await shot(page, 'bookshelf-after-login');

    await clickText(page, ['\\+ Create', 'Create', 'Create a Kindle eBook', 'Kindle eBook']);
    await page.waitForTimeout(3000);
    await shot(page, 'entry');

    const fillByLabel = async (re, value) => {
      const loc = page.getByLabel(re).first();
      if (await loc.count()) {
        await loc.fill('');
        await loc.fill(value).catch(()=>{});
        return true;
      }
      return false;
    };

    await fillByLabel(/Book title/i, 'The Open Source Student');
    await fillByLabel(/Subtitle/i, 'Practical AI & Open-Source Skills for Real-World Execution');
    await fillByLabel(/Author/i, 'Nick Cerbone');

    const desc = page.getByLabel(/Description/i).first();
    if (await desc.count()) {
      await desc.fill('The Open Source Student is a practical guide for learners, educators, and builders who want to apply AI and open-source tools in real workflows.\n\nAll proceeds from this title go directly to funding the CivicOS Institute.').catch(()=>{});
    }

    const keywords = ['open source','ai literacy','digital skills','student toolkit','terminal skills','workflow automation','civicos institute'];
    for (let i=1;i<=7;i++) await fillByLabel(new RegExp(`Keyword\\s*${i}`,'i'), keywords[i-1]);

    await shot(page, 'details');
    await clickText(page, ['Save and Continue','Continue']);
    await page.waitForTimeout(4500);
    await shot(page, 'content');

    const fileInputs = page.locator('input[type="file"]');
    const count = await fileInputs.count();
    if (count > 0) {
      await fileInputs.nth(0).setInputFiles(EPUB).catch(()=>{});
      if (count > 1) await fileInputs.nth(1).setInputFiles(COVER).catch(()=>{});
    }

    await clickText(page, ['Save and Continue','Continue']);
    await page.waitForTimeout(5000);

    await fillByLabel(/List Price|USD|US\$/i, '179.00');
    await shot(page, 'pricing-before-publish');

    console.log('[kdp] Reached pricing/publish stage; stopped before publish.');
    await browser.close();
  } catch (e) {
    console.error('[kdp] ERROR', String(e));
    await shot(page, 'error');
    await browser.close();
    process.exit(1);
  }
})();
