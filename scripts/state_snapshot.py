#!/usr/bin/env python3
"""Append durable daily operational state snapshot for continuity across models."""
import json
import subprocess
from datetime import datetime
from pathlib import Path

WS = Path('/Users/AI-OPS/.openclaw/workspace')
OUT_DIR = WS / 'data' / 'state'
OUT_DIR.mkdir(parents=True, exist_ok=True)

AUTH_PATH = Path('/Users/AI-OPS/.openclaw/agents/main/agent/auth-profiles.json')


def run_json(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": (p.stderr or p.stdout).strip()[:500]}
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"raw": p.stdout[:1000]}


def get_auth_summary():
    if not AUTH_PATH.exists():
        return {"exists": False}
    j = json.loads(AUTH_PATH.read_text())
    profiles = j.get('profiles', {})
    out = {"exists": True, "profiles": list(profiles.keys()), "openai_codex": {}}
    codex = profiles.get('openai-codex:default', {})
    if codex:
        out['openai_codex'] = {
            "profile": "openai-codex:default",
            "accountId": codex.get('accountId'),
            "type": codex.get('type'),
            "provider": codex.get('provider'),
        }
    return out


def crontab_lines():
    p = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    return p.stdout.splitlines() if p.returncode == 0 else []


def main():
    now = datetime.now().astimezone()
    day = now.strftime('%Y-%m-%d')
    ts = now.strftime('%Y-%m-%d %H:%M:%S %Z')

    status = run_json(['openclaw', 'status', '--json'])
    model_status_raw = subprocess.run(['openclaw', 'models', 'status'], capture_output=True, text=True)

    cron = crontab_lines()
    queue_worker = any('queue_manager.py process-once' in l for l in cron)
    queue_enforcer = any('local_model_queue_enforcer.py' in l for l in cron)
    csv_updater = any('update_cron_jobs_csv.py' in l for l in cron)

    snapshot = {
        'timestamp': ts,
        'auth': get_auth_summary(),
        'policy_flags': {
            'local_model_queue_worker_cron': queue_worker,
            'local_model_queue_enforcer_cron': queue_enforcer,
            'cron_csv_auto_update': csv_updater,
            'queue_hard_rule_declared': True,
        },
        'status_summary': {
            'channelSummary': status.get('channelSummary') if isinstance(status, dict) else None,
            'defaults': (status.get('sessions', {}) or {}).get('defaults') if isinstance(status, dict) else None,
            'recent_session_model': (((status.get('sessions', {}) or {}).get('recent') or [{}])[0]).get('model') if isinstance(status, dict) else None,
        },
        'models_status_text': (model_status_raw.stdout or model_status_raw.stderr)[:1500],
    }

    jsonl = OUT_DIR / 'continuity_snapshots.jsonl'
    with jsonl.open('a') as f:
        f.write(json.dumps(snapshot) + '\n')

    md = WS / 'memory' / f'{day}.md'
    md.parent.mkdir(parents=True, exist_ok=True)
    with md.open('a') as f:
        f.write('\n## ' + ts + ' — Continuity Snapshot\n')
        codex = snapshot['auth'].get('openai_codex', {})
        f.write(f"- Codex profile: `{codex.get('profile', 'n/a')}` accountId `{codex.get('accountId', 'unknown')}`\n")
        f.write(f"- Policy flags: queue_worker={queue_worker}, queue_enforcer={queue_enforcer}, cron_csv_auto_update={csv_updater}\n")
        f.write(f"- Recent session model: `{snapshot['status_summary'].get('recent_session_model')}`\n")

    print(jsonl)


if __name__ == '__main__':
    main()
