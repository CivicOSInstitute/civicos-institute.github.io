#!/usr/bin/env bash
set -euo pipefail

echo "[MC] OpenClaw Doctor started: $(date)"

echo "\n=== openclaw status --deep ==="
openclaw status --deep || true

echo "\n=== openclaw security audit --deep ==="
openclaw security audit --deep || true

echo "\n=== openclaw update status ==="
openclaw update status || true

echo "\n[MC] Done: openclaw_doctor.sh"
