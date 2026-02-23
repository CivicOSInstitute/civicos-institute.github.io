#!/usr/bin/env python3
import csv
import datetime as dt
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

BASE = '/Users/AI-OPS/.openclaw/workspace'
CFG = os.path.join(BASE, 'social_media/feeds/social_rss_sources.csv')
OUT_DIR = os.path.join(BASE, 'social_media/feeds')
os.makedirs(OUT_DIR, exist_ok=True)

now = dt.datetime.now()
stamp = now.strftime('%Y%m%d_%H%M')
out_path = os.path.join(OUT_DIR, f'social_feed_snapshot_{stamp}.md')
latest_path = os.path.join(OUT_DIR, 'social_feed_latest.md')


def text(el, path):
    n = el.find(path)
    return (n.text or '').strip() if n is not None and n.text else ''


def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    # RSS
    for item in root.findall('.//channel/item')[:5]:
        title = text(item, 'title')
        link = text(item, 'link')
        pub = text(item, 'pubDate')
        items.append((title, link, pub))
    if items:
        return items
    # Atom
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    for entry in root.findall('.//a:entry', ns)[:5]:
        title = text(entry, '{http://www.w3.org/2005/Atom}title')
        pub = text(entry, '{http://www.w3.org/2005/Atom}published') or text(entry, '{http://www.w3.org/2005/Atom}updated')
        link = ''
        lk = entry.find('{http://www.w3.org/2005/Atom}link')
        if lk is not None:
            link = (lk.attrib.get('href') or '').strip()
        items.append((title, link, pub))
    return items


rows = []
with open(CFG, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

lines = []
lines.append(f'# Social Feed Snapshot — {now.isoformat(timespec="minutes")}')
lines.append('')
lines.append('Auto-generated from `social_media/feeds/social_rss_sources.csv`.')
lines.append('')

errors = 0
for r in rows:
    platform = r['platform']
    source = r['source']
    url = r['url']
    enabled = str(r['enabled']).strip().lower() == 'true'
    notes = r.get('notes', '')

    lines.append(f'## {platform.upper()} — {source}')
    lines.append(f'- URL: {url}')
    lines.append(f'- Enabled: {enabled}')
    if notes:
        lines.append(f'- Notes: {notes}')

    if not enabled:
        lines.append('- Status: skipped (disabled)')
        lines.append('')
        continue

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 OpenClaw SocialFeedBot/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        items = parse_feed(data)
        if not items:
            lines.append('- Status: fetched but no items parsed')
        else:
            lines.append(f'- Status: OK ({len(items)} items)')
            for i, (title, link, pub) in enumerate(items, 1):
                title = title.replace('\n', ' ').strip()
                lines.append(f'  {i}. {title}')
                if pub:
                    lines.append(f'     - Published: {pub}')
                if link:
                    lines.append(f'     - Link: {link}')
    except Exception as e:
        errors += 1
        lines.append(f'- Status: ERROR ({e})')

    lines.append('')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines).rstrip() + '\n')
with open(latest_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines).rstrip() + '\n')

print(out_path)
print(f'errors={errors}')
sys.exit(0 if errors == 0 else 2)
