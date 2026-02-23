#!/usr/bin/env python3
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET
import datetime as dt
import subprocess

BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
CFG = BASE / 'social_media' / 'youtube_channels.json'
OUT_DIR = BASE / 'generated' / 'youtube_dashboard'
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE = OUT_DIR / 'state.json'
DATA = OUT_DIR / 'videos.json'

EXTRACT = BASE / 'skills' / 'youtube-summarizer' / 'scripts' / 'extract_transcript.py'
SUMMARIZE = BASE / 'skills' / 'youtube-summarizer' / 'scripts' / 'summarize_transcript.py'

ATOM = {'a': 'http://www.w3.org/2005/Atom'}


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def fetch_feed(channel_id):
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        xml = r.read()
    root = ET.fromstring(xml)
    entries = []
    for e in root.findall('a:entry', ATOM):
        vid = e.find('{http://www.youtube.com/xml/schemas/2015}videoId')
        title = e.find('a:title', ATOM)
        link = e.find('a:link', ATOM)
        pub = e.find('a:published', ATOM)
        if vid is None:
            continue
        entries.append({
            'video_id': (vid.text or '').strip(),
            'title': (title.text or '').strip() if title is not None else '',
            'url': (link.attrib.get('href') or '').strip() if link is not None else f"https://youtube.com/watch?v={(vid.text or '').strip()}",
            'published': (pub.text or '').strip() if pub is not None else ''
        })
    return entries


def summarize_video(video, out_base):
    vdir = out_base / video['video_id']
    vdir.mkdir(parents=True, exist_ok=True)
    tjson = vdir / 'transcript.json'
    smd = vdir / 'summary.md'

    if smd.exists():
        return str(smd)

    try:
        subprocess.run([
            'python3', str(EXTRACT), '--url', video['url'], '--out-dir', str(vdir)
        ], check=True, timeout=240, capture_output=True, text=True)
        subprocess.run([
            'python3', str(SUMMARIZE), '--transcript', str(tjson), '--out', str(smd)
        ], check=True, timeout=180, capture_output=True, text=True)
        return str(smd)
    except Exception:
        return ''


def main():
    cfg = load_json(CFG, {'channels': []})
    state = load_json(STATE, {'seen_video_ids': []})
    seen = set(state.get('seen_video_ids', []))

    all_rows = []
    new_rows = []
    scan_limit = int(cfg.get('scan_limit_per_channel', 5))

    for ch in cfg.get('channels', []):
        if not ch.get('enabled'):
            continue
        cid = (ch.get('channel_id') or '').strip()
        if not cid:
            continue
        name = ch.get('name') or cid
        try:
            vids = fetch_feed(cid)[:scan_limit]
        except Exception as e:
            all_rows.append({'channel': name, 'error': str(e), 'videos': []})
            continue

        rows = []
        for v in vids:
            is_new = v['video_id'] not in seen
            row = {
                'channel': name,
                **v,
                'is_new': is_new,
                'summary_path': ''
            }
            rows.append(row)
            if is_new:
                new_rows.append(row)
        all_rows.extend(rows)

    # Summarize only a limited number of new videos per run
    if cfg.get('summarize_new_videos', True):
        cap = int(cfg.get('max_new_summaries_per_run', 3))
        for r in new_rows[:cap]:
            sp = summarize_video(r, OUT_DIR / 'summaries')
            r['summary_path'] = sp

    # Persist seen IDs
    for r in all_rows:
        vid = r.get('video_id')
        if vid:
            seen.add(vid)

    state_out = {
        'updated_at': dt.datetime.now().isoformat(timespec='seconds'),
        'seen_video_ids': sorted(seen)
    }
    STATE.write_text(json.dumps(state_out, indent=2))

    payload = {
        'updated_at': dt.datetime.now().isoformat(timespec='seconds'),
        'new_count': len(new_rows),
        'videos': all_rows
    }
    DATA.write_text(json.dumps(payload, indent=2))
    print(str(DATA))


if __name__ == '__main__':
    main()
