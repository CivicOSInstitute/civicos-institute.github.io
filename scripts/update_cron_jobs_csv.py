#!/usr/bin/env python3
import csv
import subprocess
from pathlib import Path

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
OUT_PATHS = [
    WORKSPACE / 'generated' / 'current_cron_jobs.csv',
    WORKSPACE / 'main-dashboard' / 'static' / 'data' / 'current_cron_jobs.csv',
    Path('/Users/AI-OPS/Desktop/OpenClaw/Dashboards/Operations/current_cron_jobs.csv'),
]

FREQ_MAP = {
    '5 6 * * *': 'Daily at 06:05',
    '15 * * * *': 'Hourly at minute 15',
    '0 9 * * 0': 'Weekly on Sunday at 09:00',
    '30 6 * * 1': 'Weekly on Monday at 06:30',
    '45 * * * *': 'Hourly at minute 45',
    '0 */2 * * *': 'Every 2 hours (at minute 0)',
    '20 * * * *': 'Hourly at minute 20',
    '7 * * * *': 'Hourly at minute 7',
    '40 2 * * *': 'Daily at 02:40',
    '*/5 * * * *': 'Every 5 minutes',
    '*/3 * * * *': 'Every 3 minutes',
    '10 8 * * *': 'Daily at 08:10',
    '50 6 * * *': 'Daily at 06:50',
    '55 6 * * *': 'Daily at 06:55',
    '* * * * *': 'Every minute',
    '*/30 * * * *': 'Every 30 minutes',
}


def model_for(cmd: str) -> str:
    if 'scripts/local_model_toolcall_probe.py' in cmd:
        return 'Primary: local queue models (local/qwen-14b; local/mistral-small; local/qwen-coder-32b). Fallback: API model via openclaw agent'
    if 'scripts/grant_daily_local_scan.py' in cmd:
        return 'Primary: local queue model local/qwen-14b (priority high). Fallback: API model via openclaw agent'
    if 'skills/ollama-agent-queue/scripts/queue_manager.py process-once' in cmd:
        return 'Queue worker (enables local model priority routing)'
    if 'scripts/local_model_queue_enforcer.py' in cmd:
        return 'Policy guard (fails if direct Ollama/local server use is detected outside queue implementation)'
    if 'scripts/codex_mode_guard.py' in cmd:
        return 'N/A (reads Codex/API usage endpoint; no direct model call)'
    if 'scripts/weekly_cost_digest.py' in cmd:
        return 'N/A (summarizes token logs; does not run a model)'
    if 'run_ops_cycle.sh' in cmd:
        return 'Unknown / may invoke model-driven scripts indirectly'
    if 'scripts/workflow_slo_rollup.py' in cmd:
        return 'N/A (SLO analytics rollup; no model invocation detected)'
    if 'scripts/workflow_slo_alert.py' in cmd:
        return 'N/A (SLO alerting + likely-cause summary; no model invocation detected)'
    return 'N/A (no model invocation detected)'


def main() -> int:
    lines = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=True).stdout.splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        expr = ' '.join(parts[:5])
        cmd = parts[5]
        rows.append({
            'cron_expression': expr,
            'frequency_human': FREQ_MAP.get(expr, 'Custom schedule'),
            'command': cmd,
            'model_used': model_for(cmd),
        })

    for path in OUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['cron_expression', 'frequency_human', 'command', 'model_used'])
            writer.writeheader()
            writer.writerows(rows)

    print('updated')
    for p in OUT_PATHS:
        print(str(p))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
