#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${NOTION_ENV_FILE:-$HOME/.openclaw/.env.notion}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

export NOTION_TOKEN="${NOTION_TOKEN:-${NOTION_TOKEN_VALUE:-}}"
export NOTION_DB_ID="${NOTION_DB_ID:-${NOTION_DB_ID_VALUE:-}}"
