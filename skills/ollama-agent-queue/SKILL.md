---
name: ollama-agent-queue
description: Queue manager skill for serializing local Ollama agent invocations from other skills; enqueues requests, runs one-at-a-time, writes callback results, and supports status/pause/clear diagnostics.
---

# ollama-agent-queue

Infrastructure skill (library-style). Other skills call this instead of invoking local Ollama directly.

## Use when

- Multiple local agent calls can overlap and saturate VRAM/CPU.
- A calling skill needs deterministic, sequential local model execution.
- You need queue diagnostics (`status`, `pause`, `resume`, `clear`).

## Queue contract

Calling skills register work as JSON with this shape:

```json
{
  "calling_skill": "council-of-advisors",
  "agent_id": "council-dante-001",
  "model": "local/mistral-small",
  "system_prompt": "...",
  "user_prompt": "...",
  "max_tokens": 500,
  "priority": "normal",
  "callback": "./data/agent-queue/results/council-dante-001.json"
}
```

## Runtime files

- Queue state: `./data/agent-queue/queue.json`
- Results: `./data/agent-queue/results/<agent_id>.json`
- Logs: `./data/agent-queue/logs/queue.log`

## Commands

Run from this skill directory:

```bash
# Enqueue one request
python3 scripts/queue_manager.py enqueue --payload-json '<json>'

# View queue status
python3 scripts/queue_manager.py status

# Worker loop (daemon-style)
python3 scripts/queue_manager.py worker --poll-seconds 2

# Process exactly one item (good for cron)
python3 scripts/queue_manager.py process-once

# Control plane
python3 scripts/queue_manager.py pause
python3 scripts/queue_manager.py resume
python3 scripts/queue_manager.py clear
```

## Priority order

`urgent` > `high` > `normal` (FIFO within same priority).

## Integration pattern for other skills

1. Build payload JSON with `agent_id` and `callback`.
2. `enqueue` request.
3. Poll callback file (or call `status`) until complete/failed.
4. Read result JSON and continue pipeline.

## Failure behavior

- If Ollama execution fails or times out, request is marked `failed` and written to callback with error.
- Queue continues to next pending request.

## Notes

- This skill is intentionally non-user-facing and should run quietly in background workflows.
- Keep exactly one worker active per queue directory.
