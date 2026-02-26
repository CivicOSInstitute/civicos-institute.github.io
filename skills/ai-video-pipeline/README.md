# ai-video-pipeline

Deterministic video production scaffold for quick draft-to-export workflows.

## Includes

- `SKILL.md` - operational instructions and guardrails
- `scripts/init_project.sh` - project folder + brief bootstrap
- `scripts/export_variants.sh` - 16:9, 9:16, 1:1 renders
- `scripts/qa_report.sh` - JSON output integrity summary

## Quick start

```bash
# 1) Initialize project
PROJECT_DIR=$(./scripts/init_project.sh "CivicOS Launch Teaser" /tmp/video_projects)
echo "$PROJECT_DIR"

# 2) Put source video at:
# $PROJECT_DIR/src/master.mp4

# 3) Export platform variants
./scripts/export_variants.sh "$PROJECT_DIR/src/master.mp4" "$PROJECT_DIR/exports"

# 4) Generate QA report
./scripts/qa_report.sh "$PROJECT_DIR/exports" "$PROJECT_DIR/qa/report.json"
cat "$PROJECT_DIR/qa/report.json"
```

## Notes

- Uses `ffmpeg`/`ffprobe` from PATH.
- This is an MVP scaffold: expand with auto-script generation, voiceover, and caption styling next.
