#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$HOME/Desktop/the_open_source_student}"
REQ=(
"$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/02_PDF_Distribution/CivicOS_v1.3.3.3_PDF_BUNDLE_FINAL_ORDERED/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN.pdf"
"$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/04_EPUB_Distribution/CivicOS_v1.3.3.3_EPUB_BUNDLE_FINAL_ORDERED/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN.epub"
"$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/06_LMS_HTML/CivicOS_v1.3.3.3_LMS_HTML_BUNDLE_FINAL_ORDERED"
"$SRC/Build/v1.3.3.3/Archival Release/CivicOS_v1.3.3.3_COMPLETE_ARCHIVE_FINAL/07_LMS_SCORM/CivicOS_v1.3.3.3_LMS_SCORM_BUNDLE_FINAL_ORDERED"
)
missing=0
for p in "${REQ[@]}"; do
  if [ ! -e "$p" ]; then
    echo "MISSING: $p"
    missing=1
  else
    echo "OK: $p"
  fi
done
if [ "$missing" -eq 1 ]; then
  echo "PRECHECK: FAIL"
  exit 1
fi
echo "PRECHECK: PASS"