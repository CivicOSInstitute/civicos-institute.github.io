# Automation Runbook — The Open Source Student

## What is now automated
1. Build launch-ready package zips:
   - `core.zip`
   - `founder.zip`
   - `institution.zip`
2. Generate checksum file for delivery integrity.
3. Generate checkout copy for Stripe/Gumroad.
4. Emit a manifest with exact output paths.

## Run (single command)
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/build_launch_assets.sh && \
~/.openclaw/workspace/the_open_source_student_distribution/scripts/generate_checkout_copy.sh
```

## Outputs
- Packages root: `~/Desktop/the_open_source_student/launch-output/<timestamp>/`
- Checkout copy: `~/Desktop/the_open_source_student/launch-output/checkout-copy.md`

## Lemon Squeezy live metrics setup (recommended now)
1) Create API key in Lemon Squeezy dashboard and set env vars:
```bash
echo 'export LEMONSQUEEZY_API_KEY="lsq_..."' >> ~/.zshrc
# Optional but recommended for cleaner metrics filter:
echo 'export LEMONSQUEEZY_STORE_ID="12345"' >> ~/.zshrc
source ~/.zshrc
```

2) Test Lemon Squeezy sync:
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/fetch_lemonsqueezy_metrics.py
```

## Stripe live metrics setup
1) Export your Stripe secret key in shell profile:
```bash
echo 'export STRIPE_SECRET_KEY="sk_live_..."' >> ~/.zshrc
source ~/.zshrc
```

2) Test Stripe sync:
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/fetch_stripe_metrics.py
```

3) Run full pipeline (includes Lemon Squeezy + Stripe sync when keys are present):
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/run_all.sh
```

## Amazon KDP + Apple Books placeholders (export-based)
Until direct APIs are confirmed, drop report CSVs here:
- `~/.openclaw/workspace/the_open_source_student_distribution/output/imports/amazon_kdp_report.csv`
- `~/.openclaw/workspace/the_open_source_student_distribution/output/imports/apple_books_report.csv`

Then run:
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/fetch_amazon_kdp_metrics.py
~/.openclaw/workspace/the_open_source_student_distribution/scripts/fetch_apple_books_metrics.py
```

## Optional: hourly refresh cron
```bash
( crontab -l 2>/dev/null; echo "15 * * * * source ~/.zshrc; ~/.openclaw/workspace/the_open_source_student_distribution/scripts/run_all.sh >/tmp/ebook-build.log 2>&1" ) | crontab -
```
