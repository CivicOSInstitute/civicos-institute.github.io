#!/usr/bin/env python3
import json, pathlib
src = pathlib.Path('/Users/AI-OPS/.openclaw/workspace/automation/fine_tune_2b/deploy/router_map.json')
dst = pathlib.Path('/Users/AI-OPS/.openclaw/workspace/skills/model-router/config/specialist_adapters.json')
dst.parent.mkdir(parents=True, exist_ok=True)
obj = json.loads(src.read_text())
dst.write_text(json.dumps(obj, indent=2))
print(f'wrote {dst}')
