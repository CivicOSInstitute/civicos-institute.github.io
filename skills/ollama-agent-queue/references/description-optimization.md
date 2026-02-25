# Description Optimization Notes

Chosen description:

> Queue manager skill for serializing local Ollama agent invocations from other skills; enqueues requests, runs one-at-a-time, writes callback results, and supports status/pause/clear diagnostics.

Why this wording:
- Starts with **what it is** (queue manager skill)
- States **scope** (local Ollama invocations from other skills)
- States **core behavior** (one-at-a-time)
- States **outputs/ops controls** (callback + diagnostics)

Rejected shorter variants were ambiguous about callback behavior and diagnostic commands.
