#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import subprocess
import json

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'finance.db'
ATTACH = ROOT / 'data' / 'attachments'
ATTACH.mkdir(parents=True, exist_ok=True)
SCAN_STATUS = ROOT / 'data' / 'scan-status.json'

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp', '.pdf'}

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return resp


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_category(conn, name, type_):
    row = conn.execute("SELECT id FROM categories WHERE lower(name)=lower(?) LIMIT 1", (name,)).fetchone()
    if row:
        return row['id']
    cur = conn.execute("INSERT INTO categories(name,type,description) VALUES(?,?,?)", (name, type_, 'manual entry'))
    return cur.lastrowid


@app.get('/api/finance/entries')
def list_entries():
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.id,t.date,t.description,t.amount,t.type,t.vendor,t.notes,t.receipt_path,
               c.name as category_name
        FROM transactions t
        LEFT JOIN categories c ON c.id=t.category_id
        ORDER BY t.date DESC, t.id DESC
        LIMIT 100
    """).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        if d.get('receipt_path'):
            d['attachment_url'] = f"http://localhost:8876/api/finance/attachment/{Path(d['receipt_path']).name}"
        items.append(d)
    return jsonify({"items": items})


@app.route('/api/finance/manual-entry', methods=['POST', 'OPTIONS'])
def manual_entry():
    if request.method == 'OPTIONS':
        return ('', 204)
    form = request.form
    date = form.get('date')
    type_ = form.get('type', 'expense')
    amount = float(form.get('amount', '0') or 0)
    category = form.get('category', 'Other')
    vendor = form.get('vendor', '')
    description = form.get('description', '')
    notes = form.get('notes', '')

    if not date or type_ not in ('income', 'expense') or amount < 0 or not description:
        return ('invalid payload', 400)

    receipt_path = None
    f = request.files.get('attachment')
    if f and f.filename:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            return ('invalid attachment type', 400)
        fname = secure_filename(f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{f.filename}")
        out = ATTACH / fname
        f.save(out)
        receipt_path = str(out)

    conn = get_conn()
    cat_id = ensure_category(conn, category, type_)
    cur = conn.execute(
        """INSERT INTO transactions(date,description,amount,type,category_id,vendor,notes,receipt_path)
           VALUES(?,?,?,?,?,?,?,?)""",
        (date, description, amount, type_, cat_id, vendor, notes, receipt_path)
    )
    conn.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})


@app.get('/api/finance/attachment/<name>')
def attachment(name):
    return send_from_directory(ATTACH, name, as_attachment=False)


@app.post('/api/finance/scan-email')
def scan_email_start():
    try:
        SCAN_STATUS.write_text(json.dumps({"state": "starting", "current": "launching scanner", "progress": 0}))
        logf = open(ROOT / 'scan_email.log', 'a')
        proc = subprocess.Popen([
            str(ROOT / '.venv' / 'bin' / 'python') if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3',
            str(ROOT / 'scripts' / 'invoice_scanner.py')
        ], cwd=str(ROOT), stdout=logf, stderr=logf)
        return jsonify({"ok": True, "pid": proc.pid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get('/api/finance/scan-status')
def scan_status():
    if SCAN_STATUS.exists():
        try:
            return jsonify(json.loads(SCAN_STATUS.read_text()))
        except Exception:
            pass
    return jsonify({"state": "idle", "current": "Scan idle", "progress": 0})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8876, debug=False)
