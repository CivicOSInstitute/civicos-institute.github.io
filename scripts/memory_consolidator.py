#!/usr/bin/env python3
import datetime as dt
from pathlib import Path
import re

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
MEM_DIR = BASE / 'memory'
MASTER = BASE / 'MEMORY.md'
ARCH = MEM_DIR / 'archive'
ARCH.mkdir(parents=True, exist_ok=True)

TODAY = dt.date.today()
cutoff = TODAY - dt.timedelta(days=30)
week_cut = TODAY - dt.timedelta(days=7)


def parse_date(name):
    try:
        return dt.date.fromisoformat(name.replace('.md',''))
    except Exception:
        return None

lines_to_add=[]
for f in sorted(MEM_DIR.glob('20*.md')):
    d=parse_date(f.name)
    if not d: continue
    txt=f.read_text(errors='ignore').splitlines()
    if d >= week_cut:
        for ln in txt:
            if ln.strip().startswith('- '):
                lines_to_add.append(ln.strip())
    if d < cutoff:
        f.rename(ARCH / f.name)

unique=[]
seen=set()
for l in lines_to_add:
    if l not in seen:
        seen.add(l); unique.append(l)

if unique:
    stamp=dt.datetime.now().strftime('%Y-%m-%d')
    block='\n\n## Weekly Consolidation ' + stamp + '\n' + '\n'.join(unique[:80]) + '\n'
    existing=MASTER.read_text(errors='ignore') if MASTER.exists() else '# MEMORY\n'
    merged=existing + block
    # soft cap 8000 chars: keep tail of consolidated + header if exceeded
    if len(merged) > 8000:
        merged = merged[:4000] + '\n\n...\n\n' + merged[-3500:]
    MASTER.write_text(merged)

print('memory consolidation complete')
