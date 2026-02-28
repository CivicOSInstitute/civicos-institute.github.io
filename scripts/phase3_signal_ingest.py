#!/usr/bin/env python3
import json
import hashlib
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import subprocess
import requests
import xml.etree.ElementTree as ET

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
CFG = ROOT / 'config' / 'phase3_signal_sources.json'
YT_CFG = ROOT / 'social_media' / 'youtube_channels.json'
OUT_DIR = ROOT / 'generated' / 'signals'
OUT_DIR.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc)
DATE_KEY = NOW.strftime('%Y-%m-%d')

STATE_QUOTA = OUT_DIR / 'gnews_quota_state.json'
STATE_SEEN = OUT_DIR / 'seen_hashes.json'
LATEST_JSON = OUT_DIR / 'phase3_signals_latest.json'
LATEST_MD = OUT_DIR / 'phase3_signals_latest.md'
BOARD_MD = OUT_DIR / 'decision_log_board_ready.md'
NOTION_STATE = OUT_DIR / 'notion_synced_signal_ids.json'

NOTION_CREATE = ROOT / 'notion-ops' / 'notion_task_create.sh'
ACCOUNT = 'ncerbone@civicos-institute.org'


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout.strip()


def drive_ls(parent='root'):
    out = run(['gog', 'drive', 'ls', '--account', ACCOUNT, '--parent', parent, '--max', '200', '--json'])
    if not out:
        return []
    return json.loads(out).get('files', [])


def ensure_folder(name, parent='root'):
    for f in drive_ls(parent):
        if f.get('name') == name and f.get('mimeType') == 'application/vnd.google-apps.folder':
            return f['id']
    out = run(['gog', 'drive', 'mkdir', name, '--account', ACCOUNT, '--parent', parent, '--json'])
    j = json.loads(out)
    return j.get('folder', {}).get('id') or j.get('id')


def drive_upload(path, parent, name=None):
    cmd = ['gog', 'drive', 'upload', str(path), '--account', ACCOUNT, '--parent', parent, '--json']
    if name:
        cmd.extend(['--name', name])
    out = run(cmd)
    j = json.loads(out)
    return j.get('file', j)


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def signal_hash(title, link):
    key = f"{(title or '').strip().lower()}|{(link or '').strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:20]


def unwrap_google_alert_url(link):
    try:
        if not link:
            return link
        u = urlparse(link)
        if 'google.com' in (u.netloc or '') and u.path == '/url':
            q = parse_qs(u.query)
            target = (q.get('url') or q.get('q') or [''])[0]
            return unquote(target) if target else link
        return link
    except Exception:
        return link


def extract_publication(link, fallback='Unknown'):
    try:
        host = (urlparse(link).netloc or '').lower()
        if host.startswith('www.'):
            host = host[4:]
        if not host:
            return fallback
        parts = host.split('.')
        base = parts[-2] if len(parts) >= 2 else host
        return base.capitalize()
    except Exception:
        return fallback


def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9']+", (text or '').lower())
    stop = {
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'into', 'about', 'your', 'have', 'will', 'what',
        'when', 'where', 'how', 'why', 'are', 'was', 'were', 'been', 'being', 'their', 'them', 'they', 'you',
        'our', 'not', 'but', 'can', 'all', 'new', 'use', 'using', 'guide', 'video'
    }
    return {w for w in words if len(w) > 2 and w not in stop}


def find_related_video(signal, youtube_items):
    st = tokenize(signal.get('title', '') + ' ' + signal.get('summary', ''))
    best = None
    best_score = 0
    for y in youtube_items:
        yt = tokenize(y.get('title', '') + ' ' + y.get('summary', ''))
        score = len(st & yt)
        if score > best_score:
            best_score = score
            best = y
    return best if best_score >= 2 else None


def clean_text(text):
    t = re.sub(r'<[^>]+>', ' ', text or '')
    t = html.unescape(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def contains_any(text, kws):
    t = (text or '').lower()
    return any(k.lower() in t for k in kws)


def score_severity(text):
    t = (text or '').lower()
    high = ['emergency', 'lawsuit', 'investigation', 'breach', 'sanction', 'fraud', 'criminal', 'shutdown', 'ban', 'subpoena']
    medium = ['policy', 'regulation', 'compliance', 'funding', 'grant', 'procurement', 'hearing', 'vote', 'legislation']
    if any(k in t for k in high):
        return 'high'
    if any(k in t for k in medium):
        return 'medium'
    return 'low'


def parse_rss(url, source_tag):
    out = []
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        # RSS
        items = root.findall('.//item')
        for it in items[:30]:
            title = (it.findtext('title') or '').strip()
            link = (it.findtext('link') or '').strip()
            desc = (it.findtext('description') or '').strip()
            pub = (it.findtext('pubDate') or '').strip()
            out.append({
                'source': source_tag,
                'title': title,
                'link': link,
                'summary': re.sub(r'<[^>]+>', ' ', desc),
                'published': pub,
            })

        # Atom (e.g., Google Alerts)
        if not out:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            for e in entries[:30]:
                title = (e.findtext('atom:title', default='', namespaces=ns) or '').strip()
                link = ''
                link_el = e.find('atom:link', ns)
                if link_el is not None:
                    link = (link_el.attrib.get('href') or '').strip()
                desc = (e.findtext('atom:content', default='', namespaces=ns) or e.findtext('atom:summary', default='', namespaces=ns) or '').strip()
                pub = (e.findtext('atom:published', default='', namespaces=ns) or e.findtext('atom:updated', default='', namespaces=ns) or '').strip()
                out.append({
                    'source': source_tag,
                    'title': title,
                    'link': link,
                    'summary': re.sub(r'<[^>]+>', ' ', desc),
                    'published': pub,
                })
    except Exception as e:
        out.append({'source': source_tag, 'error': str(e), 'title': '', 'link': '', 'summary': ''})
    return out


def load_youtube_channels(path):
    data = load_json(path, {})
    channels = []
    for c in data.get('channels', []):
        if c.get('enabled', True) and c.get('channel_id'):
            channels.append(c)
    return channels


def parse_youtube_feed(channel):
    channel_id = channel.get('channel_id')
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    source_tag = f"youtube:{channel.get('name', channel_id)}"
    out = []
    try:
        r = requests.get(feed_url, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        entries = root.findall('atom:entry', ns)
        for e in entries[:15]:
            title = (e.findtext('atom:title', default='', namespaces=ns) or '').strip()
            video_id = (e.findtext('yt:videoId', default='', namespaces=ns) or '').strip()
            link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ''
            desc = (e.findtext('atom:group/atom:description', default='', namespaces=ns) or '').strip()
            if not desc:
                desc = (e.findtext('yt:group/yt:description', default='', namespaces=ns) or '').strip()
            pub = (e.findtext('atom:published', default='', namespaces=ns) or '').strip()
            out.append({
                'source': source_tag,
                'channel': channel.get('name', ''),
                'title': title,
                'link': link,
                'summary': desc,
                'published': pub,
            })
    except Exception as e:
        out.append({'source': source_tag, 'error': str(e), 'title': '', 'link': '', 'summary': ''})
    return out


def gnews_scan(cfg, quota_state):
    results = []
    key = (Path.home() / '.zshrc')
    api_key = None
    api_key = __import__('os').environ.get('GNEWS_API_KEY')
    if not api_key:
        return results, quota_state, 'missing GNEWS_API_KEY'

    cap = int(cfg.get('daily_cap', 100))
    per_query = int(cfg.get('per_query_max', 10))
    used = int(quota_state.get('used', 0))
    date = quota_state.get('date')
    if date != DATE_KEY:
        used = 0

    for q in cfg.get('queries', []):
        if used >= cap:
            break
        remaining = cap - used
        max_n = min(per_query, remaining)
        url = f"https://gnews.io/api/v4/search?q={quote_plus(q)}&lang=en&country=us&max={max_n}&apikey={api_key}"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
            arts = data.get('articles', [])
            for a in arts:
                results.append({
                    'source': 'gnews',
                    'query': q,
                    'title': a.get('title', ''),
                    'link': a.get('url', ''),
                    'summary': a.get('description', '') or '',
                    'published': a.get('publishedAt', ''),
                })
            used += 1
        except Exception:
            continue

    quota_state = {'date': DATE_KEY, 'used': used, 'cap': cap}
    return results, quota_state, None


def to_notion_tasks(signals):
    synced = set(load_json(NOTION_STATE, []))
    new_synced = set(synced)
    created = 0
    for s in signals:
        sid = s['id']
        if sid in synced:
            continue
        if s['severity'] == 'low':
            continue
        pri = 'P1' if s['severity'] == 'high' else 'P2'
        tag = '[Board-ready] ' if s['severity'] == 'high' else ''
        title = f"{tag}{s['severity'].upper()} signal: {s['title'][:90]}"
        cmd = [str(NOTION_CREATE), '--title', title, '--status', 'Not started', '--priority', pri, '--channel', 'Ops Signals']
        p = subprocess.run(cmd, cwd=str(ROOT / 'notion-ops'), capture_output=True, text=True)
        if p.returncode == 0:
            new_synced.add(sid)
            created += 1
    NOTION_STATE.write_text(json.dumps(sorted(new_synced)))
    return created


def main():
    cfg = load_json(CFG, {})
    nf = cfg.get('noise_filter', {})
    must_kws = nf.get('require_any_keywords', [])
    excl_kws = nf.get('exclude_keywords', [])

    seen = set(load_json(STATE_SEEN, []))
    raw = []

    for u in cfg.get('govinfo_rss', []):
        raw.extend(parse_rss(u, 'govinfo_rss'))
    for u in cfg.get('google_alerts_rss', []):
        raw.extend(parse_rss(u, 'google_alerts_rss'))

    # YouTube RSS ingestion (full enabled list from compiled channel catalog)
    for ch in load_youtube_channels(YT_CFG):
        raw.extend(parse_youtube_feed(ch))

    quota_state = load_json(STATE_QUOTA, {'date': DATE_KEY, 'used': 0, 'cap': 100})
    gnews_items, quota_state, gnews_err = gnews_scan(cfg.get('gnews', {}), quota_state)
    raw.extend(gnews_items)
    STATE_QUOTA.write_text(json.dumps(quota_state, indent=2))

    clean = []
    for r in raw:
        if r.get('error'):
            continue
        resolved_link = unwrap_google_alert_url(r.get('link', ''))
        text = f"{clean_text(r.get('title',''))} {clean_text(r.get('summary',''))}"
        if excl_kws and contains_any(text, excl_kws):
            continue
        if must_kws and not contains_any(text, must_kws):
            continue
        hid = signal_hash(r.get('title', ''), resolved_link)
        if hid in seen:
            continue
        sev = score_severity(text)
        item = {
            'id': hid,
            'source': r.get('source'),
            'title': clean_text(r.get('title')),
            'link': resolved_link,
            'summary': clean_text(r.get('summary', '')),
            'published': r.get('published', ''),
            'severity': sev,
            'board_ready': sev == 'high',
            'ingested_at': NOW.isoformat(),
            'publication': extract_publication(resolved_link, fallback=r.get('source', 'Unknown')),
            'channel': r.get('channel', ''),
        }
        clean.append(item)

    for c in clean:
        seen.add(c['id'])
    STATE_SEEN.write_text(json.dumps(sorted(seen)[-5000:], indent=2))

    counts = {'low': 0, 'medium': 0, 'high': 0}
    for c in clean:
        counts[c['severity']] += 1

    board = [c for c in clean if c['board_ready']]

    report = {
        'generated_at': NOW.isoformat(),
        'noise_filter_applied': True,
        'totals': {
            'ingested': len(clean),
            'low': counts['low'],
            'medium': counts['medium'],
            'high': counts['high'],
            'board_ready': len(board),
        },
        'gnews_quota': quota_state,
        'gnews_error': gnews_err,
        'signals': clean,
    }
    LATEST_JSON.write_text(json.dumps(report, indent=2), encoding='utf-8')

    md = [
        '# Phase 3 Signal Ingestion',
        f"Generated: {NOW.isoformat()}",
        '',
        '## Summary',
        f"- Ingested: {len(clean)}",
        f"- low: {counts['low']}",
        f"- medium: {counts['medium']}",
        f"- high: {counts['high']}",
        f"- [Board-ready]: {len(board)}",
        f"- GNews quota used: {quota_state.get('used',0)}/{quota_state.get('cap',100)}",
        '',
        '## Signals',
    ]
    for s in clean[:80]:
        tag = ' [Board-ready]' if s['board_ready'] else ''
        md.append(f"- ({s['severity']}){tag} {s['title']} — {s['source']}\n  {s['link']}")
    LATEST_MD.write_text('\n'.join(md), encoding='utf-8')

    board_md = [
        '# Decision-Logs — [Board-ready] Signals',
        f"Generated: {NOW.isoformat()}",
        '',
    ]
    youtube_items = [x for x in clean if str(x.get('source', '')).startswith('youtube:')]
    if not board:
        board_md.append('- None')
    else:
        for s in board:
            rel = find_related_video(s, youtube_items)
            board_md.append(f"## [Board-ready] {s['title']}")
            board_md.append(f"Source: {s.get('publication','Unknown')} — {s.get('link','')}")
            if rel:
                ch = rel.get('channel') or rel.get('source', '').replace('youtube:', '')
                board_md.append(f"Related video: {ch} — {rel.get('title','')} — {rel.get('link','')}")
            else:
                board_md.append("Related video: none found in monitored YouTube feeds")
            why = f"This signal indicates a potentially material governance shift that could affect CivicOS positioning in the next 30–90 days."
            risk = f"Risk: delayed response could weaken policy credibility; Opportunity: timely framing can position CivicOS as a trusted governance convener."
            nxt = f"Next step: assign an owner to produce a 1-page briefing memo and recommendation within 48 hours."
            board_md.append(f"Why it matters: {why}")
            board_md.append(f"Risk/Opportunity: {risk}")
            board_md.append(f"Next step: {nxt}")
            board_md.append('')
    BOARD_MD.write_text('\n'.join(board_md), encoding='utf-8')

    notion_created = to_notion_tasks(clean)

    uploads = []
    try:
        board_root = ensure_folder('Board-Packages')
        month_id = ensure_folder(datetime.now().strftime('%Y-%m'), board_root)
        ops_id = ensure_folder('Ops-Reports')
        dec_id = ensure_folder('Decision-Logs')
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        for p in [LATEST_JSON, LATEST_MD]:
            up = drive_upload(p, ops_id, name=f"{p.stem}_{ts}{p.suffix}")
            uploads.append({'type': 'ops_report', 'id': up.get('id'), 'name': up.get('name')})
        up = drive_upload(BOARD_MD, dec_id, name=f"decision_log_board_ready_{ts}.md")
        uploads.append({'type': 'decision_log', 'id': up.get('id'), 'name': up.get('name')})
    except Exception as e:
        uploads.append({'type': 'error', 'message': str(e)})

    route_state = {
        'generated_at': NOW.isoformat(),
        'notion_tasks_created': notion_created,
        'drive_uploads': uploads,
    }
    (OUT_DIR / 'phase3_routing_state.json').write_text(json.dumps(route_state, indent=2), encoding='utf-8')

    print(str(LATEST_JSON))
    print(str(LATEST_MD))
    print(str(BOARD_MD))


if __name__ == '__main__':
    main()
