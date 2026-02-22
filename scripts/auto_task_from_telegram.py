#!/usr/bin/env python3
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

CONFIG = Path('/Users/AI-OPS/.openclaw/openclaw.json')
STATE = Path('/Users/AI-OPS/.openclaw/.auto-task-state.json')
DB = Path('/Users/AI-OPS/.openclaw/task-tracker/tasks.db')
TARGET_CHAT = '8334496229'  # Nick direct chat

ACTION_RE = re.compile(
    r"\b(create|build|fix|update|review|send|draft|run|check|follow\s*up|schedule|set\s*up|prepare|deploy|launch|automate)\b",
    re.I,
)

IGNORE_RE = re.compile(r"^(hi|hello|hey|thanks|ok|okay|yes|no|burt\??)$", re.I)


def load_token():
    cfg = json.loads(CONFIG.read_text())
    token = cfg.get('channels', {}).get('telegram', {}).get('botToken', '')
    if not token:
        raise RuntimeError('Telegram bot token missing in openclaw.json')
    return token


def tg_post(token, method, params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.loads(r.read().decode('utf-8'))
    if not payload.get('ok'):
        raise RuntimeError(payload.get('description', 'Telegram API error'))
    return payload.get('result')


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {'offset': 0, 'processed': []}


def save_state(state):
    # keep processed small
    state['processed'] = state.get('processed', [])[-2000:]
    STATE.write_text(json.dumps(state, indent=2))


def is_actionable(text: str) -> bool:
    t = (text or '').strip()
    if len(t) < 12:
        return False
    if IGNORE_RE.match(t):
        return False
    if t.lower().startswith(('task:', 'todo:', 'action:')):
        return True
    return bool(ACTION_RE.search(t))


def normalize_title(text: str) -> str:
    t = text.strip()
    t = re.sub(r'^(task:|todo:|action:)\s*', '', t, flags=re.I)
    return (t[:197] + '...') if len(t) > 200 else t


def task_exists(conn, source_key: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM task WHERE notes LIKE ? LIMIT 1", (f"%{source_key}%",))
    return cur.fetchone() is not None


def create_task(conn, title: str, source_key: str):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO task (
          title, description, status, priority, assigned_to,
          created_date, due_date, project, tags, notes
        ) VALUES (?, ?, 'Not Started', 'Medium', 'Nick', ?, NULL, ?, ?, ?)
        """,
        (
            title,
            'Auto-captured from Telegram actionable message.',
            date.today().isoformat(),
            'Ebook Distribution',
            'telegram,auto-capture',
            f'Auto-source: {source_key}',
        ),
    )
    conn.commit()


def main():
    token = load_token()
    state = load_state()
    offset = int(state.get('offset', 0))
    processed = set(state.get('processed', []))

    params = {'timeout': 1, 'allowed_updates': json.dumps(['message'])}
    if offset > 0:
        params['offset'] = offset

    updates = tg_post(token, 'getUpdates', params)

    max_offset = offset
    created = 0
    conn = sqlite3.connect(str(DB))

    try:
        for u in updates:
            upd_id = int(u.get('update_id', 0))
            if upd_id >= max_offset:
                max_offset = upd_id + 1

            msg = u.get('message') or {}
            chat_id = str((msg.get('chat') or {}).get('id', ''))
            if chat_id != TARGET_CHAT:
                continue

            text = (msg.get('text') or msg.get('caption') or '').strip()
            msg_id = str(msg.get('message_id', ''))
            source_key = f"telegram:{chat_id}:{msg_id}"

            if not text or source_key in processed:
                continue
            if not is_actionable(text):
                processed.add(source_key)
                continue
            if task_exists(conn, source_key):
                processed.add(source_key)
                continue

            create_task(conn, normalize_title(text), source_key)
            processed.add(source_key)
            created += 1

    finally:
        conn.close()

    state['offset'] = max_offset
    state['processed'] = list(processed)
    save_state(state)
    print(f'Auto-task sync complete. created={created}')


if __name__ == '__main__':
    main()
