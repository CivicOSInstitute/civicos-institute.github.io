#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") \"Skill Name\" \"Description\" [output-dir]"
  exit 1
fi

NAME="$1"
DESC="$2"
OUT_DIR="${3:-$HOME/.openclaw/workspace/skills}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

python3 "$ROOT/create_skill.py" \
  --name "$NAME" \
  --description "$DESC" \
  --output-dir "$OUT_DIR" \
  --resources scripts,references,assets \
  --with-examples \
  --with-readme

SLUG=$(python3 - <<'PY' "$NAME"
import re,sys
s=sys.argv[1].strip().lower()
s=re.sub(r'[^a-z0-9]+','-',s)
s=re.sub(r'-+','-',s).strip('-')[:64]
print(s)
PY
)

python3 "$ROOT/package_skill.py" "$OUT_DIR/$SLUG" --out-dir "$OUT_DIR"

echo "Done: $OUT_DIR/$SLUG.skill"
