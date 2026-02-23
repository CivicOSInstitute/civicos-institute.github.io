# API Gate Policy (Active)

Activated: 2026-02-23
Trigger: Remaining API budget at ~16%

## Policy
1. Default all work to local models.
2. API usage is blocked unless explicit approval is provided in this format:
   - `APPROVE API [task-id]`
3. Emergency API reserve:
   - 8% emergency reserve
   - 8% planned critical ops reserve
4. Any non-critical task must run local-only.

## Local Model Routing
- Default: `qwen2.5:14b`
- Code-heavy only: `qwen2.5-coder:32b-instruct-q3_K_L`
- Rewrite/2nd pass: `mistral-small3.2:24b-instruct-2506-q4_K_M`

## Critical API-eligible categories
- Irreversible external communications requiring high-stakes polish
- Compliance/legal wording where precision risk is material
- Publish-critical blockers unresolved after one local retry

## Enforcement Rule
If task is non-critical and asks for API model, deny and route to local with note: "API Gate Active".
