#!/usr/bin/env bash
set -euo pipefail

# Natural-first voiceover generator with provider auto-selection.
# Priority: ElevenLabs -> OpenAI TTS -> macOS say fallback.
#
# Script tags supported (lightweight):
#   [[pause:500]]       -> half-second pause
#   [[emph:wording]]    -> stronger spoken emphasis (text shaping)
#   [[slow:sentence]]   -> slower delivery hint (comma/ellipsis shaping)
#
# Usage:
#   ./voiceover_natural.sh <script.txt> <output.wav> [narrator|founder]

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <script.txt> <output.wav> [narrator|founder]" >&2
  exit 1
fi

SCRIPT_PATH="$1"
OUT_WAV="$2"
MODE="${3:-narrator}"

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "Script file not found: $SCRIPT_PATH" >&2
  exit 2
fi

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

RAW_AUDIO="$TMP_DIR/raw_audio"
TEXT=$(cat "$SCRIPT_PATH")

if [[ -z "${TEXT// }" ]]; then
  echo "Script is empty: $SCRIPT_PATH" >&2
  exit 3
fi

# Pre-shape text for natural cadence using lightweight tags.
# Converts simple inline control tags into punctuation/cadence hints that work across providers.
TEXT=$(python3 - <<'PY' "$TEXT"
import re, sys
text = sys.argv[1]

# pause tags -> punctuation pauses
text = re.sub(r"\[\[pause:(\d{1,4})\]\]", lambda m: " ..." if int(m.group(1)) >= 400 else ",", text)

# emphasis tags -> casing + punctuation
text = re.sub(r"\[\[emph:(.*?)\]\]", lambda m: f"{m.group(1).upper()}.", text)

# slow tags -> spaced cadence
text = re.sub(r"\[\[slow:(.*?)\]\]", lambda m: f"{m.group(1).strip()}...", text)

# whitespace cleanup
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n{3,}", "\n\n", text).strip()
print(text)
PY
)

voice_hint="neutral"
pace_hint="medium"
if [[ "$MODE" == "founder" ]]; then
  voice_hint="warm"
  pace_hint="conversational"
fi

DELIVERY_PREFIX="Read naturally with ${voice_hint} tone and ${pace_hint} pacing. Prioritize human cadence and clear sentence boundaries."
TTS_TEXT="$DELIVERY_PREFIX\n\n$TEXT"

used_provider=""

# 1) ElevenLabs (best natural default when key exists)
if [[ -n "${ELEVENLABS_API_KEY:-}" ]]; then
  ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-21m00Tcm4TlvDq8ikWAM}"  # default Rachel
  model_id="${ELEVENLABS_MODEL_ID:-eleven_turbo_v2_5}"

  json_payload=$(cat <<JSON
{
  "text": $(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$TTS_TEXT"),
  "model_id": "${model_id}",
  "voice_settings": {
    "stability": 0.35,
    "similarity_boost": 0.85,
    "style": 0.35,
    "use_speaker_boost": true
  }
}
JSON
)

  if curl -sS -f \
      -X POST "https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}" \
      -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$json_payload" \
      -o "${RAW_AUDIO}.mp3"; then
    used_provider="elevenlabs"
  fi
fi

# 2) OpenAI TTS fallback
if [[ -z "$used_provider" && -n "${OPENAI_API_KEY:-}" ]]; then
  OPENAI_TTS_MODEL="${OPENAI_TTS_MODEL:-gpt-4o-mini-tts}"
  OPENAI_TTS_VOICE="${OPENAI_TTS_VOICE:-alloy}"

  json_payload=$(cat <<JSON
{
  "model": "${OPENAI_TTS_MODEL}",
  "voice": "${OPENAI_TTS_VOICE}",
  "input": $(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$TTS_TEXT")
}
JSON
)

  if curl -sS -f \
      -X POST "https://api.openai.com/v1/audio/speech" \
      -H "Authorization: Bearer ${OPENAI_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$json_payload" \
      -o "${RAW_AUDIO}.mp3"; then
    used_provider="openai"
  fi
fi

# 3) macOS fallback
if [[ -z "$used_provider" ]]; then
  SAY_VOICE="${SAY_VOICE:-Samantha}"
  # Slightly slower for natural cadence
  say -v "$SAY_VOICE" -r 175 -o "${RAW_AUDIO}.aiff" "$TTS_TEXT"
  used_provider="macos_say"
fi

# Post-process for natural clarity + platform consistency
input_audio=""
if [[ -f "${RAW_AUDIO}.mp3" ]]; then
  input_audio="${RAW_AUDIO}.mp3"
elif [[ -f "${RAW_AUDIO}.aiff" ]]; then
  input_audio="${RAW_AUDIO}.aiff"
else
  echo "Voiceover generation failed (no raw audio created)." >&2
  exit 4
fi

mkdir -p "$(dirname "$OUT_WAV")"

ffmpeg -y -i "$input_audio" \
  -af "highpass=f=80,lowpass=f=13000,deesser=i=0.4:m=0.5:f=0.5,acompressor=threshold=-18dB:ratio=2.5:attack=15:release=180,loudnorm=I=-16:LRA=11:TP=-1.5" \
  -ar 48000 -ac 1 "$OUT_WAV" >/dev/null 2>&1

echo "voiceover_provider=$used_provider"
echo "voiceover_mode=$MODE"
echo "voiceover_output=$OUT_WAV"