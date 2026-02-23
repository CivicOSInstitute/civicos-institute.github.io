#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

CFG = Path('/Users/AI-OPS/.openclaw/workspace/social_media/youtube_channels.json')


def load_cfg():
    if CFG.exists():
        return json.loads(CFG.read_text())
    return {'channels': [], 'scan_limit_per_channel': 5, 'summarize_new_videos': True, 'max_new_summaries_per_run': 3}


def get_channel_id(url):
    # Use yt-dlp metadata extraction to discover canonical channel id
    p = subprocess.run(['yt-dlp', '--dump-single-json', '--flat-playlist', url], capture_output=True, text=True, timeout=40)
    if p.returncode == 0 and p.stdout.strip():
        try:
            j = json.loads(p.stdout)
            cid = j.get('channel_id') or j.get('uploader_id')
            name = j.get('channel') or j.get('uploader') or url
            return cid, name
        except Exception:
            pass

    # fallback for common /channel/ pattern
    if '/channel/' in url:
        cid = url.split('/channel/')[1].split('/')[0].split('?')[0]
        return cid, url

    return '', url


def main():
    if len(sys.argv) < 2:
        print('Usage: youtube_add_channel.py <youtube_channel_url> [display_name]')
        raise SystemExit(1)

    url = sys.argv[1].strip()
    name_override = sys.argv[2].strip() if len(sys.argv) > 2 else ''

    cid, name = get_channel_id(url)
    if not cid:
        print('Could not resolve channel id from URL. Provide /channel/ URL with UC... id.')
        raise SystemExit(2)

    cfg = load_cfg()
    channels = cfg.get('channels', [])
    if any((c.get('channel_id') or '') == cid for c in channels):
        print('Channel already exists:', cid)
        raise SystemExit(0)

    channels.append({'name': name_override or name, 'channel_id': cid, 'enabled': True})
    cfg['channels'] = channels
    CFG.write_text(json.dumps(cfg, indent=2))
    print('Added channel:', name_override or name, cid)


if __name__ == '__main__':
    main()
