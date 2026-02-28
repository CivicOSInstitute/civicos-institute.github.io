# Model Route Map (Queue Aliases -> Actual Models)

Use this when adjusting settings manually.

- `local/qwen-14b` -> `qwen3:14b`  **(default local generalist)**
- `local/qwen3-14b` -> `qwen3:14b`
- `local/qwen2.5-14b` -> `qwen2.5:14b`  (legacy route)
- `local/mistral-small` -> `mistral-small3.2:24b-instruct-2506-q4_K_M`
- `local/qwen-coder-32b` -> `qwen2.5-coder:32b-instruct-q3_K_L`

Source of truth: `skills/ollama-agent-queue/scripts/queue_manager.py` (`MODEL_MAP`).
