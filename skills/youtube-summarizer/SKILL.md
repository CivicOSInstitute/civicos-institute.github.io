---
name: youtube-summarizer
description: Extract YouTube transcripts using yt-dlp and generate a structured summary with one-paragraph overview, timestamped sections, key announcements, product launches, names, and links/resources; include top five takeaways for videos longer than 30 minutes.
---

# youtube-summarizer

Use this skill to turn video-first updates into fast, structured text.

## Workflow

1. Run transcript extraction with `scripts/extract_transcript.py`.
2. Generate structured summary with `scripts/summarize_transcript.py`.
3. Return final markdown summary path and key highlights.

## Commands

```bash
# 1) Extract transcript + metadata
python3 scripts/extract_transcript.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --out-dir ./artifacts

# 2) Summarize
python3 scripts/summarize_transcript.py \
  --transcript ./artifacts/transcript.json \
  --out ./artifacts/summary.md
```

## Output format
- One-paragraph overview at top
- Section breakdown with timestamps
- Key announcements
- Product launches
- Names mentioned
- Links/resources referenced
- Top 5 takeaways (only if duration > 30 minutes)

## Edge-case policy
- No captions available: return explicit error and suggest fallback (manual summary).
- Auto-captions noisy: de-duplicate and compress repeated filler lines.
- Live streams/filler: reduce repetitive lines and prioritize high-information segments.

## Notes
- Prefer human captions first; fallback to auto captions.
- Keep summaries concise and scan-friendly.
