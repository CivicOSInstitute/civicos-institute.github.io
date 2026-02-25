#!/usr/bin/env python3
"""Scan session transcripts for high-signal keywords and append structured hit logs."""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path('/Users/AI-OPS/.openclaw')
WS = Path('/Users/AI-OPS/.openclaw/workspace')
OUT = WS / 'generated' / 'transcript_keyword_hits.jsonl'
STATE = WS / 'generated' / 'transcript_keyword_scan_state.json'

KEYWORDS = {
    'priority': [
        'deadline', 'urgent', 'asap', 'legal', 'contract', 'invoice', 'payment',
        'grant', 'board', 'compliance', 'risk', 'security', 'incident', 'commitment'
    ],
    'operational': [
        'cron', 'queue', 'fallback', 'model', 'codex', 'ollama', 'token', 'quota', 'limit'
    ],
}

TRANSCRIPT_GLOB = ROOT / 'agents' / '*' / 'sessions' / '*' / '*.jsonl'


def load_state():
    if not STATE.exists():
        return {'seen': {}}
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {'seen': {}}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))


def iter_transcripts():
    for p in ROOT.glob('agents/*/sessions/*/*.jsonl'):
        # Skip extremely old archives by mtime (optional safeguard)
        if datetime.fromtimestamp(p.stat().st_mtime) < datetime.now() - timedelta(days=90):
            continue
        yield p


def line_matches(text):
    text_l = text.lower()
    found = []
    for bucket, words in KEYWORDS.items():
        for w in words:
            if re.search(rf'\b{re.escape(w)}\b', text_l):
                found.append({'bucket': bucket, 'keyword': w})
    return found


def main():
    state = load_state()
    seen = state.get('seen', {})
    OUT.parent.mkdir(parents=True, exist_ok=True)

    new_hits = 0
    with OUT.open('a') as out:
        for p in iter_transcripts():
            key = str(p)
            last_line = int(seen.get(key, 0))
            try:
                lines = p.read_text(errors='ignore').splitlines()
            except Exception:
                continue

            for idx, line in enumerate(lines[last_line:], start=last_line + 1):
                m = line_matches(line)
                if not m:
                    continue
                record = {
                    'ts': datetime.now().astimezone().isoformat(timespec='seconds'),
                    'file': key,
                    'line': idx,
                    'matches': m,
                    'preview': line[:300],
                }
                out.write(json.dumps(record) + '\n')
                new_hits += 1

            seen[key] = len(lines)

    state['seen'] = seen
    state['last_run'] = datetime.now().astimezone().isoformat(timespec='seconds')
    state['last_new_hits'] = new_hits
    save_state(state)
    print(f'new_hits={new_hits}')


if __name__ == '__main__':
    main()
