#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import subprocess
import urllib.parse
import urllib.request
import urllib.error
import time

BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
CFG_PATH = BASE / 'social_media' / 'automation_config.json'
QUEUE_DIR = BASE / 'social_media' / 'queue'
LOG_DIR = BASE / 'generated'
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_cfg():
    return json.loads(CFG_PATH.read_text())


def top_news_headline():
    p = BASE / 'website-news' / 'news.json'
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        for src in data.get('sources', []):
            items = src.get('items', [])
            if items:
                item = items[0]
                return {
                    'title': item.get('title', '').strip(),
                    'link': item.get('link', '').strip(),
                    'source': src.get('name', 'News')
                }
    except Exception:
        return None
    return None


def build_posts(cfg):
    news = top_news_headline()
    today = dt.datetime.now().strftime('%Y-%m-%d')
    base_link = cfg['ebook_url']

    p1 = (
        'Founders Complete Edition is live: The Open Source Student — a unified, implementation-first guide to local AI literacy. '
        'Built for students, families, and educators.\n\n'
        f'{base_link}\n\n'
        '#OpenSource #AIEducation #CivicOS'
    )

    if news and news.get('title') and news.get('link'):
        p2 = (
            f"Civic tech signal ({news['source']}): {news['title']}\n"
            f"{news['link']}\n\n"
            'We break these trends into practical implementation steps for schools and communities.\n'
            f"{cfg['site_url']}/news\n\n#GovTech #PublicInterestTech #CivicOS"
        )
    else:
        p2 = (
            'Daily civic tech brief: practical AI + open infrastructure, minus hype.\n\n'
            f"{cfg['site_url']}/news\n\n#GovTech #OpenSource #CivicOS"
        )

    p3 = (
        'Quick question for educators/parents/builders: What is the biggest blocker to responsible student AI adoption where you are?\n\n'
        'We are building open curriculum + implementation systems to reduce friction.\n'
        f"{cfg['site_url']}\n\n#EdTech #AIliteracy #CivicOS"
    )

    return {
        'date': today,
        'posts': [
            {'slot': 'morning', 'channel': 'x/facebook/discord', 'text': p1},
            {'slot': 'midday', 'channel': 'x/facebook/discord', 'text': p2},
            {'slot': 'evening', 'channel': 'x/facebook/discord', 'text': p3}
        ]
    }


def save_pack(pack, cfg):
    d = pack['date']
    jpath = QUEUE_DIR / f'{d}.json'
    mpath = QUEUE_DIR / f'{d}.md'
    jpath.write_text(json.dumps(pack, indent=2))

    lines = [f"# Social Pack {d}", '']
    for p in pack['posts']:
        t = p['text']
        x_intent = cfg['x_intent_base'] + '?' + urllib.parse.urlencode({'text': t})
        lines.append(f"## {p['slot'].title()} ({p['channel']})")
        lines.append('')
        lines.append(t)
        lines.append('')
        lines.append(f"- X one-click: {x_intent}")
        lines.append(f"- Facebook page: {cfg['facebook_page_url']}")
        lines.append('')
    md = '\n'.join(lines)
    mpath.write_text(md)
    (QUEUE_DIR / 'latest.md').write_text(md)
    return jpath, mpath


def get_discord_webhook(cmd):
    try:
        out = subprocess.check_output([cmd], text=True).strip()
        return out if out.startswith('http') else None
    except Exception:
        return None


def post_once(webhook, text):
    body = json.dumps({'content': text}).encode('utf-8')
    req = urllib.request.Request(webhook, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def post_discord(pack, cfg, retries=2):
    cmd = cfg.get('discord_webhook_cmd')
    if not cmd:
        return {'status': 'skipped', 'reason': 'no webhook command configured', 'deliveries': []}

    webhook = get_discord_webhook(cmd)
    if not webhook:
        return {'status': 'skipped', 'reason': 'webhook unavailable', 'deliveries': []}

    deliveries = []
    sent = 0
    for p in pack['posts']:
        slot = p['slot']
        text = p['text']
        ok = False
        last_err = ''
        status_code = None

        for attempt in range(1, retries + 2):
            try:
                status_code = post_once(webhook, text)
                if 200 <= status_code < 300:
                    ok = True
                    break
                last_err = f'http_{status_code}'
            except urllib.error.HTTPError as e:
                status_code = e.code
                last_err = f'http_{e.code}'
            except Exception as e:
                last_err = str(e)
            time.sleep(1)

        deliveries.append({
            'slot': slot,
            'ok': ok,
            'status_code': status_code,
            'error': last_err if not ok else ''
        })
        if ok:
            sent += 1

    overall = 'ok' if sent == len(pack['posts']) else ('partial' if sent > 0 else 'error')
    return {'status': overall, 'sent': sent, 'total': len(pack['posts']), 'deliveries': deliveries}


def write_delivery_log(result):
    ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    p = LOG_DIR / f'social_delivery_{ts}.json'
    p.write_text(json.dumps(result, indent=2))
    (LOG_DIR / 'social_delivery_latest.json').write_text(json.dumps(result, indent=2))
    return str(p)


if __name__ == '__main__':
    cfg = load_cfg()
    pack = build_posts(cfg)
    jpath, mpath = save_pack(pack, cfg)
    result = {
        'generated_at': dt.datetime.now().isoformat(timespec='seconds'),
        'pack_json': str(jpath),
        'pack_md': str(mpath)
    }

    if cfg.get('discord_enabled', False):
        result['discord'] = post_discord(pack, cfg)

    result['delivery_log'] = write_delivery_log(result)
    print(json.dumps(result, indent=2))
