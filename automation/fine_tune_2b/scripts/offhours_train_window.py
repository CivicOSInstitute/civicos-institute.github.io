#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/Users/AI-OPS/.openclaw/workspace/automation/fine_tune_2b')
CFG = json.loads((ROOT / 'config/specialists.json').read_text())
LOG = ROOT / 'logs' / 'offhours_train.log'
LOG.parent.mkdir(parents=True, exist_ok=True)

WINDOW_START = dt.time(1, 0)
WINDOW_END = dt.time(6, 25)


def in_window(now: dt.datetime) -> bool:
    t = now.time()
    return WINDOW_START <= t <= WINDOW_END


def pick_specialist(now: dt.datetime) -> str:
    specs = [s['id'] for s in CFG['specialists']]
    # Rotate one specialist per day to keep load predictable.
    return specs[now.toordinal() % len(specs)]


def run(cmd: list[str]):
    with LOG.open('a') as f:
        f.write(f"\n[{dt.datetime.now().isoformat(timespec='seconds')}] RUN {' '.join(cmd)}\n")
        p = subprocess.run(cmd, stdout=f, stderr=f)
        f.write(f"EXIT {p.returncode}\n")
    return p.returncode


def main():
    now = dt.datetime.now()
    if not in_window(now):
        print('outside window; skip')
        return 0

    sid = pick_specialist(now)
    print(f'offhours window active; training {sid}')
    cmd = [sys.executable, str(ROOT / 'scripts/orchestrate.py'), '--specialist', sid]
    return run(cmd)


if __name__ == '__main__':
    raise SystemExit(main())
