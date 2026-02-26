# Data Boundary Policy (Personal vs Org)

Status: Active
Date: 2026-02-26

## Classification tags (mandatory)
- `org-only`: CivicOS institutional operations.
- `personal-only`: personal/private workflows.
- `mixed-prohibited`: workflows must not blend both without explicit approval.

## Rules
1. Production workflows in this repo default to `org-only`.
2. `personal-only` data cannot be used in `org-only` prompts/reports.
3. Any cross-boundary transfer requires explicit Director approval and audit note.
4. Logs/artifacts must include classification when practical.

## Enforcement guidance
- Include `data_boundary` field in workflow outputs where feasible.
- Treat unknown boundary as `mixed-prohibited` until classified.
