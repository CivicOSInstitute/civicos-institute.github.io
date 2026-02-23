#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = BASE / 'generated'
GEN.mkdir(parents=True, exist_ok=True)
STATE = GEN / 'battery_alert_state.json'
SEND_TG = Path('/Users/AI-OPS/.openclaw/scripts/send-telegram.sh')
IMSG_TARGET_FILE = Path('/Users/AI-OPS/.openclaw/workspace/generated/imessage_target.txt')


def get_battery():
    out = subprocess.check_output(['pmset', '-g', 'batt'], text=True, timeout=5)
    m = re.search(r'(\d+)%', out)
    pct = int(m.group(1)) if m else 0
    low = out.lower()
    charging = 'charging' in low or 'charged' in low or 'ac power' in low
    return pct, charging, out.strip()


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {'last_alert_level': None, 'last_alert_at': None}


def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))


def send_telegram(msg):
    if SEND_TG.exists():
        subprocess.run([str(SEND_TG), '8334496229', msg], check=False)


def send_imessage(msg):
    # Optional target file; put phone/email/chat id in generated/imessage_target.txt
    if not IMSG_TARGET_FILE.exists():
        return
    target = IMSG_TARGET_FILE.read_text().strip()
    if not target:
        return
    if subprocess.run(['which', 'imsg'], capture_output=True, text=True).returncode != 0:
        return
    # Best-effort; command variants differ by install
    subprocess.run(['imsg', 'send', '--to', target, '--text', msg], check=False)


def main():
    pct, charging, raw = get_battery()
    st = load_state()

    if charging or pct > 12:
        # reset when healthy/charging
        st['last_alert_level'] = None
        st['last_alert_at'] = datetime.now().isoformat(timespec='seconds')
        save_state(st)
        print(json.dumps({'battery_pct': pct, 'charging': charging, 'alert': False}))
        return

    # alert levels: <=10, <=5
    level = 5 if pct <= 5 else (10 if pct <= 10 else None)
    if level is None:
        print(json.dumps({'battery_pct': pct, 'charging': charging, 'alert': False}))
        return

    if st.get('last_alert_level') == level:
        print(json.dumps({'battery_pct': pct, 'charging': charging, 'alert': False, 'reason': 'already_alerted'}))
        return

    msg = f"⚠️ Mac battery low: {pct}% ({'charging' if charging else 'on battery'}). Connect power now."
    send_telegram(msg)
    send_imessage(msg)

    st['last_alert_level'] = level
    st['last_alert_at'] = datetime.now().isoformat(timespec='seconds')
    save_state(st)

    print(json.dumps({'battery_pct': pct, 'charging': charging, 'alert': True, 'level': level, 'raw': raw}))


if __name__ == '__main__':
    main()
