#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <project-name> <base-dir>"
  exit 1
fi

PROJECT_NAME="$1"
BASE_DIR="$2"
SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g;s/^-+|-+$//g')
STAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="${BASE_DIR}/${STAMP}_${SLUG}"

mkdir -p "$PROJECT_DIR"/{src,assets,audio,captions,edits,exports,qa,tmp}

cat > "$PROJECT_DIR/brief.md" <<'MD'
# Video Brief

## Objective
- 

## Audience
- 

## Platform + Duration
- 

## Core Message
- 

## Hook (first 3 seconds)
- 

## CTA
- 
MD

echo "$PROJECT_DIR"
