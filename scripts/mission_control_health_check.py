#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
OUT = BASE / 'generated' / 'mission_control_health_latest.json'
OUT.parent.mkdir(parents=True, exist_ok=True)

checks = {
    'ui_home_8765': 'http://localhost:8765/',
    'router_status_file': 'http://localhost:8765/data/router-status.json',
    'router_last10_api': 'http://localhost:8876/api/router/last10',
    'finance_entries_api': 'http://localhost:8876/api/finance/entries',
    'news_categories_api': 'http://localhost:8877/api/news/categories',
}

result = {
    'timestamp': datetime.now().isoformat(timespec='seconds'),
    'ok': True,
    'checks': {}
}

for name, url in checks.items():
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            status = r.getcode()
            body = r.read(200).decode('utf-8', errors='ignore')
            ok = 200 <= status < 300
            result['checks'][name] = {'ok': ok, 'status': status, 'url': url, 'preview': body[:120]}
            if not ok:
                result['ok'] = False
    except Exception as e:
        result['checks'][name] = {'ok': False, 'status': None, 'url': url, 'error': str(e)}
        result['ok'] = False

OUT.write_text(json.dumps(result, indent=2))
print(json.dumps({'ok': result['ok'], 'output': str(OUT)}))
raise SystemExit(0 if result['ok'] else 1)
