# Local-First Router Skill

## Name
local-first-router

## Description
A skill that consults the model router to evaluate if ANY task can be handled by local models. Uses strict local-first policy with zero API escalation unless explicitly impossible locally.

## Version
1.0.0

## Author
Burt Prime

## Requirements
- ollama-agent-queue skill
- model-router skill
- Phi-3 Mini classifier available

## Configuration
```json
{
  "strict_local": true,
  "api_escalation_only_when": "explicitly_impossible_locally",
  "classifier": "phi3:mini",
  "fallback_chain": ["llama3.1:8b", "qwen3:14b", "deepseek-coder:6.7b"]
}
```

## Usage

### classify_for_local
Evaluates any task for local model execution.

**Input:**
```json
{
  "task": "string - description of task",
  "complexity": "low|medium|high",
  "requires_coding": boolean,
  "requires_vision": boolean,
  "requires_long_context": boolean
}
```

**Output:**
```json
{
  "can_handle_locally": true,
  "recommended_model": "llama3.1:8b",
  "reason": "Task is general writing within local model capabilities",
  "confidence": 0.95
}
```

### route_task
Routes task to appropriate local model or escalates only if impossible.

**Input:**
```json
{
  "task": "string",
  "context": "string (optional)"
}
```

**Output:**
```json
{
  "route": "local|escalate",
  "model": "llama3.1:8b|qwen3:14b|...",
  "execution_plan": "string"
}
```

## Policy

### 100% Local-First Rule
1. Every task MUST be evaluated for local execution first
2. Classification runs through phi3:mini (3-second overhead)
3. Only escalate to API if ALL local models fail or task is explicitly impossible locally
4. API escalation requires explicit user approval or "use API" keyword

### Local Model Priority Chain
1. **phi3:mini** - Fast classification (3s)
2. **llama3.1:8b** - General tasks, writing (16s)
3. **qwen3:14b** - Reasoning, Q&A (45s)
4. **deepseek-coder:6.7b** - Code tasks (28s)
5. **qwen3.5 variants** - Specialized roles

### Escalation Criteria (Strict)
- Task explicitly requires GPT-4/Codex capabilities
- All local models failed after retry
- User explicitly requests API with "use API", "use Kimi", "use GPT-4"
- Budget exception approved

## Scripts

### local_router.py
Main routing logic that consults model router for every task.

```python
#!/usr/bin/env python3
"""Local-First Router - 100% local model consultation"""
import subprocess
import json
import sys

def classify_task(task_desc):
    """Use phi3:mini to classify task for local execution"""
    prompt = f"""Classify this task for local model execution:
Task: {task_desc}

Can this be handled by a local 8B-14B parameter model?
Options: yes_coding, yes_writing, yes_reasoning, yes_vision, no_requires_api

Respond with JSON: {{"can_local": true/false, "model_type": "...", "confidence": 0.0-1.0}}"""
    
    result = subprocess.run(
        ["ollama", "run", "phi3:mini", prompt],
        capture_output=True, text=True, timeout=10
    )
    # Parse response
    return parse_classification(result.stdout)

def route_to_local(task, classification):
    """Route to appropriate local model"""
    model_map = {
        "yes_coding": "deepseek-coder:6.7b",
        "yes_writing": "llama3.1:8b", 
        "yes_reasoning": "qwen3:14b",
        "yes_vision": "qwen3.5:4b"
    }
    return model_map.get(classification["model_type"], "llama3.1:8b")

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "General task"
    classification = classify_task(task)
    
    if classification["can_local"]:
        model = route_to_local(task, classification)
        print(json.dumps({
            "route": "local",
            "model": model,
            "reason": f"Classified as {classification['model_type']} with confidence {classification['confidence']}"
        }))
    else:
        print(json.dumps({
            "route": "escalate",
            "reason": "Task requires capabilities beyond local models",
            "requires_approval": True
        }))
```

## Integration

### With OpenClaw
Add to `openclaw.json`:
```json
{
  "skills": ["local-first-router"],
  "default_classifier": "local-first-router/classify_for_local"
}
```

### With Model Router
This skill wraps and enforces the model router with 100% local-first policy.

## Testing

Run test suite:
```bash
python3 skills/local-first-router/tests/test_classifier.py
```

Expected results:
- 95%+ tasks classified for local execution
- <5% escalated to API
- Average classification time <5s

## License
MIT - CivicOS Institute
