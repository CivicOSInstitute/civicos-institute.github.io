---
name: ai-video-pipeline
description: Build short-form and long-form videos from a brief using a deterministic pipeline (script, narration, rough cut, captions, and multi-format exports) with ffmpeg + local tooling.
---

# AI Video Pipeline

Use this skill when the user wants production-ready video assets quickly from a concept, transcript, or source footage.

## What this skill does

1. Normalizes a project brief into a production spec.
2. Generates a script + scene plan (hook, body, CTA).
3. Builds a rough cut from source clips/assets.
4. Adds narration/audio bed and normalizes loudness.
5. Generates subtitles and burns captions.
6. Exports platform variants (9:16, 16:9, 1:1).
7. Produces a QA report (duration, loudness, dropped/blank frames, outputs).

## Input contract

Required:
- `project_name`
- `goal` (e.g., launch teaser, explainer, highlight reel)
- `target_platforms` (youtube, x, linkedin, tiktok, instagram)
- `duration_seconds`
- At least one source:
  - `source_video` path, or
  - `source_audio` path + `broll_dir`, or
  - `script_text`

Optional:
- `tone` (bold, educational, cinematic, documentary, etc.)
- `cta`
- `brand_hex_primary`, `brand_hex_secondary`
- `logo_path`
- `music_path`
- `voiceover_path`
- `voice_profile` (`auto` default, `narrator`, `founder`)
- `captions_style` (minimal, bold, subtitle)

## Output contract

Return:
- `project_dir`
- `master_video`
- `exports[]` (per platform)
- `captions` (`.srt` and burned-in outputs)
- `qa_report.json`
- `notes` (manual touch-ups recommended)

## Execution workflow

1. Initialize project folders with `scripts/init_project.sh`.
2. Write/edit brief in `project/brief.md`.
3. If needed, extract transcript with Whisper skill/tooling and save `captions/raw.srt`.
4. Build rough cut: concatenate/select clips; trim to target duration.
5. Audio pass:
   - generate natural voiceover with `scripts/voiceover_natural.sh` using `voice_profile=auto`
   - support expressive script tags: `[[pause:ms]]`, `[[emph:text]]`, `[[slow:text]]`, `[[calm:text]]`, `[[urgent:text]]`, `[[inspiring:text]]`
   - voiceover mix
   - background music ducking
   - loudness normalization (EBU R128 target)
6. Caption pass:
   - clean SRT timing
   - burn styled captions for each export aspect ratio
7. Export variants with `scripts/export_variants.sh`.
8. Generate QA summary with `scripts/qa_report.sh`.

## Guardrails

- Never claim "fully autonomous replacement" of editors.
- Default positioning: speed + iteration + cost compression with human creative oversight.
- Preserve source media; write outputs into project-scoped folders only.
- Fail fast when required input is missing; print exact remediation.

## Edge cases

- Missing footage -> generate script + shot list only, no render.
- No voiceover/music -> export clean spoken/audio-light version.
- Captions fail -> still export clean master and report caption failure.
- Aspect-ratio crop conflicts -> produce letterboxed fallback and note it.
