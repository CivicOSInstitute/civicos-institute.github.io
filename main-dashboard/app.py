#!/usr/bin/env python3
"""
CivicOS Main Command Center Dashboard
Aggregates data from all sub-systems
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, date
import csv
from pathlib import Path
import urllib.request
import urllib.error
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Service URLs
SERVICES = {
    'task_tracker': {'url': 'http://localhost:8082', 'port': 8082},
    'crm': {'url': 'http://localhost:8083', 'port': 8083},
    'token_tracker': {'url': 'http://localhost:8081', 'port': 8081},
    'website': {'url': 'https://civicos-institute.org', 'external': True},
    'news_widget': {'url': 'http://localhost:8080', 'port': 8080},
    'searxng': {'url': 'http://100.81.239.69:8080', 'external': True}
}


def get_dashboard_registry():
    """Single source of truth for dashboard/navigation cards shown in Command Center."""
    return {
        'operations': [
            {'name': 'Task Tracker', 'url': 'http://100.81.239.69:8082', 'desc': 'Execution queue and owners'},
            {'name': 'CRM', 'url': 'http://100.81.239.69:8083', 'desc': 'Contacts and relationship pipeline'},
            {'name': 'Token Tracker', 'url': 'http://100.81.239.69:8081', 'desc': 'Model usage and budget controls'},
            {'name': 'Publishing Ops', 'url': '/publishing-ops', 'desc': 'Amazon/Apple channel readiness'},
            {'name': 'Finance', 'url': '/finance', 'desc': 'Revenue, expenses, and net'},
        ],
        'youtube': [
            {'name': 'YouTube Content Studio (Future CivicOS)', 'url': '/youtube/content-studio', 'desc': 'Our planned/published content workflow'},
            {'name': 'YouTube Channel Monitor', 'url': '/youtube/channel-monitor', 'desc': 'Tracked channels + summary feed'},
        ],
        'external': [
            {'name': 'Website', 'url': 'https://civicos-institute.org', 'desc': 'Public web presence'},
            {'name': 'News Feed', 'url': 'https://civicos-institute.org/news', 'desc': 'Public updates and widget'},
            {'name': 'SearXNG', 'url': 'http://100.81.239.69:8080', 'desc': 'Private search'}
        ]
    }


def get_integrity_status():
    """Non-breaking guardrail: verify legacy command center dependencies are still available."""
    checks = {
        'task_db': (OPENCLAW_DIR / 'task-tracker' / 'tasks.db').exists(),
        'crm_db': (OPENCLAW_DIR / 'civic-crm' / 'crm.db').exists(),
        'token_log': (OPENCLAW_DIR / 'token-tracker' / 'token_log.jsonl').exists(),
        'revenue_csv': REVENUE_CSV.exists(),
        'expenses_csv': EXPENSES_CSV.exists(),
        'youtube_monitor': (WORKSPACE_DIR / 'generated' / 'youtube_dashboard' / 'videos.json').exists(),
        'ebook_pipeline': (EBOOK_SCRIPTS / 'run_all.sh').exists(),
    }

    # Bridge reachability (telegram/email/gateway API dependency)
    try:
        urllib.request.urlopen('http://host.docker.internal:18080/gateway/status', timeout=4)
        checks['host_bridge'] = True
    except Exception:
        checks['host_bridge'] = False

    total = len(checks)
    ok = sum(1 for v in checks.values() if v)
    return {
        'checks': checks,
        'ok': ok,
        'total': total,
        'score': round((ok / total) * 100) if total else 0
    }

HOME_DIR = Path.home()
OPENCLAW_DIR = HOME_DIR / '.openclaw'
WORKSPACE_DIR = OPENCLAW_DIR / 'workspace'

EBOOK_SCRIPTS = WORKSPACE_DIR / 'the_open_source_student_distribution' / 'scripts'
EBOOK_OUTPUT = HOME_DIR / 'Desktop' / 'the_open_source_student' / 'launch-output'
REVENUE_CSV = WORKSPACE_DIR / 'civicos-revenue-tracker.csv'
EXPENSES_CSV = WORKSPACE_DIR / 'civicos-financial-tracker.csv'
DIST_METRICS_JSON = WORKSPACE_DIR / 'the_open_source_student_distribution' / 'output' / 'distribution_metrics.json'
YT_SKILL_DIR = WORKSPACE_DIR / 'skills' / 'youtube-summarizer'
YT_ARTIFACTS_DIR = YT_SKILL_DIR / 'artifacts'
BROWSER_SKILL_DIR = WORKSPACE_DIR / 'skills' / 'browser-automation'
COUNCIL_DATA_DIR = WORKSPACE_DIR / 'data' / 'council'
COUNCIL_ISSUES_DIR = COUNCIL_DATA_DIR / 'issues'
COUNCIL_SESSIONS_DIR = COUNCIL_DATA_DIR
COUNCIL_ISSUES_DIR.mkdir(parents=True, exist_ok=True)

def check_service(name, config):
    """Check if a service is online."""
    try:
        if config.get('external'):
            response = urllib.request.urlopen(config['url'], timeout=5)
            return 'online' if response.status == 200 else 'offline'
        else:
            response = urllib.request.urlopen(config['url'], timeout=2)
            return 'online' if response.status == 200 else 'offline'
    except:
        return 'offline'

def get_task_stats():
    """Get task statistics from task tracker DB."""
    try:
        db_path = OPENCLAW_DIR / 'task-tracker' / 'tasks.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT status, COUNT(*) FROM task GROUP BY status")
        stats = dict(cursor.fetchall())
        conn.close()
        
        return {
            'total': sum(stats.values()),
            'in_progress': stats.get('In Progress', 0),
            'blocked': stats.get('Blocked', 0),
            'completed': stats.get('Completed', 0),
            'not_started': stats.get('Not Started', 0)
        }
    except Exception as e:
        print(f"Error getting task stats: {e}")
        return {}

def get_crm_stats():
    """Get CRM statistics."""
    try:
        db_path = OPENCLAW_DIR / 'civic-crm' / 'crm.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contact")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE engagement_level IN ('Hot', 'Very Hot')")
        hot = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE contact_type = 'Board Candidate'")
        board = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE contact_type = 'Foundation Contact'")
        foundation = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'hot': hot,
            'board': board,
            'foundation': foundation
        }
    except Exception as e:
        print(f"Error getting CRM stats: {e}")
        return {}

def get_token_stats():
    """Get token usage statistics from token-tracker JSONL (current setup)."""
    from datetime import timedelta, timezone

    log_path = OPENCLAW_DIR / 'token-tracker' / 'token_log.jsonl'
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    stats = {
        'today': 0.0,
        'week': 0.0,
        'month': 0.0,
        'apis': 0,
        'local_calls': 0,
        'api_calls': 0,
        'total_calls': 0,
        'local_share': 0,
        'top_model': 'n/a',
        'policy': 'Local-first',
        'codex_5h_remaining': None,
        'codex_daily_remaining': None,
        'codex_mode': 'unavailable'
    }

    try:
        if not log_path.exists():
            return stats

        providers_api = set()
        model_counts = {}

        for line in log_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue

            # timestamp parsing
            ts_raw = rec.get('timestamp') or rec.get('ts')
            ts = None
            if ts_raw:
                try:
                    ts = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except Exception:
                    ts = None
            if ts is None:
                ts = now

            cost = rec.get('cost_usd', rec.get('cost', 0)) or 0
            try:
                cost = float(cost)
            except Exception:
                cost = 0.0

            provider = str(rec.get('provider', 'unknown')).lower()
            model = str(rec.get('model', 'unknown'))

            stats['total_calls'] += 1
            if provider in ('ollama', 'local'):
                stats['local_calls'] += 1
            else:
                stats['api_calls'] += 1
                providers_api.add(provider)

            model_counts[model] = model_counts.get(model, 0) + 1

            if ts >= day_ago:
                stats['today'] += cost
            if ts >= week_ago:
                stats['week'] += cost
            if ts >= month_ago:
                stats['month'] += cost

        stats['apis'] = len(providers_api)
        if stats['total_calls'] > 0:
            stats['local_share'] = round((stats['local_calls'] / stats['total_calls']) * 100)
        if model_counts:
            stats['top_model'] = max(model_counts, key=model_counts.get)

        stats['today'] = round(stats['today'], 2)
        stats['week'] = round(stats['week'], 2)
        stats['month'] = round(stats['month'], 2)

        # Codex 5h/daily remaining from host bridge (estimated from sessions)
        try:
            bridge_url = 'http://host.docker.internal:18080/codex/usage'
            with urllib.request.urlopen(bridge_url, timeout=8) as r:
                cu = json.loads(r.read().decode('utf-8'))
            if cu.get('status') == 'success':
                stats['codex_5h_remaining'] = cu.get('five_hour', {}).get('remaining_pct')
                stats['codex_daily_remaining'] = cu.get('daily', {}).get('remaining_pct')
                stats['codex_mode'] = cu.get('mode', 'estimated')
        except Exception:
            pass

        return stats

    except Exception as e:
        print(f"Error getting token stats: {e}")
        return stats

def get_council_stats():
    """Get advisory council stats from latest report."""
    try:
        reports_dir = OPENCLAW_DIR / 'advisory-council' / 'reports'
        if not reports_dir.exists():
            return {}
        
        # Get most recent report
        reports = sorted(reports_dir.glob("council_report_*.txt"), reverse=True)
        if not reports:
            return {}
        
        latest = reports[0]
        with open(latest) as f:
            content = f.read()
        
        # Parse counts
        critical = content.count('🚨') + content.count('CRITICAL')
        important = content.count('⚠️') + content.count('IMPORTANT')
        info = content.count('ℹ️') + content.count('INFORMATIONAL')
        
        # Get date from filename
        date_str = latest.stem.replace('council_report_', '')
        
        return {
            'critical': critical,
            'important': important,
            'info': info,
            'last_run': date_str
        }
    except Exception as e:
        print(f"Error getting council stats: {e}")
        return {}

def get_council_issues(limit=20):
    """Load queued council issues (pre-council summaries)."""
    issues = []
    try:
        files = sorted(COUNCIL_ISSUES_DIR.glob('*.json'), reverse=True)
        for f in files[:limit]:
            try:
                issues.append(json.loads(f.read_text()))
            except Exception:
                continue
    except Exception as e:
        print(f"Error loading council issues: {e}")
    return issues


def create_council_issue(topic, context):
    """Create council issue intake record for dashboard visibility and later retrieval."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    slug = ''.join(c if c.isalnum() else '-' for c in (topic or 'untitled').lower()).strip('-')[:60] or 'untitled'
    issue_id = f"council-{ts}-{slug[:24]}"
    summary = (context or '').strip().replace('\n', ' ')
    if len(summary) > 280:
        summary = summary[:277] + '...'

    payload = {
        'id': issue_id,
        'topic': topic,
        'context': context,
        'pre_council_summary': summary,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'status': 'queued'
    }
    out = COUNCIL_ISSUES_DIR / f"{issue_id}.json"
    out.write_text(json.dumps(payload, indent=2))
    return payload


def get_recent_activity():
    """Get recent activity from logs and databases."""
    activities = []
    
    # Recent CRM contacts
    try:
        db_path = OPENCLAW_DIR / 'civic-crm' / 'crm.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, contact_type, created_date 
            FROM contact 
            ORDER BY created_date DESC LIMIT 5
        """)
        for row in cursor.fetchall():
            activities.append({
                'message': f"Added {row[0]} ({row[1]})",
                'time': row[2]
            })
        conn.close()
    except:
        pass
    
    return activities

def get_gateway_stats():
    """Get OpenClaw Gateway statistics via host bridge API."""
    stats = {
        'version': 'OpenClaw',
        'uptime': 'Unknown',
        'status': 'Unknown',
        'raw': ''
    }
    try:
        bridge_url = 'http://host.docker.internal:18080/gateway/status'
        response = urllib.request.urlopen(bridge_url, timeout=10)
        result = json.loads(response.read().decode('utf-8'))

        if result.get('status') == 'success':
            g = (result.get('gateway_status') or 'unknown').lower()
            if g == 'running':
                stats['status'] = 'Running'
            elif g == 'stopped':
                stats['status'] = 'Stopped'
            else:
                stats['status'] = 'Unknown'
            stats['raw'] = result.get('raw', '')
        return stats
    except Exception as e:
        print(f"Error getting gateway stats: {e}")
        return stats

def get_email_stats():
    """Get email statistics from Himalaya via bridge API."""
    try:
        def check_account(account):
            bridge_url = 'http://host.docker.internal:18080/email/check'
            payload = {
                'account': account
            }
            
            req = urllib.request.Request(
                bridge_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            response = urllib.request.urlopen(req, timeout=15)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('status') == 'success':
                return result.get('unread', 0)
            return 0
        
        nick_unread = check_account('nick')
        burt_unread = check_account('burt')
        
        return {
            'nick_unread': nick_unread,
            'burt_unread': burt_unread,
            'unread': nick_unread + burt_unread
        }
    except Exception as e:
        print(f"Error getting email stats: {e}")
        return {
            'nick_unread': 0,
            'burt_unread': 0,
            'unread': 0
        }

def get_ebook_stats():
    """Get ebook distribution automation stats."""
    try:
        latest_dir = None
        if EBOOK_OUTPUT.exists():
            candidates = [
                p for p in EBOOK_OUTPUT.iterdir()
                if p.is_dir() and p.name[:8].isdigit() and '-' in p.name
            ]
            if candidates:
                latest_dir = sorted(candidates, key=lambda p: p.name, reverse=True)[0]

        def file_size(path):
            return round(path.stat().st_size / 1024, 1) if path.exists() else 0

        data = {
            'pipeline_ready': (EBOOK_SCRIPTS / 'run_all.sh').exists(),
            'latest_build': latest_dir.name if latest_dir else 'None',
            'core_zip_kb': file_size(latest_dir / 'core.zip') if latest_dir else 0,
            'founder_zip_kb': file_size(latest_dir / 'founder.zip') if latest_dir else 0,
            'institution_zip_kb': file_size(latest_dir / 'institution.zip') if latest_dir else 0,
            'checkout_copy': (EBOOK_OUTPUT / 'checkout-copy.md').exists(),
            'launch_content': (EBOOK_OUTPUT / 'launch-content').exists(),
            'output_path': str(latest_dir) if latest_dir else ''
        }
        return data
    except Exception as e:
        print(f"Error getting ebook stats: {e}")
        return {
            'pipeline_ready': False,
            'latest_build': 'Error',
            'core_zip_kb': 0,
            'founder_zip_kb': 0,
            'institution_zip_kb': 0,
            'checkout_copy': False,
            'launch_content': False,
            'output_path': ''
        }

def get_distribution_stats():
    """Get distribution/revenue analytics for ebook operations."""
    stats = {
        'total_revenue': 0.0,
        'units_sold': 0,
        'orders': 0,
        'aov': 0.0,
        'channels': [],
        'last_updated': 'Unknown'
    }

    try:
        if REVENUE_CSV.exists():
            with open(REVENUE_CSV, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    amount_raw = (row.get('Amount') or '0').replace('$', '').replace(',', '').strip()
                    try:
                        amount = float(amount_raw)
                    except Exception:
                        amount = 0.0
                    category = (row.get('Category') or '').strip().lower()
                    if category == 'revenue':
                        stats['total_revenue'] += amount
                        stats['orders'] += 1 if amount > 0 else 0

            if stats['orders'] > 0:
                stats['aov'] = round(stats['total_revenue'] / stats['orders'], 2)

        if DIST_METRICS_JSON.exists():
            extra = json.loads(DIST_METRICS_JSON.read_text())
            stats['units_sold'] = int(extra.get('units_sold', stats['units_sold']))
            stats['channels'] = extra.get('channels', [])
            stats['last_updated'] = extra.get('last_updated', stats['last_updated'])

        stats['total_revenue'] = round(stats['total_revenue'], 2)
        return stats
    except Exception as e:
        print(f"Error getting distribution stats: {e}")
        return stats


def _parse_amount(raw):
    try:
        s = str(raw or '').replace('$', '').replace(',', '').strip()
        return float(s)
    except Exception:
        return None


def get_finance_stats():
    stats = {
        'revenue_total': 0.0,
        'expense_paid_total': 0.0,
        'expense_pending_total': 0.0,
        'payment_failed_total': 0.0,
        'lemon_revenue': 0.0,
        'amazon_revenue': 0.0,
        'apple_revenue': 0.0,
        'net': 0.0,
        'revenue_rows': 0,
        'expense_rows': 0,
    }

    try:
        if REVENUE_CSV.exists():
            with open(REVENUE_CSV, newline='') as f:
                for row in csv.DictReader(f):
                    amount = _parse_amount(row.get('Amount'))
                    if amount is None:
                        continue
                    if (row.get('Category') or '').strip().lower() == 'revenue':
                        stats['revenue_total'] += amount
                        stats['revenue_rows'] += 1

        if EXPENSES_CSV.exists():
            with open(EXPENSES_CSV, newline='') as f:
                for row in csv.DictReader(f):
                    status = (row.get('Status') or '').strip().upper()
                    amount = _parse_amount(row.get('Amount'))
                    if amount is None:
                        continue
                    # ignore non-financial log rows
                    if (row.get('Type') or '').strip().upper() == 'SCAN_LOG':
                        continue

                    stats['expense_rows'] += 1
                    if status == 'PAID':
                        stats['expense_paid_total'] += amount
                    elif status == 'PENDING':
                        stats['expense_pending_total'] += amount
                    elif status == 'PAYMENT_FAILED':
                        stats['payment_failed_total'] += amount

        if DIST_METRICS_JSON.exists():
            dm = json.loads(DIST_METRICS_JSON.read_text())
            for ch in dm.get('channels', []):
                name = (ch.get('name') or '').lower()
                try:
                    rev = float(ch.get('revenue', 0) or 0)
                except Exception:
                    rev = 0.0
                if name.startswith('lemon squeezy'):
                    stats['lemon_revenue'] = rev
                elif name.startswith('amazon kdp'):
                    stats['amazon_revenue'] = rev
                elif name.startswith('apple books'):
                    stats['apple_revenue'] = rev

        for k in ('revenue_total', 'expense_paid_total', 'expense_pending_total', 'payment_failed_total', 'lemon_revenue', 'amazon_revenue', 'apple_revenue'):
            stats[k] = round(stats[k], 2)
        stats['net'] = round(stats['revenue_total'] - stats['expense_paid_total'], 2)
        return stats
    except Exception as e:
        print(f"Error getting finance stats: {e}")
        return stats


def get_battery_stats():
    """Read host battery status (best effort)."""
    import subprocess
    stats = {
        'percent': None,
        'charging': None,
        'source': 'Unknown',
        'status': 'unknown'
    }
    try:
        out = subprocess.check_output(['pmset', '-g', 'batt'], text=True, timeout=5)
        # Example: 'Now drawing from \"AC Power\"' + '85%; charging;'
        if 'AC Power' in out:
            stats['source'] = 'AC'
        elif 'Battery Power' in out:
            stats['source'] = 'Battery'

        import re
        m = re.search(r'(\d+)%', out)
        if m:
            stats['percent'] = int(m.group(1))

        if 'charging' in out.lower() or 'charged' in out.lower() and 'discharging' not in out.lower():
            stats['charging'] = True
        elif 'discharging' in out.lower():
            stats['charging'] = False

        if stats['percent'] is not None:
            if stats['percent'] <= 20:
                stats['status'] = 'low'
            elif stats['percent'] <= 40:
                stats['status'] = 'warning'
            else:
                stats['status'] = 'good'
        return stats
    except Exception as e:
        print(f"Error getting battery stats: {e}")
        return stats


def get_alerts():
    """Generate alerts based on system state."""
    alerts = []
    
    # Check for blocked tasks
    task_stats = get_task_stats()
    if task_stats.get('blocked', 0) > 0:
        alerts.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f"{task_stats['blocked']} blocked tasks need attention"
        })
    
    # Check CRM for follow-ups
    try:
        db_path = OPENCLAW_DIR / 'civic-crm' / 'crm.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute("SELECT COUNT(*) FROM contact WHERE next_follow_up <= ?", (today,))
        followups = cursor.fetchone()[0]
        if followups > 0:
            alerts.append({
                'type': 'warning',
                'icon': '📞',
                'message': f"{followups} follow-ups due today"
            })
        conn.close()
    except:
        pass
    
    return alerts

@app.route('/')
def index():
    """Main dashboard page."""
    # Check all services
    services = {}
    for name, config in SERVICES.items():
        services[name] = {'status': check_service(name, config)}
    
    # Gather stats
    task_stats = get_task_stats()
    crm_stats = get_crm_stats()
    token_stats = get_token_stats()
    council_stats = get_council_stats()
    council_issues = get_council_issues(limit=12)
    recent_activity = get_recent_activity()
    alerts = get_alerts()
    gateway_stats = get_gateway_stats()
    email_stats = get_email_stats()
    ebook_stats = get_ebook_stats()
    distribution_stats = get_distribution_stats()
    finance_stats = get_finance_stats()
    battery_stats = get_battery_stats()
    integrity_status = get_integrity_status()
    epic_mode = os.getenv('COMMAND_CENTER_EPIC_MODE', '1') == '1'
    
    # Calculate grant deadlines
    from datetime import datetime
    knight_deadline = datetime(2026, 3, 1)
    trust_deadline = datetime(2026, 3, 15)
    today = datetime.now()
    grant_deadlines = {
        'knight_days': (knight_deadline - today).days,
        'trust_days': (trust_deadline - today).days
    }
    
    return render_template('index.html',
                         services=services,
                         task_stats=task_stats,
                         crm_stats=crm_stats,
                         token_stats=token_stats,
                         council_stats=council_stats,
                         council_issues=council_issues,
                         website_stats={'last_deploy': 'Unknown'},
                         recent_activity=recent_activity,
                         alerts=alerts,
                         gateway_stats=gateway_stats,
                         email_stats=email_stats,
                         ebook_stats=ebook_stats,
                         distribution_stats=distribution_stats,
                         finance_stats=finance_stats,
                         battery_stats=battery_stats,
                         integrity_status=integrity_status,
                         epic_mode=epic_mode,
                         dashboard_registry=get_dashboard_registry(),
                         grant_deadlines=grant_deadlines,
                         now=datetime.now())

@app.route('/distribution')
def distribution_dashboard():
    """Expanded ebook distribution analytics page."""
    return render_template('distribution.html',
                           dist=get_distribution_stats(),
                           ebook=get_ebook_stats(),
                           finance=get_finance_stats(),
                           now=datetime.now())

def get_publishing_ops_status():
    status_file = WORKSPACE_DIR / 'the_open_source_student_distribution' / 'platforms' / 'PUBLISHING_ACCOUNT_STATUS.json'
    imports_dir = WORKSPACE_DIR / 'the_open_source_student_distribution' / 'output' / 'imports'

    data = {
        'amazon': {'account_status': 'unknown', 'listing_status': 'unknown', 'asin': ''},
        'apple': {'account_status': 'unknown', 'listing_status': 'unknown', 'books_id': ''},
        'imports': {
            'amazon_report': (imports_dir / 'amazon_kdp_report.csv').exists(),
            'apple_report': (imports_dir / 'apple_books_report.csv').exists(),
        },
        'readiness_score': 0
    }

    try:
        if status_file.exists():
            raw = json.loads(status_file.read_text())
            a = raw.get('amazon_kdp', {})
            p = raw.get('apple_books', {})
            data['amazon'] = {
                'account_status': a.get('account_status', 'unknown'),
                'listing_status': a.get('listing_status', 'unknown'),
                'asin': a.get('asin', '')
            }
            data['apple'] = {
                'account_status': p.get('account_status', 'unknown'),
                'listing_status': p.get('listing_status', 'unknown'),
                'books_id': p.get('books_id', '')
            }

        score = 0
        if data['amazon']['account_status'] not in ('unknown', 'pending_owner_completion'): score += 25
        if data['apple']['account_status'] not in ('unknown', 'pending_owner_completion'): score += 25
        if data['imports']['amazon_report']: score += 25
        if data['imports']['apple_report']: score += 25
        data['readiness_score'] = score
        return data
    except Exception:
        return data

@app.route('/finance')
def finance_dashboard():
    """Revenue and expenses dashboard."""
    return render_template('finance.html',
                           finance=get_finance_stats(),
                           dist=get_distribution_stats(),
                           now=datetime.now())

@app.route('/publishing-ops')
def publishing_ops_dashboard():
    """Publishing operations status for Amazon/Apple channels."""
    return render_template('publishing_ops.html',
                           ops=get_publishing_ops_status(),
                           now=datetime.now())

@app.route('/api/distribution/stats')
def api_distribution_stats():
    return jsonify(get_distribution_stats())

@app.route('/api/finance/stats')
def api_finance_stats():
    return jsonify(get_finance_stats())

@app.route('/api/publishing-ops/stats')
def api_publishing_ops_stats():
    return jsonify(get_publishing_ops_status())

@app.route('/api/status')
def api_status():
    """API endpoint for service status."""
    services = {}
    for name, config in SERVICES.items():
        services[name] = {'status': check_service(name, config)}
    return jsonify(services)


@app.route('/api/command-center/integrity')
def api_command_center_integrity():
    """Return legacy-function integrity checks to ensure non-breaking layout migration."""
    return jsonify(get_integrity_status())


@app.route('/youtube/content-studio')
def youtube_content_studio():
    """Future CivicOS YouTube content dashboard scaffold."""
    return render_template('youtube_content_studio.html', now=datetime.now())


@app.route('/youtube/channel-monitor')
def youtube_channel_monitor():
    """Current monitored-channel summaries dashboard scaffold."""
    monitor_root = WORKSPACE_DIR / 'generated' / 'youtube_dashboard'
    summaries = monitor_root / 'summaries'
    videos = monitor_root / 'videos.json'

    items = []
    if summaries.exists():
        for d in sorted(summaries.glob('*'), reverse=True)[:20]:
            if d.is_dir():
                md = d / 'summary.md'
                items.append({
                    'id': d.name,
                    'has_summary': md.exists(),
                    'summary_path': str(md) if md.exists() else ''
                })

    return render_template(
        'youtube_channel_monitor.html',
        now=datetime.now(),
        monitor_root=str(monitor_root),
        videos_json_exists=videos.exists(),
        summary_count=len(items),
        items=items
    )

@app.route('/api/run-council', methods=['POST'])
def run_council():
    """Trigger council analysis with optional issue intake (topic/context)."""
    import subprocess
    try:
        payload = request.get_json(silent=True) or {}
        topic = (payload.get('topic') or '').strip() or 'Council session'
        context = (payload.get('context') or '').strip()

        issue = create_council_issue(topic, context)

        # Keep council trigger lightweight; council script can read latest issue file if desired.
        subprocess.run(
            ['python3', '/Users/AI-OPS/.openclaw/workspace/advisory-council/council.py'],
            capture_output=True,
            timeout=45
        )
        return jsonify({'status': 'success', 'issue': issue})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/council/issues')
def api_council_issues():
    """Return recent council issues for dashboard rendering."""
    return jsonify({'items': get_council_issues(limit=20)})

@app.route('/api/restart-gateway', methods=['POST'])
def restart_gateway():
    """Restart OpenClaw Gateway via host bridge API."""
    try:
        bridge_url = 'http://host.docker.internal:18080/gateway/restart'
        req = urllib.request.Request(bridge_url, method='POST')
        response = urllib.request.urlopen(req, timeout=12)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify({
                'status': 'success',
                'message': 'Gateway restart initiated. Polling for recovery...'
            })
        return jsonify({'status': 'error', 'message': result.get('message', 'Restart failed')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/gateway/status')
def api_gateway_status():
    """Gateway health/status for frontend polling."""
    try:
        bridge_url = 'http://host.docker.internal:18080/gateway/status'
        response = urllib.request.urlopen(bridge_url, timeout=10)
        result = json.loads(response.read().decode('utf-8'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check-email/<account>', methods=['POST'])
def check_email(account):
    """Check email for specified account via bridge API."""
    if account not in ['nick', 'burt']:
        return jsonify({'status': 'error', 'message': 'Invalid account'}), 400
    
    try:
        # Call bridge API on host
        bridge_url = 'http://host.docker.internal:18080/email/check'
        payload = {
            'account': account
        }
        
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('status') == 'success':
            return jsonify({
                'status': 'success',
                'unread': result.get('unread', 0),
                'emails': result.get('emails', []),
                'account': account
            })
        else:
            return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
            
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ebook/run', methods=['POST'])
def run_ebook_pipeline():
    """Run ebook distribution automation pipeline."""
    import subprocess
    try:
        script = EBOOK_SCRIPTS / 'run_all.sh'
        if not script.exists():
            return jsonify({'status': 'error', 'message': 'run_all.sh not found'}), 404

        result = subprocess.run([str(script)], capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            stats = get_ebook_stats()
            return jsonify({
                'status': 'success',
                'message': 'Automation run complete',
                'latest_build': stats.get('latest_build'),
                'output_path': stats.get('output_path')
            })

        return jsonify({'status': 'error', 'message': result.stderr or result.stdout}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/youtube-summarize', methods=['POST'])
def youtube_summarize():
    """Run YouTube summarizer skill scripts for a given URL."""
    import subprocess
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()

    if not url:
        return jsonify({'status': 'error', 'message': 'YouTube URL required'}), 400

    try:
        extract_script = YT_SKILL_DIR / 'scripts' / 'extract_transcript.py'
        summarize_script = YT_SKILL_DIR / 'scripts' / 'summarize_transcript.py'

        if not extract_script.exists() or not summarize_script.exists():
            return jsonify({'status': 'error', 'message': 'youtube-summarizer scripts missing'}), 404

        YT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        transcript_path = YT_ARTIFACTS_DIR / 'transcript.json'
        summary_path = YT_ARTIFACTS_DIR / 'summary.md'

        p1 = subprocess.run(
            ['python3', str(extract_script), '--url', url, '--out-dir', str(YT_ARTIFACTS_DIR)],
            capture_output=True, text=True, timeout=240
        )
        if p1.returncode != 0:
            return jsonify({'status': 'error', 'message': p1.stderr or p1.stdout or 'Transcript extraction failed'}), 500

        p2 = subprocess.run(
            ['python3', str(summarize_script), '--transcript', str(transcript_path), '--out', str(summary_path)],
            capture_output=True, text=True, timeout=180
        )
        if p2.returncode != 0:
            return jsonify({'status': 'error', 'message': p2.stderr or p2.stdout or 'Summary generation failed'}), 500

        preview = ''
        if summary_path.exists():
            preview = summary_path.read_text()[:1400]

        return jsonify({
            'status': 'success',
            'summary_path': str(summary_path),
            'transcript_path': str(transcript_path),
            'preview': preview
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/browser-job', methods=['POST'])
def run_browser_job():
    """Run browser automation jobs on host via bridge API."""
    data = request.get_json() or {}
    mode = (data.get('mode') or 'task').strip().lower()
    cfg = data.get('config')

    try:
        bridge_url = 'http://host.docker.internal:18080/browser/job'
        payload = {'mode': mode, 'config': cfg}
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urllib.request.urlopen(req, timeout=360)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Browser job failed')}), 500
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            parsed = json.loads(body)
            return jsonify({'status': 'error', 'message': parsed.get('message', str(e))}), 500
        except Exception:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/read-email/<account>/<email_id>', methods=['POST'])
def read_email(account, email_id):
    """Read a specific email for account via bridge API."""
    if account not in ['nick', 'burt']:
        return jsonify({'status': 'error', 'message': 'Invalid account'}), 400

    try:
        bridge_url = 'http://host.docker.internal:18080/email/read'
        payload = {
            'account': account,
            'id': email_id
        }

        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode('utf-8'))

        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500

    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/chats', methods=['GET'])
def telegram_chats():
    """List Telegram chats from bridge API."""
    try:
        bridge_url = 'http://host.docker.internal:18080/telegram/chats'
        response = urllib.request.urlopen(bridge_url, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/telegram/health', methods=['GET'])
def telegram_health():
    """Telegram diagnostics for command center card hardening."""
    diag = {
        'status': 'error',
        'bridge': False,
        'chats_ok': False,
        'chat_count': 0,
        'message': 'Unknown'
    }
    try:
        bridge_url = 'http://host.docker.internal:18080/telegram/chats'
        response = urllib.request.urlopen(bridge_url, timeout=12)
        result = json.loads(response.read().decode('utf-8'))
        diag['bridge'] = True
        if result.get('status') == 'success':
            chats = result.get('chats', []) or []
            diag['chats_ok'] = True
            diag['chat_count'] = len(chats)
            diag['status'] = 'success'
            diag['message'] = 'Telegram bridge healthy'
        else:
            diag['message'] = result.get('message', 'Telegram bridge returned error')
    except Exception as e:
        diag['message'] = str(e)

    return jsonify(diag)

@app.route('/api/telegram/history', methods=['POST'])
def telegram_history():
    """Get recent Telegram messages for selected chat."""
    data = request.get_json() or {}
    chat_id = str(data.get('chat_id', '')).strip()
    limit = int(data.get('limit', 6))

    if not chat_id:
        return jsonify({'status': 'error', 'message': 'chat_id required'}), 400

    try:
        bridge_url = 'http://host.docker.internal:18080/telegram/history'
        payload = {'chat_id': chat_id, 'limit': limit}
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/send', methods=['POST'])
def telegram_send():
    """Send Telegram message via bridge API."""
    from flask import request
    data = request.get_json()
    chat_id = data.get('chat_id', '8334496229')  # Default to Nick
    message = data.get('message', '')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Message required'}), 400
    
    try:
        # Call bridge API on host
        bridge_url = 'http://host.docker.internal:18080/telegram/send'
        payload = {
            'chat_id': chat_id,
            'message': message
        }
        
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('status') == 'success':
            return jsonify({'status': 'success', 'message': 'Message sent'})
        else:
            return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
            
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/task/create', methods=['POST'])
def create_task():
    """Create new task."""
    import subprocess
    data = request.get_json()
    title = data.get('title', '')
    assigned_to = data.get('assigned_to', 'Nick')
    due_date = data.get('due_date', '')
    
    if not title:
        return jsonify({'status': 'error', 'message': 'Title required'}), 400
    
    try:
        # Insert into task tracker database
        db_path = OPENCLAW_DIR / 'task-tracker' / 'tasks.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task (title, status, assigned_to, due_date, created_date)
            VALUES (?, 'Not Started', ?, ?, ?)
        """, (title, assigned_to, due_date, date.today().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Task created'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/crm/add-contact', methods=['POST'])
def add_contact():
    """Add new CRM contact."""
    import subprocess
    data = request.get_json()
    name = data.get('name', '')
    contact_type = data.get('contact_type', 'Other')
    organization = data.get('organization', '')
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Name required'}), 400
    
    try:
        # Insert into CRM database
        db_path = OPENCLAW_DIR / 'civic-crm' / 'crm.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contact (name, organization, contact_type, status, engagement_level, created_date, updated_date)
            VALUES (?, ?, ?, 'New Lead', 'Cold', ?, ?)
        """, (name, organization, contact_type, date.today().isoformat(), date.today().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Contact added'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("CivicOS Command Center starting...")
    print("Access: http://100.81.239.69:8090")
    app.run(host='0.0.0.0', port=8090, debug=False)
