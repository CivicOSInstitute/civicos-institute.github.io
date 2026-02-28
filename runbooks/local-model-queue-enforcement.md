# Local Model Queue Enforcement

Policy: all local-model invocations must route through:
- `skills/ollama-agent-queue/scripts/integration_helper.py`
- or `skills/ollama-agent-queue/scripts/queue_manager.py`

## Runtime guard (single command)

```bash
python3 scripts/local_queue_guard.py \
  --context "subagent" \
  --command "<command to execute>"
```

- Exit `0`: allowed
- Exit `42`: blocked (direct local model invocation detected)

## Preflight audit (codebase)

```bash
python3 scripts/audit_local_model_routing.py
python3 scripts/audit_local_model_routing.py --json
```

Latest report path:
- `generated/local_model_routing_audit_2026-02-28.json`
