#!/usr/bin/env bash
set -euo pipefail

CONTAINER="civic-n8n"
BACKUP_DIR="/Users/AI-OPS/.openclaw/workspace/backups/n8n"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/n8n-backup-$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# Use a helper container so this works on Docker Desktop (no host access to /var/lib/docker required)
OUT_BASENAME="$(basename "$OUT")"
docker run --rm \
  --volumes-from "$CONTAINER" \
  -v "$BACKUP_DIR":/backup \
  alpine:3.20 \
  sh -c 'cd /home/node/.n8n && tar -czf "/backup/'"$OUT_BASENAME"'" .'

# Keep last 14 backups
ls -1t "$BACKUP_DIR"/n8n-backup-*.tar.gz 2>/dev/null | tail -n +15 | xargs -I{} rm -f "{}" || true

echo "Backup created: $OUT"
