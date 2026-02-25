#!/usr/bin/env python3
import csv
import datetime as dt
from pathlib import Path
from collections import defaultdict

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
CSV_PATH = BASE / 'social_media' / 'analytics' / 'metrics_daily.csv'
OUT_PATH = BASE / 'generated' / 'social_analytics_weekly.md'


def to_int(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0


def safe_div(a, b):
    return (a / b) if b else 0.0


def load_rows(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                r['_date'] = dt.date.fromisoformat((r.get('date') or '').strip())
            except Exception:
                continue
            rows.append(r)
    return rows


def aggregate(rows):
    totals = defaultdict(int)
    by_platform = defaultdict(lambda: defaultdict(int))

    for r in rows:
        p = (r.get('platform') or 'unknown').lower()
        fields = [
            'posts','reach','impressions','views','likes','comments','shares','saves',
            'profile_visits','link_clicks','follower_delta','outreach_actions',
            'dms_started','meaningful_conversations'
        ]
        for k in fields:
            v = to_int(r.get(k))
            totals[k] += v
            by_platform[p][k] += v

    return totals, by_platform


def fmt_pct(v):
    return f"{v*100:.2f}%"


def build_report(all_rows):
    today = dt.date.today()
    start = today - dt.timedelta(days=6)
    week_rows = [r for r in all_rows if start <= r['_date'] <= today]
    prev_start = start - dt.timedelta(days=7)
    prev_end = start - dt.timedelta(days=1)
    prev_rows = [r for r in all_rows if prev_start <= r['_date'] <= prev_end]

    totals, by_platform = aggregate(week_rows)
    prev_totals, _ = aggregate(prev_rows)

    engagements = totals['likes'] + totals['comments'] + totals['shares'] + totals['saves']
    engagement_rate = safe_div(engagements, totals['reach'])
    conversation_rate = safe_div(totals['meaningful_conversations'], totals['posts'])
    follower_conv = safe_div(totals['follower_delta'], totals['reach'])
    outreach_yield = safe_div(totals['meaningful_conversations'], totals['outreach_actions'])

    def delta(cur, prev):
        if prev == 0:
            return 'n/a' if cur == 0 else '+∞'
        return f"{((cur-prev)/prev)*100:+.1f}%"

    lines = []
    lines.append(f"# Social Analytics Weekly Scorecard — {today.isoformat()}")
    lines.append('')
    lines.append(f"**Window:** {start.isoformat()} to {today.isoformat()}")
    lines.append('')

    lines.append('## Topline')
    lines.append(f"- Posts: {totals['posts']} (WoW {delta(totals['posts'], prev_totals['posts'])})")
    lines.append(f"- Reach: {totals['reach']} (WoW {delta(totals['reach'], prev_totals['reach'])})")
    lines.append(f"- Engagements: {engagements} (WoW {delta(engagements, (prev_totals['likes']+prev_totals['comments']+prev_totals['shares']+prev_totals['saves']))})")
    lines.append(f"- Follower/Sub Delta: {totals['follower_delta']} (WoW {delta(totals['follower_delta'], prev_totals['follower_delta'])})")
    lines.append('')

    lines.append('## Effectiveness KPIs')
    lines.append(f"- Engagement Rate: {fmt_pct(engagement_rate)}")
    lines.append(f"- Conversation Rate: {conversation_rate:.2f} meaningful conversations/post")
    lines.append(f"- Follower Conversion: {fmt_pct(follower_conv)}")
    lines.append(f"- Outreach Yield: {fmt_pct(outreach_yield)}")
    lines.append('')

    lines.append('## Platform Breakdown')
    for p in ['x','facebook','youtube']:
        t = by_platform.get(p, {})
        if not t:
            continue
        eng = t.get('likes',0)+t.get('comments',0)+t.get('shares',0)+t.get('saves',0)
        er = safe_div(eng, t.get('reach',0))
        lines.append(f"- **{p.upper()}**: posts={t.get('posts',0)}, reach={t.get('reach',0)}, engagements={eng}, ER={fmt_pct(er)}, follower_delta={t.get('follower_delta',0)}")
    lines.append('')

    lines.append('## Decisions for Next Week')
    lines.append('1. Double down on the platform/post type with highest Engagement Rate and Conversation Rate.')
    lines.append('2. Cut or rework low-reach formats after 3 attempts.')
    lines.append('3. Maintain daily outreach blocks; they are required for non-bot growth.')
    lines.append('4. Keep CTA consistent for 7 days before changing conversion asks.')
    lines.append('')

    return '\n'.join(lines)


def main():
    rows = load_rows(CSV_PATH)
    report = build_report(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report)
    print(str(OUT_PATH))


if __name__ == '__main__':
    main()
