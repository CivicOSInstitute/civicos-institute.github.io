#!/usr/bin/env bash
set -euo pipefail

echo "[MC] Reset Gateway started: $(date)"
openclaw gateway restart
sleep 2

echo "[MC] Post-restart status"
openclaw gateway status

echo "[MC] Done: reset_gateway.sh"
