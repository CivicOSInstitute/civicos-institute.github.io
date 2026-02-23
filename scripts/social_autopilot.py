#!/usr/bin/env python3
import datetime as dt
import json
import os
import pathlib
import subprocess
import urllib.parse
import urllib.request

BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
CFG_PATH = BASE / 'social_media' / 'automation_config.json'
QUEUE_DIR = BASE / 'social_media' / 'queue'
QUEUE_DIR.mkdir(parents=True, exist_ok=True)


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
        'Founders Complete Edition is live: The Open Source Student — a unified, implementation-first guide to local AI literacy. '\
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
    mpath.write_text('\n'.join(lines))
    latest = QUEUE_DIR / 'latest.md'
    latest.write_text('\n'.join(lines))
    return jpath, mpath


def get_discord_webhook(cmd):
    try:
        out = subprocess.check_output([cmd], text=True).strip()
        return out if out.startswith('http') else None
    except Exception:
        return None


def post_discord(pack, cfg):
    cmd = cfg.get('discord_webhook_cmd')
    if not cmd:
        return {'status': 'skipped', 'reason': 'no webhook command configured'}
    webhook = get_discord_webhook(cmd)
    if not webhook:
        return {'status': 'skipped', 'reason': 'webhook unavailable'}

    sent = 0
    for p in pack['posts']:
        body = json.dumps({'content': p['text']}).encode('utf-8')
        req = urllib.request.Request(webhook, data=body, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                if 200 <= r.status < 300:
                    sent += 1
        except Exception:
            pass
    return {'status': 'ok', 'sent': sent, 'total': len(pack['posts'])}


if __name__ == '__main__':
    cfg = load_cfg()
    pack = build_posts(cfg)
    jpath, mpath = save_pack(pack, cfg)
    result = {'pack_json': str(jpath), 'pack_md': str(mpath)}

    if cfg.get('discord_enabled', False):
        result['discord'] = post_discord(pack, cfg)

    print(json.dumps(result, indent=2))
