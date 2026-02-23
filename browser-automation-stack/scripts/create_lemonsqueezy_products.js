const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const cfg = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../config/lemonsqueezy_products.json'), 'utf8'));
const statePath = path.resolve(__dirname, '../.ls_storage_state.json');

async function fillIfPresent(page, selectors, value) {
  for (const s of selectors) {
    const el = page.locator(s).first();
    if (await el.count()) {
      try { await el.fill(value); return true; } catch {}
    }
  }
  return false;
}

(async () => {
  if (!fs.existsSync(statePath)) {
    throw new Error('Missing .ls_storage_state.json. Run npm run login:ls first.');
  }

  const browser = await chromium.launch({ headless: false, slowMo: 70 });
  const context = await browser.newContext({ storageState: statePath });
  const page = await context.newPage();

  await page.goto('https://app.lemonsqueezy.com/products', { waitUntil: 'domcontentloaded' });

  for (const product of cfg.products) {
    console.log(`Creating: ${product.name}`);

    await page.getByRole('button', { name: /new product|create product|add product/i }).first().click();
    await page.waitForTimeout(1200);

    // Flexible selectors to survive UI changes
    await fillIfPresent(page, ['input[name="name"]', 'input[placeholder*="Product name"]', 'input[id*=name]'], product.name);
    await fillIfPresent(page, ['input[name="slug"]', 'input[placeholder*="slug"]'], product.slug);
    await fillIfPresent(page, ['input[name="price"]', 'input[placeholder*="price"]', 'input[id*=price]'], product.priceUsd);

    const descDone = await fillIfPresent(page, ['textarea[name="description"]', 'textarea[placeholder*="Description"]', 'textarea[id*=description]'], product.description);
    if (!descDone) {
      const editor = page.locator('[contenteditable="true"]').first();
      if (await editor.count()) {
        await editor.click();
        await page.keyboard.type(product.description);
      }
    }

    const saveBtn = page.getByRole('button', { name: /save|publish|create/i }).first();
    await saveBtn.click();
    await page.waitForTimeout(1800);
  }

  console.log('Done. Validate product list in browser.');
  await context.storageState({ path: statePath });
  await browser.close();
})();
