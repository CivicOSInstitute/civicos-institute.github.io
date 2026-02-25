#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

MODELS = [
    "local/qwen-14b",
    "local/mistral-small",
    "local/qwen-coder-32b",
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
    helper = Path('/Users/AI-OPS/.openclaw/workspace/skills/ollama-agent-queue/scripts/integration_helper.py')

    def parse_and_eval(raw: str, route: str, err: str = ''):
        sec = round(time.time() - t0, 2)
        result = {
            'model': model,
            'route': route,
            'ok': False,
            'seconds': sec,
            'raw_preview': (raw or '')[:220].replace('\n', ' '),
            'json_valid': False,
            'schema_valid': False,
            'exec_result': '',
            'error': err,
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
        except Exception as e:
            result['error'] = result['error'] or f'json_parse_error: {e}'
        return result

    try:
        # Primary: local queue
        q = subprocess.run(
            [
                'python3', str(helper),
                '--calling-skill', 'model-toolcall-probe',
                '--model', model,
                '--priority', 'high',
                '--system-prompt', 'Return only strict JSON as instructed.',
                '--user-prompt', PROMPT,
                '--max-tokens', '180',
                '--timeout-seconds', '240',
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if q.returncode == 0:
            payload = json.loads(q.stdout.strip())
            if payload.get('status') == 'complete':
                return parse_and_eval((payload.get('result') or '').strip(), 'local_queue')
            local_err = f"local_queue_status={payload.get('status')}"
        else:
            local_err = (q.stderr or q.stdout or 'local queue failed').strip()[:220]

        # Fallback: API model
        a = subprocess.run(
            [
                'openclaw', 'agent', '--local', '--agent', 'main',
                '--message', PROMPT,
                '--json', '--timeout', '240'
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if a.returncode != 0:
            return parse_and_eval('', 'api_fallback', f"{local_err}; api_error={(a.stderr or a.stdout or '').strip()[:180]}")

        data = json.loads(a.stdout)
        raw = (data.get('payloads') or [{}])[0].get('text', '').strip()
        return parse_and_eval(raw, 'api_fallback', local_err)
    except Exception as e:
        return {
            'model': model,
            'route': 'error',
            'ok': False,
            'seconds': round(time.time() - t0, 2),
            'json_valid': False,
            'schema_valid': False,
            'exec_result': '',
            'raw_preview': str(e)[:220],
            'error': str(e)[:220],
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
