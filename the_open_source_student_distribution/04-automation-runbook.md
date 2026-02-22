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

3) Run full pipeline (now includes Stripe sync when key is present):
```bash
~/.openclaw/workspace/the_open_source_student_distribution/scripts/run_all.sh
```

## Optional: hourly refresh cron
```bash
( crontab -l 2>/dev/null; echo "15 * * * * source ~/.zshrc; ~/.openclaw/workspace/the_open_source_student_distribution/scripts/run_all.sh >/tmp/ebook-build.log 2>&1" ) | crontab -
```
