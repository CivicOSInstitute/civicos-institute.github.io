#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <exports-dir> <report-path>"
  exit 1
fi

EXPORTS_DIR="$1"
REPORT_PATH="$2"

shopt -s nullglob
files=("$EXPORTS_DIR"/*.mp4)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No mp4 files found in $EXPORTS_DIR" >&2
  exit 2
fi

{
  echo "{"
  echo "  \"generated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," 
  echo "  \"exports\": ["
  for i in "${!files[@]}"; do
    f="${files[$i]}"
    dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f" | awk '{printf "%.2f", $1}')
    res=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$f")
    audio=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=nw=1:nk=1 "$f" || true)
    comma=","; [[ "$i" -eq $((${#files[@]}-1)) ]] && comma=""
    echo "    {\"file\": \"$(basename "$f")\", \"duration_s\": $dur, \"resolution\": \"$res\", \"audio\": \"${audio:-none}\"}$comma"
  done
  echo "  ]"
  echo "}"
} > "$REPORT_PATH"

echo "QA report written: $REPORT_PATH"
