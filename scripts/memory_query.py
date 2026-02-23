#!/usr/bin/env python3
"""Local memory query with fallback:
1) tries memory_search tool is not available from shell, so do deterministic keyword scan.
2) returns top matching lines from MEMORY.md and memory/*.md.
"""
import argparse, re
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
paths = [BASE/'MEMORY.md'] + sorted((BASE/'memory').glob('*.md'))

ap = argparse.ArgumentParser()
ap.add_argument('query')
ap.add_argument('--limit', type=int, default=12)
args = ap.parse_args()
terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_\-]+", args.query) if len(t) > 2]

hits=[]
for p in paths:
    if not p.exists():
        continue
    for i,l in enumerate(p.read_text(errors='ignore').splitlines(),1):
        low=l.lower()
        score=sum(1 for t in terms if t in low)
        if score>0:
            hits.append((score,str(p),i,l.strip()))

hits.sort(key=lambda x:(-x[0],x[1],x[2]))
for h in hits[:args.limit]:
    print(f"[{h[0]}] {h[1]}#{h[2]}: {h[3]}")
