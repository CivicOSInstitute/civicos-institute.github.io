#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input-video> <output-dir>"
  exit 1
fi

INPUT="$1"
OUTDIR="$2"
mkdir -p "$OUTDIR"

# 16:9 (YouTube / X landscape)
ffmpeg -y -i "$INPUT" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k \
  "$OUTDIR/master_16x9.mp4"

# 9:16 (Shorts/Reels/TikTok)
ffmpeg -y -i "$INPUT" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
  -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 160k \
  "$OUTDIR/master_9x16.mp4"

# 1:1 (feed posts)
ffmpeg -y -i "$INPUT" \
  -vf "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080" \
  -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 160k \
  "$OUTDIR/master_1x1.mp4"

echo "Exported variants to: $OUTDIR"
