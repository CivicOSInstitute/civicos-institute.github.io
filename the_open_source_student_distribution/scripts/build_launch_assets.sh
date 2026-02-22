#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$HOME/Desktop/the_open_source_student}"
OUT_ROOT="${2:-$HOME/Desktop/the_open_source_student/launch-output}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$OUT_ROOT/$STAMP"

mkdir -p "$OUT"/{core,founder,institution,manifests}

# Core
cp -f "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/02_PDF_Distribution/CivicOS_v1.3.3.3_PDF_BUNDLE_FINAL_ORDERED/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN.pdf" "$OUT/core/" || true
cp -f "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/04_EPUB_Distribution/CivicOS_v1.3.3.3_EPUB_BUNDLE_FINAL_ORDERED/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN.epub" "$OUT/core/" || true
cp -f "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/01_Markdown_Source/CivicOS_v1.3.3.3_Markdown_BUNDLE_FINAL_ORDERED/Student-Setup-Checklist-v1_3_3-FINAL-LOCKDOWN.md" "$OUT/core/" || true

# Founder bundle
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/01_Markdown_Source/CivicOS_v1.3.3.3_Markdown_BUNDLE_FINAL_ORDERED" "$OUT/founder/markdown" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/02_PDF_Distribution/CivicOS_v1.3.3.3_PDF_BUNDLE_FINAL_ORDERED" "$OUT/founder/pdf" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/03_Word_Distribution/CivicOS_v1.3.3.3_Word_BUNDLE_FINAL_ORDERED" "$OUT/founder/word" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/04_EPUB_Distribution/CivicOS_v1.3.3.3_EPUB_BUNDLE_FINAL_ORDERED" "$OUT/founder/epub" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/08_Founders_Complete_Edition_Unified/Open-Source-Student-Founders-Complete-Edition-UNIFIED-INTERNAL-LINKS" "$OUT/founder/founders-edition" || true

# Institution bundle
cp -R "$OUT/founder" "$OUT/institution/full" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/06_LMS_HTML/CivicOS_v1.3.3.3_LMS_HTML_BUNDLE_FINAL_ORDERED" "$OUT/institution/lms-html" || true
cp -R "$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/07_LMS_SCORM/CivicOS_v1.3.3.3_LMS_SCORM_BUNDLE_FINAL_ORDERED" "$OUT/institution/lms-scorm" || true

cat > "$OUT/manifests/START-HERE.txt" <<'EOF'
The Open Source Student Launch Packages

Packages:
- core.zip ($19)
- founder.zip ($49)
- institution.zip ($149)
EOF

echo "Generated: $(date)" >> "$OUT/manifests/START-HERE.txt"

(cd "$OUT" && zip -qr core.zip core && zip -qr founder.zip founder && zip -qr institution.zip institution)

(cd "$OUT" && shasum -a 256 core.zip founder.zip institution.zip > manifests/checksums.sha256)

cat > "$OUT/manifests/manifest.txt" <<EOF
OUTPUT_DIR=$OUT
CORE_ZIP=$OUT/core.zip
FOUNDER_ZIP=$OUT/founder.zip
INSTITUTION_ZIP=$OUT/institution.zip
CHECKSUMS=$OUT/manifests/checksums.sha256
EOF

echo "$OUT"