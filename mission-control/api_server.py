#!/usr/bin/env python3
"""
CivicOS Mission Control - Full Backend API
Serves dashboard with real-time data and automated scanning
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import sqlite3
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Thread
import time
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for Tailscale access

ROOT = Path('/app') if os.path.exists('/app') else Path('.')
DATA_DIR = ROOT / 'data'
DB_DIR = ROOT / 'data'  # Database is in data directory
WORKSPACE_DIR = ROOT.parent if ROOT.name == 'mission-control' else Path('/Users/AI-OPS/.openclaw/workspace')
MC_SCRIPTS_DIR = WORKSPACE_DIR / 'scripts' / 'mc'

def get_db_connection(db_name='finance.db'):
    """Get database connection."""
    db_path = DB_DIR / db_name
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    return None


def run_script(script_name: str, timeout: int = 180):
    script = MC_SCRIPTS_DIR / script_name
    if not script.exists():
        return {'status': 'error', 'message': f'Script not found: {script}'}
    try:
        proc = subprocess.run([str(script)], capture_output=True, text=True, timeout=timeout, cwd=str(WORKSPACE_DIR))
        return {
            'status': 'success' if proc.returncode == 0 else 'error',
            'returncode': proc.returncode,
            'stdout': (proc.stdout or '')[-12000:],
            'stderr': (proc.stderr or '')[-6000:]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def read_router_status():
    f = DATA_DIR / 'router-status.json'
    if f.exists():
        try:
            j = json.loads(f.read_text())
            return j
        except Exception:
            return {}
    return {}


def _json_list(path: Path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_json_list(path: Path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2))

@app.route('/')
def index():
    """Serve main dashboard."""
    return send_from_directory(ROOT, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory(ROOT, path)

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/finance/status')
def finance_status():
    """Get complete finance status."""
    try:
        conn = get_db_connection('finance.db')
        if not conn:
            return jsonify({"error": "Database not found"}), 404
        
        cur = conn.cursor()
        today = datetime.now().date()
        start = today.replace(day=1).isoformat()
        end = today.replace(year=today.year + (1 if today.month == 12 else 0), 
                           month=(1 if today.month == 12 else today.month + 1), 
                           day=1).isoformat()
        
        # Monthly totals
        income = cur.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date>=? AND date<?",
            (start, end)
        ).fetchone()[0]
        
        expenses = cur.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND date>=? AND date<?",
            (start, end)
        ).fetchone()[0]
        
        # Recent transactions
        tx = [dict(r) for r in cur.execute("""
            SELECT t.date, t.description, t.amount, t.type, t.vendor, c.name as category_name
            FROM transactions t LEFT JOIN categories c ON c.id=t.category_id
            ORDER BY t.date DESC, t.id DESC LIMIT 25
        """).fetchall()]
        
        # Unpaid invoices
        inv_list = [dict(r) for r in cur.execute("""
            SELECT id, invoice_number, vendor, amount, due_date, status 
            FROM invoices 
            WHERE status IN ('unpaid','overdue') 
            ORDER BY CASE status WHEN 'overdue' THEN 0 ELSE 1 END, due_date ASC 
            LIMIT 25
        """).fetchall()]
        
        unpaid_count = len(inv_list)
        unpaid_total = sum(r.get('amount', 0) for r in inv_list)
        overdue_count = sum(1 for r in inv_list if r.get('status') == 'overdue')
        
        conn.close()
        
        return jsonify({
            "monthly": {
                "income": float(income or 0),
                "expenses": float(expenses or 0),
                "net": float((income or 0) - (expenses or 0)),
                "period": f"{today.year}-{today.month:02d}"
            },
            "invoices": {
                "unpaid_count": unpaid_count,
                "unpaid_total": unpaid_total,
                "overdue_count": overdue_count,
                "list": inv_list
            },
            "transactions": tx,
            "updatedAt": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/finance/entries')
def finance_entries():
    """Get all finance entries for Command Center."""
    return finance_status()

@app.route('/api/invoices/scan', methods=['POST'])
def scan_invoices():
    """Trigger invoice scan."""
    try:
        result = subprocess.run(
            ['python3', str(ROOT / 'scripts' / 'invoice_scanner.py')],
            capture_output=True, text=True, timeout=120
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.stderr else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoices/<int:inv_id>/pay', methods=['POST'])
def mark_invoice_paid(inv_id):
    """Mark invoice as paid."""
    try:
        conn = get_db_connection('finance.db')
        if not conn:
            return jsonify({"error": "Database not found"}), 404
        
        cur = conn.cursor()
        cur.execute("UPDATE invoices SET status='paid', paid_date=? WHERE id=?",
                   (datetime.now().date().isoformat(), inv_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"Invoice {inv_id} marked as paid"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """Add manual transaction."""
    try:
        data = request.json
        conn = get_db_connection('finance.db')
        if not conn:
            return jsonify({"error": "Database not found"}), 404
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (date, description, amount, type, vendor, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('date', datetime.now().date().isoformat()),
            data.get('description', ''),
            data.get('amount', 0),
            data.get('type', 'expense'),
            data.get('vendor', ''),
            data.get('payment_method', 'manual')
        ))
        conn.commit()
        tx_id = cur.lastrowid
        conn.close()
        
        return jsonify({"success": True, "id": tx_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/router/status')
def router_status():
    """Get router status."""
    try:
        rs = read_router_status()
        return jsonify(rs if rs else {"status": "unknown"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sysadmin/status')
def sysadmin_status():
    """Return system admin readouts for C&C panel."""
    out = {
        'gateway_status': 'Unknown',
        'gateway_uptime': 'Unknown',
        'main_model': 'Unknown',
        'router_first': 'Unknown',
        'fallback_model': 'Unknown',
        'codex_readout': 'N/A',
        'codex_notes': 'No explicit quota telemetry'
    }

    try:
        g = subprocess.run(['openclaw', 'gateway', 'status'], capture_output=True, text=True, timeout=20)
        txt = (g.stdout or '') + '\n' + (g.stderr or '')
        m = re.search(r'Gateway\s*status\s*:\s*(\w+)', txt, re.IGNORECASE)
        if m:
            out['gateway_status'] = m.group(1).capitalize()
        up = re.search(r'Uptime\s*:\s*([^\n]+)', txt, re.IGNORECASE)
        if up:
            out['gateway_uptime'] = up.group(1).strip()
    except Exception:
        pass

    try:
        cfg = json.loads((Path('/Users/AI-OPS/.openclaw/openclaw.json')).read_text())
        model = cfg.get('agents', {}).get('defaults', {}).get('model', {}).get('primary')
        if model:
            out['main_model'] = model
    except Exception:
        pass

    rs = read_router_status()
    if rs:
        out['router_first'] = 'ON' if rs.get('routerFirst') else 'OFF'
        out['fallback_model'] = rs.get('fallbackModel') or rs.get('fallbackModelId') or 'Unknown'

    try:
        ss = subprocess.run(['openclaw', 'status'], capture_output=True, text=True, timeout=25)
        st = (ss.stdout or '')
        line = ''
        for ln in st.splitlines():
            if 'Model:' in ln or 'model=' in ln.lower():
                line = ln.strip()
                break
        if line:
            out['codex_readout'] = line[:140]
            out['codex_notes'] = 'Session status snapshot'
    except Exception:
        pass

    return jsonify(out)


@app.route('/api/sysadmin/reset-gateway', methods=['POST'])
def sysadmin_reset_gateway():
    res = run_script('reset_gateway.sh', timeout=120)
    code = 200 if res.get('status') == 'success' else 500
    return jsonify(res), code


@app.route('/api/sysadmin/openclaw-doctor', methods=['POST'])
def sysadmin_openclaw_doctor():
    res = run_script('openclaw_doctor.sh', timeout=240)
    code = 200 if res.get('status') == 'success' else 500
    return jsonify(res), code

@app.route('/api/hours', methods=['GET', 'POST'])
def api_hours():
    p = DATA_DIR / 'hours_entries.json'
    if request.method == 'GET':
        items = _json_list(p)
        return jsonify({'items': items})

    data = request.json or {}
    item = {
        'id': int(time.time() * 1000),
        'date': data.get('date', datetime.now().date().isoformat()),
        'hours': float(data.get('hours', 0) or 0),
        'type': (data.get('type') or 'volunteer').lower(),
        'category': data.get('category', 'Other'),
        'description': data.get('description', ''),
        'created': datetime.now().isoformat()
    }
    items = _json_list(p)
    items.append(item)
    _save_json_list(p, items)
    return jsonify({'ok': True, 'item': item})


@app.route('/api/hours/<int:item_id>', methods=['PUT', 'DELETE'])
def api_hours_item(item_id):
    p = DATA_DIR / 'hours_entries.json'
    items = _json_list(p)
    if request.method == 'DELETE':
        items = [x for x in items if int(x.get('id', 0)) != item_id]
        _save_json_list(p, items)
        return jsonify({'ok': True})

    data = request.json or {}
    for i, x in enumerate(items):
        if int(x.get('id', 0)) == item_id:
            x.update({
                'date': data.get('date', x.get('date')),
                'hours': float(data.get('hours', x.get('hours', 0)) or 0),
                'type': (data.get('type', x.get('type', 'volunteer')) or 'volunteer').lower(),
                'category': data.get('category', x.get('category', 'Other')),
                'description': data.get('description', x.get('description', '')),
            })
            items[i] = x
            _save_json_list(p, items)
            return jsonify({'ok': True, 'item': x})
    return jsonify({'ok': False, 'error': 'not found'}), 404


@app.route('/api/expenses-lite', methods=['GET', 'POST'])
def api_expenses_lite():
    p = DATA_DIR / 'expenses_entries.json'
    if request.method == 'GET':
        return jsonify({'items': _json_list(p)})

    data = request.json or {}
    item = {
        'id': int(time.time() * 1000),
        'date': data.get('date', datetime.now().date().isoformat()),
        'amount': float(data.get('amount', 0) or 0),
        'category': data.get('category', 'Other'),
        'vendor': data.get('vendor', ''),
        'description': data.get('description', ''),
        'created': datetime.now().isoformat()
    }
    items = _json_list(p)
    items.append(item)
    _save_json_list(p, items)
    return jsonify({'ok': True, 'item': item})


@app.route('/api/expenses-lite/<int:item_id>', methods=['DELETE'])
def api_expenses_lite_item(item_id):
    p = DATA_DIR / 'expenses_entries.json'
    items = _json_list(p)
    items = [x for x in items if int(x.get('id', 0)) != item_id]
    _save_json_list(p, items)
    return jsonify({'ok': True})


@app.route('/api/council/index')
def council_index():
    """Get council index."""
    try:
        council_file = DATA_DIR / 'council-index.json'
        if council_file.exists():
            return jsonify(json.loads(council_file.read_text()))
        return jsonify({"sessions": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def auto_scan_loop():
    """Background thread for automatic invoice scanning."""
    while True:
        try:
            print(f"[{datetime.now()}] Running automatic invoice scan...")
            subprocess.run(
                ['python3', str(ROOT / 'scripts' / 'invoice_scanner.py')],
                capture_output=True, timeout=120
            )
            # Update finance status export
            subprocess.run(
                ['python3', str(ROOT / 'scripts' / 'export_finance_status.py')],
                capture_output=True, timeout=30
            )
            print(f"[{datetime.now()}] Auto-scan complete")
        except Exception as e:
            print(f"[{datetime.now()}] Auto-scan error: {e}")
        
        # Sleep for 15 minutes
        time.sleep(900)

if __name__ == '__main__':
    # Start auto-scan thread
    scan_thread = Thread(target=auto_scan_loop, daemon=True)
    scan_thread.start()
    
    port = int(os.environ.get('PORT', 8765))
    print(f"🚀 CivicOS Mission Control API starting on port {port}")
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"🔍 Auto-scan: Every 15 minutes")
    
    app.run(host='0.0.0.0', port=port, threaded=True)
