#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
TASK_DB = Path('/Users/AI-OPS/.openclaw/task-tracker/tasks.db')
NEWS_JSON = BASE / 'website-news' / 'news.json'
SOCIAL_QUEUE = BASE / 'social_media' / 'queue'
OUT_DIR = BASE / 'generated'
AUTOMATION_HEALTH = OUT_DIR / 'automation_health.json'


def query_one(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else 0


def load_task_stats(today: str):
    if not TASK_DB.exists():
        return {'error': f'missing task db: {TASK_DB}'}

    conn = sqlite3.connect(str(TASK_DB))
    try:
        total = query_one(conn, 'SELECT COUNT(*) FROM task')
        by_status = {
            'Not Started': query_one(conn, "SELECT COUNT(*) FROM task WHERE status='Not Started'"),
            'In Progress': query_one(conn, "SELECT COUNT(*) FROM task WHERE status='In Progress'"),
            'Completed': query_one(conn, "SELECT COUNT(*) FROM task WHERE status='Completed'"),
        }
        by_priority = {
            'High': query_one(conn, "SELECT COUNT(*) FROM task WHERE priority='High' AND status!='Completed'"),
            'Medium': query_one(conn, "SELECT COUNT(*) FROM task WHERE priority='Medium' AND status!='Completed'"),
            'Low': query_one(conn, "SELECT COUNT(*) FROM task WHERE priority='Low' AND status!='Completed'"),
        }
        due_today = query_one(conn, 'SELECT COUNT(*) FROM task WHERE due_date=? AND status!=\'Completed\'', (today,))
        overdue = query_one(conn, "SELECT COUNT(*) FROM task WHERE due_date < ? AND due_date IS NOT NULL AND status!='Completed'", (today,))
        auto_captured_today = query_one(
            conn,
            "SELECT COUNT(*) FROM task WHERE created_date=? AND notes LIKE '%Auto-source: telegram:%'",
            (today,),
        )
        latest_auto = conn.execute(
            "SELECT title, created_date FROM task WHERE notes LIKE '%Auto-source: telegram:%' ORDER BY id DESC LIMIT 5"
        ).fetchall()

        return {
            'total': total,
            'by_status': by_status,
            'by_priority_open': by_priority,
            'due_today_open': due_today,
            'overdue_open': overdue,
            'auto_captured_today': auto_captured_today,
            'latest_auto': latest_auto,
        }
    finally:
        conn.close()


def load_news_headline():
    if not NEWS_JSON.exists():
        return None
    try:
        data = json.loads(NEWS_JSON.read_text())
        for src in data.get('sources', []):
            items = src.get('items', [])
            if items:
                it = items[0]
                return {
                    'source': src.get('name', 'Unknown'),
                    'title': it.get('title', '').strip(),
                    'link': it.get('link', '').strip(),
                }
    except Exception:
        return None
    return None


def social_queue_status(today: str):
    p_json = SOCIAL_QUEUE / f'{today}.json'
    p_md = SOCIAL_QUEUE / f'{today}.md'
    latest = SOCIAL_QUEUE / 'latest.md'
    return {
        'today_json_exists': p_json.exists(),
        'today_md_exists': p_md.exists(),
        'latest_exists': latest.exists(),
    }


def load_automation_health():
    if not AUTOMATION_HEALTH.exists():
        return None
    try:
        return json.loads(AUTOMATION_HEALTH.read_text())
    except Exception:
        return None


def build_checklist(task_stats, queue, news, health):
    items = []

    if isinstance(task_stats, dict) and task_stats.get('overdue_open', 0) > 0:
        items.append(f"Triage overdue tasks first ({task_stats['overdue_open']} open overdue).")

    if isinstance(task_stats, dict) and task_stats.get('due_today_open', 0) > 0:
        items.append(f"Close or re-schedule tasks due today ({task_stats['due_today_open']} open due today).")

    if isinstance(task_stats, dict) and task_stats.get('auto_captured_today', 0) > 0:
        items.append(f"Review Telegram auto-captured tasks ({task_stats['auto_captured_today']} new today).")

    if not queue.get('today_json_exists'):
        items.append("Generate today's social queue (run scripts/social_autopilot.py).")

    if news and news.get('title'):
        items.append("Use top news headline for one midday post and one outreach talking point.")

    if health and isinstance(health, dict):
        bad = [s for s in health.get('steps', []) if s.get('status') != 'ok']
        if bad:
            items.append(f"Fix failed automation steps first ({len(bad)} failing in last ops cycle).")

    if not items:
        items.append('No urgent blockers detected. Proceed with highest-impact strategic tasks.')

    return items


def render_md(now, task_stats, news, queue, checklist, health):
    lines = []
    lines.append(f"# Ops Morning Brief — {now.strftime('%Y-%m-%d %H:%M %Z')}")
    lines.append('')

    lines.append('## Snapshot')
    if task_stats.get('error'):
        lines.append(f"- Task tracker: {task_stats['error']}")
    else:
        lines.append(f"- Tasks total: {task_stats['total']}")
        lines.append(f"- Open by priority: High {task_stats['by_priority_open']['High']}, Medium {task_stats['by_priority_open']['Medium']}, Low {task_stats['by_priority_open']['Low']}")
        lines.append(f"- Open due today: {task_stats['due_today_open']}")
        lines.append(f"- Open overdue: {task_stats['overdue_open']}")
        lines.append(f"- Telegram auto-captured today: {task_stats['auto_captured_today']}")

    lines.append(f"- Social queue ready today: {'yes' if queue['today_json_exists'] else 'no'}")
    lines.append(f"- Social latest draft exists: {'yes' if queue['latest_exists'] else 'no'}")
    lines.append('')

    lines.append('## Automation Health (Last Ops Cycle)')
    if health and isinstance(health, dict):
        lines.append(f"- Last run total seconds: {health.get('total_seconds', 'n/a')}")
        bad = [s for s in health.get('steps', []) if s.get('status') != 'ok']
        if bad:
            for s in bad:
                lines.append(f"- ❌ {s.get('name')}: status={s.get('status')} ({s.get('seconds')}s)")
        else:
            lines.append('- ✅ All ops cycle steps succeeded in last run.')
    else:
        lines.append('- No automation health file found yet (`generated/automation_health.json`).')
    lines.append('')

    lines.append('## Top News Signal')
    if news:
        lines.append(f"- {news.get('source', 'Source')}: {news.get('title', 'No title')}")
        if news.get('link'):
            lines.append(f"- Link: {news['link']}")
    else:
        lines.append('- No local news feed headline available.')
    lines.append('')

    lines.append('## Latest Auto-Captured Telegram Tasks')
    latest_auto = task_stats.get('latest_auto', []) if isinstance(task_stats, dict) else []
    if latest_auto:
        for title, created in latest_auto:
            lines.append(f"- [{created}] {title}")
    else:
        lines.append('- None found.')
    lines.append('')

    lines.append('## Prioritized Morning Checklist')
    for idx, item in enumerate(checklist, 1):
        lines.append(f"{idx}. {item}")
    lines.append('')

    lines.append('## Suggested Command Sequence')
    lines.append('```bash')
    lines.append('python3 scripts/auto_task_from_telegram.py')
    lines.append('python3 scripts/fetch_social_feeds.py')
    lines.append('python3 scripts/social_autopilot.py')
    lines.append('python3 scripts/ops_morning_brief.py')
    lines.append('```')
    lines.append('')

    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    now = dt.datetime.now().astimezone()
    today = now.strftime('%Y-%m-%d')

    task_stats = load_task_stats(today)
    news = load_news_headline()
    queue = social_queue_status(today)
    health = load_automation_health()
    checklist = build_checklist(task_stats, queue, news, health)

    md = render_md(now, task_stats, news, queue, checklist, health)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.out).resolve() if args.out else (OUT_DIR / f'ops_morning_brief_{today}.md')
    out.write_text(md)
    print(str(out))


if __name__ == '__main__':
    main()
