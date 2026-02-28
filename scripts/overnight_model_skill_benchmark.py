#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
HELPER = ROOT / 'skills' / 'ollama-agent-queue' / 'scripts' / 'integration_helper.py'
OUT_DIR = ROOT / 'generated' / 'benchmarks'
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    'local/qwen-14b',
    'local/qwen2.5-14b',
    'local/mistral-small',
    'local/qwen-coder-32b',
    'qwen3.5:cloud',  # experimental lane candidate
]

SKILL_TASKS = [
    ('weather', 'Get a 3-day weather forecast for Miami, FL.'),
    ('apple-reminders', 'Add a reminder tomorrow at 9am to submit grant report.'),
    ('github', 'Check open PRs and CI status for owner/repo.'),
    ('youtube-summarizer', 'Summarize this YouTube video transcript and key takeaways.'),
    ('video-frames', 'Extract one frame every 10 seconds from this mp4.'),
    ('browser-automation', 'Log in to a website and capture a screenshot after submit.'),
    ('openai-whisper', 'Transcribe this local audio file to text.'),
    ('apple-notes', 'Create a note in Apple Notes with meeting bullets.'),
    ('apple-reminders', 'List overdue reminders and mark completed ones done.'),
    ('weather', 'What is the current temperature in New York City?'),
]

TOOLCALL_PROMPT = (
    'Return ONLY valid JSON with exact schema '
    '{"tool":"exec","arguments":{"command":"echo TOOLCALL_BENCH"}} '
    'No markdown, no commentary.'
)

SKILL_PROMPT_TMPL = (
    'You are selecting the best skill. Return ONLY JSON: '
    '{{"skill":"<one>","confidence":<0-1>}} . '\
    'Allowed skills: weather, apple-reminders, github, youtube-summarizer, video-frames, '\
    'browser-automation, openai-whisper, apple-notes. '\
    'Task: {task}'
)


def call_model(model: str, system_prompt: str, user_prompt: str, max_tokens: int = 220, timeout: int = 420):
    t0 = time.time()
    p = subprocess.run([
        'python3', str(HELPER),
        '--calling-skill', 'overnight-benchmark',
        '--model', model,
        '--priority', 'high',
        '--system-prompt', system_prompt,
        '--user-prompt', user_prompt,
        '--max-tokens', str(max_tokens),
        '--timeout-seconds', str(timeout),
    ], capture_output=True, text=True, timeout=timeout + 60)
    dt = round(time.time() - t0, 2)
    if p.returncode != 0:
        return {'ok': False, 'seconds': dt, 'error': (p.stderr or p.stdout).strip()[:280], 'result': ''}
    try:
        j = json.loads(p.stdout.strip())
        return {'ok': j.get('status') == 'complete', 'seconds': dt, 'error': j.get('error', ''), 'result': (j.get('result') or '').strip()}
    except Exception as e:
        return {'ok': False, 'seconds': dt, 'error': f'parse_error:{e}', 'result': p.stdout.strip()[:280]}


def eval_toolcall(raw: str):
    out = {'json_valid': False, 'schema_valid': False, 'exec_ok': False}
    try:
        obj = json.loads(raw)
        out['json_valid'] = True
        if isinstance(obj, dict) and obj.get('tool') == 'exec' and isinstance(obj.get('arguments'), dict):
            cmd = obj['arguments'].get('command', '')
            if isinstance(cmd, str) and cmd.strip():
                out['schema_valid'] = True
                ex = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                out['exec_ok'] = (ex.returncode == 0 and 'TOOLCALL_BENCH' in (ex.stdout or ''))
    except Exception:
        pass
    return out


def eval_skill(raw: str, expected: str):
    out = {'json_valid': False, 'match': False, 'predicted': ''}
    try:
        obj = json.loads(raw)
        out['json_valid'] = True
        pred = (obj.get('skill') or '').strip()
        out['predicted'] = pred
        out['match'] = pred == expected
    except Exception:
        pass
    return out


def main():
    report = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'models': {},
        'method': 'queue-routed empirical benchmark: tool-call schema pass + skill-routing accuracy + latency'
    }

    for model in MODELS:
        tool_rows = []
        skill_rows = []

        # repeat toolcall test for stability
        for _ in range(5):
            r = call_model(model, 'Return strict JSON only.', TOOLCALL_PROMPT, max_tokens=120, timeout=300)
            ev = eval_toolcall(r['result'])
            tool_rows.append({**r, **ev})

        # skill-task classification benchmark
        for expected, task in SKILL_TASKS:
            prompt = SKILL_PROMPT_TMPL.format(task=task)
            r = call_model(model, 'Choose best skill from allowed list; JSON only.', prompt, max_tokens=160, timeout=360)
            ev = eval_skill(r['result'], expected)
            skill_rows.append({**r, **ev, 'expected': expected, 'task': task})

        def avg(vals):
            return round(sum(vals) / len(vals), 2) if vals else None

        report['models'][model] = {
            'toolcall': {
                'runs': len(tool_rows),
                'json_valid_rate': round(sum(1 for x in tool_rows if x['json_valid']) / max(1, len(tool_rows)), 3),
                'schema_valid_rate': round(sum(1 for x in tool_rows if x['schema_valid']) / max(1, len(tool_rows)), 3),
                'exec_pass_rate': round(sum(1 for x in tool_rows if x['exec_ok']) / max(1, len(tool_rows)), 3),
                'avg_seconds': avg([x['seconds'] for x in tool_rows]),
                'details': tool_rows,
            },
            'skill_routing': {
                'runs': len(skill_rows),
                'json_valid_rate': round(sum(1 for x in skill_rows if x['json_valid']) / max(1, len(skill_rows)), 3),
                'accuracy': round(sum(1 for x in skill_rows if x['match']) / max(1, len(skill_rows)), 3),
                'avg_seconds': avg([x['seconds'] for x in skill_rows]),
                'details': skill_rows,
            }
        }

    # derive per-skill winner based on accuracy on tasks for that skill
    skill_best = {}
    for skill, _task in SKILL_TASKS:
        per_model = {}
        for model in MODELS:
            details = report['models'][model]['skill_routing']['details']
            subset = [x for x in details if x['expected'] == skill]
            if not subset:
                continue
            acc = sum(1 for x in subset if x['match']) / len(subset)
            sec = sum(x['seconds'] for x in subset) / len(subset)
            per_model[model] = {'accuracy': round(acc, 3), 'avg_seconds': round(sec, 2)}
        if per_model:
            best = sorted(per_model.items(), key=lambda kv: (-kv[1]['accuracy'], kv[1]['avg_seconds']))[0]
            skill_best[skill] = {'best_model': best[0], 'metrics': best[1], 'all_models': per_model}

    report['best_model_by_skill'] = skill_best

    # Experimental gate card for qwen3.5-27B candidate (from same run)
    q35_key = 'qwen3.5:cloud'
    if q35_key in report['models']:
        q = report['models'][q35_key]
        report['qwen3_5_experimental_gate_card'] = {
            'model': q35_key,
            'toolcall_exec_pass_rate': q['toolcall']['exec_pass_rate'],
            'toolcall_avg_seconds': q['toolcall']['avg_seconds'],
            'skill_routing_accuracy': q['skill_routing']['accuracy'],
            'skill_routing_avg_seconds': q['skill_routing']['avg_seconds'],
            'sample_size': {
                'toolcall_runs': q['toolcall']['runs'],
                'skill_runs': q['skill_routing']['runs']
            }
        }

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_json = OUT_DIR / f'overnight_model_skill_benchmark_{ts}.json'
    latest_json = OUT_DIR / 'overnight_model_skill_benchmark_latest.json'
    out_md = OUT_DIR / f'overnight_model_skill_benchmark_{ts}.md'
    latest_md = OUT_DIR / 'overnight_model_skill_benchmark_latest.md'

    out_json.write_text(json.dumps(report, indent=2), encoding='utf-8')
    latest_json.write_text(json.dumps(report, indent=2), encoding='utf-8')

    lines = [
        '# Overnight Local Model Benchmark Report',
        f"Generated: {report['generated_at']}",
        '',
        '## Summary by Model',
    ]
    for model in MODELS:
        m = report['models'][model]
        lines += [
            f"### {model}",
            f"- Toolcall exec pass rate: {m['toolcall']['exec_pass_rate']}",
            f"- Toolcall avg seconds: {m['toolcall']['avg_seconds']}",
            f"- Skill routing accuracy: {m['skill_routing']['accuracy']}",
            f"- Skill routing avg seconds: {m['skill_routing']['avg_seconds']}",
            ''
        ]
    lines += ['## Best model by skill (empirical)']
    for skill, d in sorted(skill_best.items()):
        lines.append(f"- {skill}: {d['best_model']} (acc={d['metrics']['accuracy']}, avg_sec={d['metrics']['avg_seconds']})")

    out_md.write_text('\n'.join(lines), encoding='utf-8')
    latest_md.write_text('\n'.join(lines), encoding='utf-8')

    print(str(latest_json))
    print(str(latest_md))


if __name__ == '__main__':
    main()
