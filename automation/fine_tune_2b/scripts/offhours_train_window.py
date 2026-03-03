#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/Users/AI-OPS/.openclaw/workspace/automation/fine_tune_2b')
CFG = json.loads((ROOT / 'config/specialists.json').read_text())
MISSION = ROOT / 'config/mission_plan.json'
LOG = ROOT / 'logs' / 'offhours_train.log'
LOG.parent.mkdir(parents=True, exist_ok=True)

WINDOW_START = dt.time(1, 0)
WINDOW_END = dt.time(6, 25)


def in_window(now: dt.datetime) -> bool:
    t = now.time()
    return WINDOW_START <= t <= WINDOW_END


def load_wave_specialists() -> list[str]:
    if not MISSION.exists():
        return [s['id'] for s in CFG['specialists'][:2]]
    m = json.loads(MISSION.read_text())
    wave = str(m.get('active_wave', 1))
    return m.get('waves', {}).get(wave, [])


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

    sids = load_wave_specialists()
    if not sids:
        print('no active wave specialists configured; skip')
        return 0

    rc = 0
    for sid in sids:
        print(f'offhours window active; training {sid}')
        cmd = [sys.executable, str(ROOT / 'scripts/orchestrate.py'), '--specialist', sid]
        rc = run(cmd) or rc

    # Sync latest router map after nightly run.
    sync_cmd = [sys.executable, str(ROOT / 'scripts/push_router_map.py')]
    rc = run(sync_cmd) or rc
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
