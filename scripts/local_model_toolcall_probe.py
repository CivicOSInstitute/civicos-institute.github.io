#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

MODELS = [
    "qwen2.5:14b",
    "mistral-small3.2:24b-instruct-2506-q4_K_M",
    "qwen2.5-coder:32b-instruct-q3_K_L",
]

PROMPT = (
    'Return ONLY valid JSON with this exact schema: '
    '{"tool":"exec","arguments":{"command":"echo TOOLCALL_TEST"}} '
    'No markdown, no extra keys, no explanation.'
)

OUT_DIR = Path('/Users/AI-OPS/.openclaw/workspace/generated')
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_model(model: str):
    t0 = time.time()
    try:
        p = subprocess.run(
            ['ollama', 'run', model, PROMPT],
            capture_output=True,
            text=True,
            timeout=240
        )
        raw = (p.stdout or p.stderr or '').strip()
        sec = round(time.time() - t0, 2)

        result = {
            'model': model,
            'ok': False,
            'seconds': sec,
            'raw_preview': raw[:220].replace('\n', ' '),
            'json_valid': False,
            'schema_valid': False,
            'exec_result': ''
        }

        try:
            obj = json.loads(raw)
            result['json_valid'] = True
            if (
                isinstance(obj, dict)
                and obj.get('tool') == 'exec'
                and isinstance(obj.get('arguments'), dict)
                and isinstance(obj['arguments'].get('command'), str)
            ):
                result['schema_valid'] = True
                cmd = obj['arguments']['command']
                ex = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                result['exec_result'] = (ex.stdout or ex.stderr or '').strip()[:120]
                result['ok'] = ex.returncode == 0
        except Exception:
            pass

        return result
    except Exception as e:
        return {
            'model': model,
            'ok': False,
            'seconds': round(time.time() - t0, 2),
            'json_valid': False,
            'schema_valid': False,
            'exec_result': '',
            'raw_preview': str(e)[:220]
        }


def main():
    rows = [run_model(m) for m in MODELS]
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'probe': 'local_toolcall_proxy',
        'models': rows
    }

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = OUT_DIR / f'model_toolcall_probe_{ts}.json'
    latest = OUT_DIR / 'model_toolcall_probe_latest.json'
    out.write_text(json.dumps(payload, indent=2))
    latest.write_text(json.dumps(payload, indent=2))
    print(str(latest))


if __name__ == '__main__':
    main()
