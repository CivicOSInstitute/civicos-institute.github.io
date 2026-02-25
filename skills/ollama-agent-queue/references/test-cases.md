# ollama-agent-queue — Test Cases

## Functional

1. **Enqueue valid request**
   - Input: full required JSON payload.
   - Expect: `pending` increments, request appears in `queue.json`.

2. **Reject missing required fields**
   - Input missing `agent_id`.
   - Expect: non-zero exit + explicit missing field error.

3. **Priority ordering**
   - Enqueue 3 requests: normal, urgent, high.
   - Process repeatedly.
   - Expect order: urgent → high → normal.

4. **Duplicate agent_id protection**
   - Enqueue same `agent_id` twice.
   - Expect second enqueue rejected.

5. **Pause/resume behavior**
   - Pause queue, enqueue request, run `process-once`.
   - Expect `queue_paused` and no processing.
   - Resume then process; expect normal execution.

## Reliability

6. **Model timeout handling**
   - Process with low timeout on long prompt.
   - Expect callback file with `status=timeout` and timeout error.

7. **Ollama failure propagation**
   - Use invalid model string.
   - Expect `status=error` and error detail captured.

8. **Crash-safe queue file write**
   - Verify `queue.json.tmp` swaps atomically to `queue.json`.

9. **Lock-file discipline**
   - Create `queue.lock` manually and run `process-once`.
   - Expect no new processing while lock exists.

10. **Offline Ollama handling**
   - Stop Ollama and run worker/process-once.
   - Expect 3 retries with backoff, queue status `paused_ollama_offline`, pending items failed with error outputs.

11. **Resource-overload retry behavior**
   - Simulate `503` / `out of memory` response.
   - Expect one 30s backoff retry, then fail/continue if still broken.

12. **Consecutive resource-failure pause**
   - Force 3 consecutive resource errors across items.
   - Expect queue status becomes `paused` and direct alert emitted.

13. **Stale-lock recovery path**
   - Create lock older than 10 minutes with `current_agent` set and no Ollama process active.
   - Expect stale lock cleared, current agent timed out to callback, queue resumes.

## Output contract

14. **Result schema completeness**
   - Expect fields: `agent_id`, `calling_skill`, `model`, `status`, `result/error`, `duration_seconds`, `completed_at`.

15. **Callback path honored**
   - Set custom callback path.
   - Expect result JSON at that exact path.
