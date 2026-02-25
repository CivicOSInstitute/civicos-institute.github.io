# ollama-agent-queue

Sequential queue manager for local Ollama model calls so only one local agent runs at a time.

## Why it exists

Parallel local model calls can saturate VRAM and stall sessions. This skill serializes requests from other skills (infrastructure layer).

## Quick start

```bash
cd ~/.openclaw/workspace/skills/ollama-agent-queue

# 1) enqueue a request
python3 scripts/queue_manager.py enqueue --payload-json '{
  "calling_skill":"diagnostic",
  "agent_id":"diag-001",
  "model":"local/qwen-14b",
  "system_prompt":"You are concise.",
  "user_prompt":"Say READY",
  "max_tokens":64,
  "priority":"normal"
}'

# 2) process one item
python3 scripts/queue_manager.py process-once

# 3) inspect queue/result
python3 scripts/queue_manager.py status
cat data/agent-queue/results/diag-001.json
```

## Validate/package

```bash
python3 ../skill-creator/scripts/validate_skill.py ~/.openclaw/workspace/skills/ollama-agent-queue
python3 ../skill-creator/scripts/package_skill.py ~/.openclaw/workspace/skills/ollama-agent-queue --out-dir ~/.openclaw/workspace/skills
```
