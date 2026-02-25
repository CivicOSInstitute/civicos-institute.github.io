---
name: ollama-agent-queue
description: Queue manager skill for serializing local Ollama agent invocations from other skills; enqueues requests, runs one-at-a-time with queue.lock, writes callback results, and supports status/pause/clear diagnostics.
---

# ollama-agent-queue

Infrastructure skill (library-style). Other skills call this instead of invoking local Ollama directly.

## Intent

Provide a centralized sequential queue for local Ollama agent requests. The queue manager processes exactly one request at a time and writes results to callback files. Calling skills poll result files; the queue manager never pushes results.

## Queue contract (input)

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
- Lock file: `./data/agent-queue/queue.lock`
- Results: `./data/agent-queue/results/<agent_id>.json`
- Logs: `./data/agent-queue/logs/queue.log`
- Alert stream: `./data/agent-queue/alerts.jsonl`

## Core loop behavior (worker)

Every ~2 seconds:
1. If `queue.lock` exists, do nothing.
2. If no pending items, set `queue.status = "idle"`.
3. Else select next item by priority (`urgent > high > normal`) + FIFO.
4. Create `queue.lock`, set `current_agent`, call Ollama `/api/generate` with `stream=false`.
5. Block until complete/timeout/error.
6. Write callback result JSON.
7. Clear `current_agent`, update counters, delete `queue.lock`.
8. Continue loop.

## Model mapping

- `local/qwen-coder-32b` → `qwen2.5-coder:32b`
- `local/qwen-14b` → `qwen2.5:14b`
- `local/mistral-small` → `mistral:latest`

Startup/model check uses Ollama tags (`/api/tags`). If requested model is unavailable, that item fails immediately and queue continues.

## Timeout policy

- `local/mistral-small`: 120s
- `local/qwen-14b`: 240s
- `local/qwen-coder-32b`: 480s

On timeout, result is written with `status: "timeout"`, queue continues.

## Offline policy

If Ollama is unreachable:
- Retry tags check 3 times with 10s backoff.
- If still failing: set queue status to `paused_ollama_offline`, fail pending items to callback files, emit alert event, and wait for manual `resume`.

## Commands

```bash
# Enqueue one request
python3 scripts/queue_manager.py enqueue --payload-json '<json>'

# View queue status
python3 scripts/queue_manager.py status

# Run one cycle
python3 scripts/queue_manager.py process-once

# Persistent watcher
python3 scripts/queue_manager.py worker --poll-seconds 2

# Control plane
python3 scripts/queue_manager.py pause
python3 scripts/queue_manager.py resume
python3 scripts/queue_manager.py clear
```

## Result schema (output)

```json
{
  "agent_id": "council-dante-001",
  "calling_skill": "council-of-advisors",
  "model": "local/mistral-small",
  "status": "complete",
  "result": "...",
  "tokens_used": 347,
  "duration_seconds": 12.4,
  "completed_at": "ISO timestamp"
}
```

Timeout/error variants include `status: "timeout"` or `status: "error"` and `error` text.
