# ollama-agent-queue — Eval Rubric

Score each 0-2 (max 10):

1. **Serialization correctness**
   - 0: parallel execution observed
   - 1: mostly serialized with race edge cases
   - 2: strictly one-at-a-time

2. **Queue integrity**
   - 0: state corruption occurs
   - 1: occasional malformed/partial state
   - 2: consistent valid queue.json updates

3. **Failure isolation**
   - 0: one failure blocks queue
   - 1: queue sometimes halts after failure
   - 2: failure logged + queue continues

4. **Integration clarity**
   - 0: other skills unclear how to call
   - 1: partial contract docs
   - 2: contract + commands + callback schema clear

5. **Ops diagnostics**
   - 0: no usable status/control
   - 1: partial controls
   - 2: status/pause/resume/clear all function

Passing threshold: **8/10**.
