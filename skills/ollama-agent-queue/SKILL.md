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
1. If `queue.lock` exists, treat as active processing; if stale (>10 min) and no Ollama process is active, auto-clear stale lock and recover.
2. If no pending items, set `queue.status = "idle"`.
3. Else select next item by priority (`urgent > high > normal`) + FIFO.
4. Create `queue.lock`, set `current_agent`, call Ollama `/api/generate` with `stream=false`.
5. **Blocking execution:** do not move to next item until current item completes/timeouts/errors.
6. Write callback result JSON.
7. Clear `current_agent`, update counters, delete `queue.lock`.
8. Continue loop.

## Model mapping

- `local/qwen-coder-32b` → `qwen2.5-coder:32b`
- `local/qwen-14b` → `qwen2.5:14b`
- `local/mistral-small` → `mistral:latest`

Startup/model check uses Ollama tags (`/api/tags`). If requested model is unavailable, that item fails immediately and queue continues.

## Priority and wait alerts

- `urgent`: front of queue; if wait exceeds 30s, emit Architecture backlog alert.
- `high`: ahead of normal; if wait exceeds 120s, emit Architecture backlog alert.
- `normal`: FIFO, no wait alerting.

## Timeout policy

- `local/mistral-small`: 120s
- `local/qwen-14b`: 240s
- `local/qwen-coder-32b`: 480s

On timeout, result is written with `status: "timeout"`, queue continues.

## Resource-overload handling (503 / OOM)

If Ollama returns resource-exhaustion style errors (`503`, `out of memory`, `resource exhausted`):
1. Back off 30 seconds.
2. Retry the same item once.
3. If still failing: write error result, continue queue, emit Architecture alert.
4. If 3 consecutive resource errors occur: pause queue and emit direct alert for manual intervention.

## Offline policy

If Ollama is unreachable:
- Retry tags check 3 times with 10s backoff.
- If still failing: set queue status to `paused_ollama_offline`, fail pending items to callback files, emit alert event, and wait for manual `resume`.

## Stale lock recovery

If `queue.lock` is older than 10 minutes and no Ollama process is active:
1. Clear lock file.
2. Write timeout result for `current_agent`.
3. Resume queue processing.
4. Emit Architecture alert: `⚠️ Stale lock file cleared — queue resumed`.

## Commands

```bash
# Enqueue one request
python3 scripts/queue_manager.py enqueue --payload-json '<json>'

# View queue status (JSON)
python3 scripts/queue_manager.py status

# View queue status (human block)
python3 scripts/queue_manager.py status-block

# Run one cycle
python3 scripts/queue_manager.py process-once

# Persistent watcher (2s loop)
python3 scripts/queue_manager.py worker --poll-seconds 2

# Control plane
python3 scripts/queue_manager.py pause
python3 scripts/queue_manager.py resume
python3 scripts/queue_manager.py clear
python3 scripts/queue_manager.py skip-current
```

## Performance log

Each processed item appends to:
- `./data/agent-queue/queue-log-YYYY-MM-DD.json`

Entry fields include:
- `agent_id`, `calling_skill`, `model`, `priority`
- `queued_at`, `started_at`, `completed_at`
- `wait_time_seconds`, `duration_seconds`, `tokens_used`, `status`

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

## Calling-skill integration helper

Use `scripts/integration_helper.py` to standardize caller behavior (enqueue + poll + optional cleanup):

```bash
python3 scripts/integration_helper.py \
  --calling-skill council-of-advisors \
  --model local/qwen-14b \
  --priority high \
  --system-prompt "You are Vera..." \
  --user-prompt "Analyze this decision..." \
  --max-tokens 500
```

The helper returns final result JSON to stdout when `status` reaches `complete|timeout|error|cancelled`.
