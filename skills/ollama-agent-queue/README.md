# ollama-agent-queue

Sequential queue manager for local Ollama model calls so only one local agent runs at a time.

## Why it exists

Parallel local model calls can saturate VRAM and stall sessions. This skill serializes requests from other skills.

## Quick start

```bash
cd ~/.openclaw/workspace/skills/ollama-agent-queue

# enqueue
python3 scripts/queue_manager.py enqueue --payload-json '{
  "calling_skill":"diagnostic",
  "agent_id":"diag-001",
  "model":"local/qwen-14b",
  "system_prompt":"You are concise.",
  "user_prompt":"Say READY",
  "max_tokens":64,
  "priority":"normal"
}'

# process one item
python3 scripts/queue_manager.py process-once

# status + result (caller polls result file)
python3 scripts/queue_manager.py status
cat data/agent-queue/results/diag-001.json
```

## Worker mode

```bash
python3 scripts/queue_manager.py worker --poll-seconds 2
```

- Uses `data/agent-queue/queue.lock` while active item is running.
- Will not start next item until current call returns complete/timeout/error.
- Handles stale lock recovery (>10 min, no ollama process) automatically.

## Controls

```bash
python3 scripts/queue_manager.py pause
python3 scripts/queue_manager.py resume
python3 scripts/queue_manager.py clear
python3 scripts/queue_manager.py skip-current
python3 scripts/queue_manager.py status-block
```

## Calling convention for other skills

1) Register request with `enqueue`.
2) Poll callback result file until status is `complete|timeout|error`.
3) After consuming result, caller deletes its own callback file to keep `results/` clean.

## Validate/package

```bash
python3 ../skill-creator/scripts/validate_skill.py ~/.openclaw/workspace/skills/ollama-agent-queue
python3 ../skill-creator/scripts/package_skill.py ~/.openclaw/workspace/skills/ollama-agent-queue --out-dir ~/.openclaw/workspace/skills
```
