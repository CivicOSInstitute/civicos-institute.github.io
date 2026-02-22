#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-$HOME/Desktop/the_open_source_student/launch-output/launch-content}"
mkdir -p "$OUT"
cat > "$OUT/x-post.txt" <<'EOF'
🚀 Launching: The Open Source Student

Practical digital fluency for the AI/open-source era.

✅ Core eBook ($19)
✅ Founder Bundle ($49)
✅ Team License ($149)

Get it now: [INSERT LINK]
EOF

cat > "$OUT/linkedin-post.txt" <<'EOF'
Today we’re launching The Open Source Student — a practical, implementation-first guide for learners, educators, and organizations.

Offers now live:
• Core eBook — $19
• Founder Bundle — $49
• Team License — $149

If you want real-world digital capability, this is built for action.

[INSERT LINK]
EOF

cat > "$OUT/email-blast.txt" <<'EOF'
Subject: Launch: The Open Source Student is Live

Hi —

The Open Source Student is now available.

You can get:
- Core eBook ($19)
- Founder Bundle ($49)
- Team License ($149)

This is a practical, step-by-step system designed to move from theory to execution.

Get access here: [INSERT LINK]

— Nick
EOF

echo "$OUT"