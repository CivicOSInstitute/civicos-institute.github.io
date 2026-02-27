# Model Route Map (Queue Aliases -> Actual Models)

Use this when adjusting settings manually.

- `local/qwen-14b` -> `qwen3:14b`  **(default local generalist)**
- `local/qwen3-14b` -> `qwen3:14b`
- `local/qwen2.5-14b` -> `qwen2.5:14b`  (legacy route)
- `local/mistral-small` -> `mistral:latest`
- `local/qwen-coder-32b` -> `qwen2.5-coder:32b`

Source of truth: `skills/ollama-agent-queue/scripts/queue_manager.py` (`MODEL_MAP`).
