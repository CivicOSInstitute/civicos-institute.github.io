#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import os

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
CFG = ROOT / 'config' / 'ga4_monitoring.json'
OUT = ROOT / 'generated' / 'analytics'
OUT.mkdir(parents=True, exist_ok=True)
STATE = OUT / 'ga4_daily_latest.json'
MD = OUT / 'ga4_daily_latest.md'

now = datetime.now(timezone.utc).isoformat()

if not CFG.exists():
    report = {'generated_at': now, 'ok': False, 'error': 'missing config/ga4_monitoring.json'}
    STATE.write_text(json.dumps(report, indent=2))
    MD.write_text(f"# GA4 Daily Pull\n\nGenerated: {now}\n\n- ⚠️ missing config/ga4_monitoring.json\n")
    print(MD)
    raise SystemExit(0)

cfg = json.loads(CFG.read_text()).get('ga4', {})
property_id = cfg.get('property_id')
threshold = int(cfg.get('board_ready_threshold_wow_pct', 20))

# import analytics client from venv-installed package
blockers = []
if not property_id:
    blockers.append('missing property_id')
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    blockers.append('GOOGLE_APPLICATION_CREDENTIALS not set (service account json path required for Data API)')

if blockers:
    report = {
        'generated_at': now,
        'ok': False,
        'property_id': property_id,
        'measurement_id': cfg.get('measurement_id'),
        'blockers': blockers,
        'next_step': 'Set GOOGLE_APPLICATION_CREDENTIALS to GA4 service account key and grant Viewer to property.'
    }
    STATE.write_text(json.dumps(report, indent=2), encoding='utf-8')
    MD.write_text(
        "# GA4 Daily Pull\n\n"
        f"Generated: {now}\n\n"
        "## Status\n"
        "- ⚠️ Blocked\n"
        f"- Property ID: {property_id}\n"
        f"- Measurement ID: {cfg.get('measurement_id')}\n"
        "\n## Blockers\n" + '\n'.join([f"- {b}" for b in blockers]) +
        "\n\n## Next Step\n- Set service-account credential path and grant GA4 property Viewer access.\n"
    , encoding='utf-8')
    print(MD)
    raise SystemExit(0)

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest

client = BetaAnalyticsDataClient()
prop = f"properties/{property_id}"

# core totals: last 7 days vs previous 7 days
req = RunReportRequest(
    property=prop,
    dimensions=[],
    metrics=[Metric(name='totalUsers'), Metric(name='sessions')],
    date_ranges=[DateRange(start_date='7daysAgo', end_date='yesterday'), DateRange(start_date='14daysAgo', end_date='8daysAgo')]
)
resp = client.run_report(req)

# Parse totals
cur_users = int(resp.rows[0].metric_values[0].value) if resp.rows else 0
cur_sessions = int(resp.rows[0].metric_values[1].value) if resp.rows else 0
prev_users = int(resp.rows[1].metric_values[0].value) if len(resp.rows) > 1 else 0
prev_sessions = int(resp.rows[1].metric_values[1].value) if len(resp.rows) > 1 else 0

def wow(cur, prev):
    if prev == 0:
        return None
    return round(((cur-prev)/prev)*100,2)

wow_users = wow(cur_users, prev_users)
wow_sessions = wow(cur_sessions, prev_sessions)

# source/medium top 10 last 7 days
sm_req = RunReportRequest(
    property=prop,
    dimensions=[Dimension(name='sessionSourceMedium')],
    metrics=[Metric(name='sessions'), Metric(name='totalUsers')],
    date_ranges=[DateRange(start_date='7daysAgo', end_date='yesterday')],
    limit=10
)
sm = client.run_report(sm_req)
source_medium = [
    {
        'source_medium': r.dimension_values[0].value,
        'sessions': int(r.metric_values[0].value),
        'users': int(r.metric_values[1].value),
    }
    for r in sm.rows
]

# top pages by views (landing page path)
pg_req = RunReportRequest(
    property=prop,
    dimensions=[Dimension(name='landingPagePlusQueryString')],
    metrics=[Metric(name='sessions')],
    date_ranges=[DateRange(start_date='7daysAgo', end_date='yesterday')],
    limit=10
)
pg = client.run_report(pg_req)
top_pages = [
    {'page': r.dimension_values[0].value or '(not set)', 'sessions': int(r.metric_values[0].value)}
    for r in pg.rows
]

flags=[]
if wow_users is not None and abs(wow_users) >= threshold:
    flags.append({'metric':'users','wow_pct':wow_users,'tag':'[Board-ready]'})
if wow_sessions is not None and abs(wow_sessions) >= threshold:
    flags.append({'metric':'sessions','wow_pct':wow_sessions,'tag':'[Board-ready]'})

report = {
    'generated_at': now,
    'ok': True,
    'property_id': property_id,
    'measurement_id': cfg.get('measurement_id'),
    'window': 'last7 vs prior7',
    'totals': {
        'users': {'current': cur_users, 'previous': prev_users, 'wow_pct': wow_users},
        'sessions': {'current': cur_sessions, 'previous': prev_sessions, 'wow_pct': wow_sessions}
    },
    'source_medium_top10': source_medium,
    'top_pages_top10': top_pages,
    'board_ready_flags': flags
}
STATE.write_text(json.dumps(report, indent=2), encoding='utf-8')

lines=[
    '# GA4 Daily Pull',
    f'Generated: {now}',
    '',
    f"- Property ID: {property_id}",
    f"- Measurement ID: {cfg.get('measurement_id')}",
    f"- Users: {cur_users} (prev {prev_users}, WoW {wow_users}%)",
    f"- Sessions: {cur_sessions} (prev {prev_sessions}, WoW {wow_sessions}%)",
    '',
    '## Top Source/Medium',
]
for r in source_medium:
    lines.append(f"- {r['source_medium']}: {r['sessions']} sessions / {r['users']} users")
lines += ['', '## Top Pages']
for r in top_pages:
    lines.append(f"- {r['page']}: {r['sessions']} sessions")
if flags:
    lines += ['', '## [Board-ready] Flags']
    for f in flags:
        lines.append(f"- {f['metric']} WoW {f['wow_pct']}%")

MD.write_text('\n'.join(lines), encoding='utf-8')
print(MD)

# optional: route to drive ops reports using existing script if present
route_script = ROOT / 'scripts' / 'drive_route_crm_artifacts.py'
if route_script.exists():
    pass
