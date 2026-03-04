#!/usr/bin/env python3
from flask import Flask, render_template, request, abort
from flask_cors import CORS
from pathlib import Path
import json, sqlite3, os
from datetime import datetime

app = Flask(__name__)
CORS(app)

ROOT = Path('/app') if Path('/app').exists() else Path(__file__).parent
DATA = ROOT / 'data'

ROLE_KEYS = {
    'provisional': os.getenv('BOARD_KEY_PROVISIONAL', 'provisional-demo-key'),
    'advisory': os.getenv('BOARD_KEY_ADVISORY', 'advisory-demo-key'),
    'board': os.getenv('BOARD_KEY_BOARD', 'board-demo-key'),
}

ROLE_PERMS = {
    'provisional': {'finance': 'summary', 'grants': 'summary', 'news': True, 'incidents': False},
    'advisory': {'finance': 'standard', 'grants': 'standard', 'news': True, 'incidents': True},
    'board': {'finance': 'full', 'grants': 'full', 'news': True, 'incidents': True},
}

def auth_role():
    role = request.args.get('role', '').lower()
    key = request.args.get('key', '')
    if role in ROLE_KEYS and key and key == ROLE_KEYS[role]:
        return role
    return None

def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def finance_snapshot():
    j = read_json(DATA / 'finance-status.json', {})
    monthly = j.get('monthly', {})
    invoices = j.get('invoices', {})
    return {
        'income': float(monthly.get('income', 0) or 0),
        'expenses': float(monthly.get('expenses', 0) or 0),
        'net': float(monthly.get('net', 0) or 0),
        'unpaid_count': int(invoices.get('unpaid_count', 0) or 0),
        'unpaid_total': float(invoices.get('unpaid_total', 0) or 0),
        'updated': j.get('updatedAt')
    }

def grants_snapshot():
    latest = Path('/app/generated/grants/grant-scan-latest.md') if Path('/app/generated/grants/grant-scan-latest.md').exists() else Path('/Users/AI-OPS/.openclaw/workspace/generated/grants/grant-scan-latest.md')
    if latest.exists():
        text = latest.read_text(errors='ignore')
        lines = [l.strip('- ').strip() for l in text.splitlines() if l.strip().startswith('- ')]
        return lines[:12]
    return []

def news_items():
    p = Path('/app/website-news/news.json') if Path('/app/website-news/news.json').exists() else Path('/Users/AI-OPS/.openclaw/workspace/website-news/news.json')
    j = read_json(p, {'news': []})
    items = j.get('news', [])
    return items[:10]

def incidents():
    p = DATA / 'scan-status.json'
    j = read_json(p, {})
    return [j] if j else []

@app.route('/')
def home():
    role = auth_role()
    if not role:
        abort(401)
    perms = ROLE_PERMS[role]
    return render_template(
        'index.html',
        role=role,
        perms=perms,
        finance=finance_snapshot(),
        grants=grants_snapshot(),
        news=news_items(),
        incidents=incidents(),
        now=datetime.now().isoformat(timespec='seconds')
    )

@app.route('/health')
def health():
    return {'status':'ok','time':datetime.now().isoformat()}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','8788')))
