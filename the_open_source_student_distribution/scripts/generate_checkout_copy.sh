#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-$HOME/Desktop/the_open_source_student/launch-output/checkout-copy.md}"
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<'EOF'
# Checkout Copy (Paste into Stripe/Gumroad)

## Product 1
Name: The Open Source Student — Core eBook
Price: $19
Description: Main book (PDF + EPUB) plus Student Setup Checklist. Ideal for individual learners.

## Product 2
Name: The Open Source Student — Founder Bundle
Price: $49
Description: Complete multi-format bundle (PDF/EPUB/DOCX/HTML) + Operational Guide + Terminal Survival Guide + Hardware Guide + Emergency Fix Card + Founder Edition.

## Product 3
Name: The Open Source Student — Team License (Up to 10 Seats)
Price: $149
Description: Founder Bundle + LMS-ready HTML/SCORM materials with team usage rights.
EOF

echo "$OUT"