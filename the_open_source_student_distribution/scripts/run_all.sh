#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-$HOME/Desktop/the_open_source_student}"
ROOT="$HOME/.openclaw/workspace/the_open_source_student_distribution/scripts"

"$ROOT/preflight_check.sh" "$BASE"
"$ROOT/build_launch_assets.sh" "$BASE"
"$ROOT/generate_checkout_copy.sh"
"$ROOT/generate_launch_content.sh"

if [ -n "${STRIPE_SECRET_KEY:-}" ]; then
  "$ROOT/fetch_stripe_metrics.py" || true
else
  echo "INFO: STRIPE_SECRET_KEY not set, skipping Stripe sync"
fi

echo "AUTOMATION: COMPLETE"