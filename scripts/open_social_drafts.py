#!/usr/bin/env python3
import json, pathlib, subprocess, urllib.parse, datetime as dt
BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
cfg = json.loads((BASE/'social_media'/'automation_config.json').read_text())
q = BASE/'social_media'/'queue'/f"{dt.datetime.now().strftime('%Y-%m-%d')}.json"
if not q.exists():
    raise SystemExit('No queue for today. Run scripts/social_autopilot.py first.')
pack = json.loads(q.read_text())
for p in pack.get('posts',[]):
    url = cfg['x_intent_base'] + '?' + urllib.parse.urlencode({'text': p['text']})
    subprocess.run(['open', url])
print('Opened X intent drafts for today.')
subprocess.run(['open', cfg.get('facebook_page_url','https://facebook.com')])
print('Opened Facebook page.')
