#!/usr/bin/env python3
"""
Autonomous Agent - Main entry point for human-out-of-the-loop operations
Integrates: Phi-3 router + Autonomy engine + Execution layer
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Import from same directory
import importlib.util
spec = importlib.util.spec_from_file_location("autonomy_engine", str(Path(__file__).parent / "autonomy-engine.py"))
autonomy_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(autonomy_engine)
analyze_request = autonomy_engine.analyze_request
format_approval_request = autonomy_engine.format_approval_request

# Configuration
LOG_FILE = Path.home() / ".openclaw" / "logs" / "autonomous-agent.log"
APPROVAL_QUEUE = Path.home() / ".openclaw" / "run" / "approval-queue.json"
DAILY_SPEND_FILE = Path.home() / ".openclaw" / "run" / "daily-spend.json"
DAILY_BUDGET = 5.00  # $5 USD maximum per day
GLOBAL_FALLBACK_MODEL = "moonshot/kimi-k2.5"  # final fallback for routed requests

def log(msg, level="INFO"):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] [{level}] {msg}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def get_daily_spend() -> float:
    """Get today's API spend"""
    if DAILY_SPEND_FILE.exists():
        with open(DAILY_SPEND_FILE) as f:
            data = json.load(f)
            today = datetime.now().strftime("%Y-%m-%d")
            if data.get("date") == today:
                return data.get("amount", 0.0)
    return 0.0

def add_daily_spend(amount: float):
    """Add to today's API spend"""
    today = datetime.now().strftime("%Y-%m-%d")
    current = get_daily_spend()
    data = {"date": today, "amount": current + amount}
    with open(DAILY_SPEND_FILE, "w") as f:
        json.dump(data, f)

def check_budget() -> tuple[bool, float]:
    """Check if we're within daily budget. Returns (ok, remaining)"""
    spent = get_daily_spend()
    remaining = DAILY_BUDGET - spent
    return (remaining > 0, remaining)

def log_routing_summary():
    """Generate daily routing analytics"""
    try:
        with open(LOG_FILE) as f:
            logs = f.read()
        
        # Count routing decisions
        local_count = logs.count("[ROUTING] Completed")
        api_count = logs.count("[ROUTING] API Escalation")
        delegate_count = logs.count("[ROUTING] Sub-agent spawned")
        budget_exceeded = logs.count("[ROUTING] Budget exceeded")
        
        # Extract model usage
        models_used = {}
        for line in logs.split('\n'):
            if '[ROUTING] Completed' in line and 'Model:' in line:
                model = line.split('Model:')[1].split('|')[0].strip()
                models_used[model] = models_used.get(model, 0) + 1
        
        summary = f"""
=== DAILY ROUTING SUMMARY ===
Date: {datetime.now().strftime('%Y-%m-%d')}
Total Requests: {local_count + api_count + delegate_count}
  - Local: {local_count} (${local_count * 0.00:.2f})
  - API: {api_count}
  - Sub-agent: {delegate_count}
  - Budget Blocks: {budget_exceeded}

Model Usage:
{chr(10).join(f'  {model}: {count}' for model, count in sorted(models_used.items(), key=lambda x: x[1], reverse=True))}

Daily Spend: ${get_daily_spend():.2f} / $5.00
"""
        log(summary, "SUMMARY")
        
    except Exception as e:
        log(f"Error generating routing summary: {e}", "ERROR")

def classify_with_phi3(prompt: str) -> dict:
    """Use Phi-3 Mini for fast classification"""
    try:
        result = subprocess.run(
            ["ollama", "run", "phi3:mini"],
            input=prompt[:500],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"success": True, "output": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_local(prompt: str, model: str) -> str:
    """Execute with local Ollama model"""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout
    except Exception as e:
        return f"[Execution error: {e}]"

def queue_for_approval(prompt: str, level: str, reason: str):
    """Queue request for human approval"""
    approval_item = {
        "id": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "prompt": prompt,
        "level": level,
        "reason": reason,
        "requested_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    # Load existing queue
    queue = []
    if APPROVAL_QUEUE.exists():
        with open(APPROVAL_QUEUE) as f:
            queue = json.load(f)
    
    # Add new item
    queue.append(approval_item)
    
    # Save queue
    with open(APPROVAL_QUEUE, "w") as f:
        json.dump(queue, f, indent=2)
    
    log(f"Queued for approval: {approval_item['id']}", "PENDING")
    return approval_item

def process_request(prompt: str, source: str = "unknown") -> dict:
    """
    Main processing pipeline for autonomous agent
    Returns execution result with metadata
    """
    log(f"New request from {source}: {prompt[:80]}...")
    
    # Step 1: Autonomy analysis
    level, action, reason, confidence = analyze_request(prompt)
    log(f"Autonomy level: {level} | Action: {action} | Confidence: {confidence}")
    
    result = {
        "prompt": prompt,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "autonomy_level": level,
        "decision": action,
        "reason": reason,
        "confidence": confidence,
        "status": "pending"
    }
    
    # Step 2: Route based on autonomy level
    if level == "L5":  # Full autonomy
        log("Executing with full autonomy (L5)")
        
        # Classify for model selection
        routing = classify_request_phi3(prompt)
        
        # ENHANCED LOGGING: Capture routing decision
        log(f"[ROUTING] Decision: {routing['route']} | Model: {routing['model']} | Reason: {routing['reason']}")
        
        if routing["route"] == "delegate":
            # Spawn sub-agent for complex/multi-step tasks
            log(f"[ROUTING] Delegating to sub-agent: {routing['reason']}")
            sub_agent_result = spawn_sub_agent(prompt, routing["reason"])
            result["status"] = "delegated"
            result["sub_agent"] = sub_agent_result
            result["delegation_reason"] = routing["reason"]
            log(f"[ROUTING] Sub-agent spawned: {sub_agent_result.get('id', 'unknown')}")
            
        elif routing["route"] == "local":
            start_time = time.time()
            output = execute_local(prompt, routing["model"])
            elapsed = time.time() - start_time
            result["status"] = "completed"
            result["output"] = output
            result["model_used"] = routing["model"]
            result["personality"] = routing['reason']
            result["response_time"] = f"{elapsed:.1f}s"
            result["cost"] = "$0.00"
            log(f"[ROUTING] Completed | Model: {routing['model']} | Time: {elapsed:.1f}s | Personality: {routing['reason']}")
        elif routing["route"] == "escalate":
            # Check daily budget before API escalation
            budget_ok, remaining = check_budget()
            if not budget_ok:
                result["status"] = "budget_exceeded"
                result["message"] = f"Daily budget exceeded ($5). Spent: ${get_daily_spend():.2f}. Falling back to {GLOBAL_FALLBACK_MODEL}."
                result["fallback_model"] = GLOBAL_FALLBACK_MODEL
                log(f"[ROUTING] Budget exceeded! Fallback to {GLOBAL_FALLBACK_MODEL}")
                # Fallback to configured global model
                result["output"] = f"[FALLBACK to {GLOBAL_FALLBACK_MODEL}]"
                result["cost"] = "API_CALL_REQUIRED_FALLBACK"
            else:
                # Queue for API execution
                result["status"] = "queued_api"
                result["model_recommended"] = routing["model"]
                result["daily_spend"] = f"${get_daily_spend():.2f} / $5.00"
                log(f"[ROUTING] API Escalation | Model: {routing['model']} | Budget: ${remaining:.2f} remaining | Reason: {routing['reason']}")
        
    elif level == "L4":  # Standard autonomy (notify after)
        log("Executing with standard autonomy (L4)")
        
        routing = classify_request_phi3(prompt)
        
        if routing["route"] == "local":
            output = execute_local(prompt, routing["model"])
            result["status"] = "completed"
            result["output"] = output
            result["notification"] = "Action completed - see output above"
            log("Completed - notification sent")
        else:
            result["status"] = "queued_api"
            result["notification"] = "Queued for API execution"
        
    elif level in ["L3", "L2", "L1"]:  # Requires approval
        log(f"Requires approval ({level})")
        approval_item = queue_for_approval(prompt, level, reason)
        result["status"] = "awaiting_approval"
        result["approval_id"] = approval_item["id"]
        result["message"] = format_approval_request(prompt, level, reason)
        log(f"Awaiting approval: {approval_item['id']}")
    
    return result

def classify_request_phi3(prompt: str) -> dict:
    """
    Task Routing Matrix - Personality-based model selection
    Routes to optimal model based on task type and required personality
    """
    prompt_lower = prompt.lower()
    
    # === DELEGATION CHECK (Multi-step / Parallel tasks) ===
    delegation_indicators = [
        (r'\band\b.*\band\b', "Multiple parallel tasks"),
        (r'(research|analyze|check).*(and|then).*(write|create|generate)', "Multi-step workflow"),
        (r'(monitor|watch).*(for|24|hour|day)', "Long-running monitoring"),
        (r'(all|every|each).*(file|document|post|email)', "Batch processing"),
        (r'(refactor|rewrite|reorganize).*(entire|all|project|codebase)', "Large codebase work"),
        (r'(write|create|generate).*(10|20|\d+).*(posts|emails|documents)', "Bulk content creation"),
        (r'(process|analyze).*(100|1000|\d{3,}).*(rows|records|items)', "Large data processing"),
    ]
    
    for pattern, reason in delegation_indicators:
        if re.search(pattern, prompt_lower):
            return {
                "route": "delegate",
                "action": "SPAWN_SUB_AGENT",
                "model": "sub-agent",
                "reason": reason,
                "parent_task": prompt
            }
    
    # === EXPLICIT API ESCALATION (User requested) ===
    explicit_api_triggers = [
        (r'\b(use\s+)?kimi\b', "Explicit Kimi request", "moonshot/kimi-k2.5"),
        (r'\b(use\s+)?gpt-?4\b', "Explicit GPT-4 request", "openai/gpt-4o"),
        (r'\b(use\s+)?codex\b', "Explicit Codex request", "openai-codex/gpt-5.3-codex"),
        (r'\b(use\s+)?api\b', "Explicit API request", "moonshot/kimi-k2.5"),
    ]
    
    for pattern, reason, model in explicit_api_triggers:
        if re.search(pattern, prompt_lower):
            return {"route": "escalate", "model": model, "reason": reason}
    
    # === PERSONALITY-BASED ROUTING (Local Models) ===
    
    # 1. MULTIMODAL / VISION (Qwen 3.5-4B - The Integrator)
    # Only model with vision capabilities
    if any(kw in prompt_lower for kw in ["image", "chart", "diagram", "screenshot", "document", "ocr", "scan", "photo", "picture"]):
        return {"route": "local", "model": "qwen3.5:4b", "reason": "Multimodal task - vision + text (The Integrator)"}
    
    # 2. CODE / TECHNICAL (DeepSeek 6.7B - The Engineer)
    # Refuses advisory, pure implementation
    if any(kw in prompt_lower for kw in ["code", "function", "script", "program", "python", "debug", "error", "implement", "build", "develop"]):
        return {"route": "local", "model": "deepseek-coder:6.7b", "reason": "Coding task - implementation focused (The Engineer)"}
    
    # 3. ETHICAL DILEMMA / EXPLORATION (Qwen 3:14B - The Philosopher)
    # Thinks out loud, explores nuance, questions assumptions
    if any(kw in prompt_lower for kw in ["ethical", "dilemma", "not sure", "explore", "philosophy", "moral", "uncertain", "complex trade", "think through"]):
        return {"route": "local", "model": "qwen3:14b", "reason": "Ethical exploration - deliberative reasoning (The Philosopher)"}
    
    # 4. CHALLENGE / CONTRARIAN / DATA-DRIVEN (Qwen 3.5-9B - The Contrarian)
    # Only model that chose A vs B, challenges groupthink
    if any(kw in prompt_lower for kw in ["challenge", "contrarian", "what if", "opposite", "counter", "evidence", "data shows", "alternative view"]):
        return {"route": "local", "model": "qwen3.5:9b", "reason": "Contrarian analysis - challenge assumptions (The Data Analyst)"}
    
    # 5. BUSINESS STRATEGY / FAST EXECUTIVE (Phi-3 Mini - The Strategist)
    # 20s, ROI-focused, structured, board-ready
    if any(kw in prompt_lower for kw in ["strategy", "business", "roi", "fundraising", "board", "executive", "investor", "stakeholder", "quick analysis", "fast check"]):
        return {"route": "local", "model": "phi3:mini", "reason": "Business strategy - fast executive framing (The Strategist)"}
    
    # 6. NARRATIVE / STORY / ENGAGEMENT (Llama 3.1 8B - The Visionary)
    # Emotional resonance, storytelling, mission alignment
    if any(kw in prompt_lower for kw in ["story", "narrative", "engage", "inspire", "move", "audience", "donor letter", "pitch", "vision", "mission"]):
        return {"route": "local", "model": "llama3.1:8b", "reason": "Narrative task - emotional resonance (The Visionary)"}
    
    # 7. BALANCED / PRAGMATIC / MIDDLE GROUND (Qwen 3.5-2B - The Pragmatist)
    # Practical considerations, implementation focus
    if any(kw in prompt_lower for kw in ["balanced", "pragmatic", "realistic", "implement", "practical", "middle ground", "compromise", "feasible"]):
        return {"route": "local", "model": "qwen3.5:2b", "reason": "Balanced analysis - pragmatic approach (The Pragmatist)"}
    
    # 8. ULTRA-FAST TRIAGE (Qwen 3.5-0.8B - The Rapid Analyst)
    # <2s responses, quick assessments
    if any(kw in prompt_lower for kw in ["triage", "quick check", "brief", "summary", "overview", "status", "update"]):
        return {"route": "local", "model": "qwen3.5:0.8b", "reason": "Ultra-fast triage - rapid assessment (The Rapid Analyst)"}
    
    # 9. ANALYSIS / RESEARCH / Q&A (Default to Qwen 3:14B or 9B based on complexity)
    if any(kw in prompt_lower for kw in ["analyze", "research", "explain", "compare", "evaluate", "assess"]):
        # Use 9B for complex analysis, 14B for exploratory
        if any(kw in prompt_lower for kw in ["complex", "deep", "thorough", "comprehensive"]):
            return {"route": "local", "model": "qwen3.5:9b", "reason": "Complex analysis - deep reasoning (The Data Analyst)"}
        else:
            return {"route": "local", "model": "qwen3:14b", "reason": "Analysis task - exploratory reasoning (The Philosopher)"}
    
    # 10. WRITING / CONTENT (Default to Llama 3.1 8B - The Visionary)
    if any(kw in prompt_lower for kw in ["write", "draft", "email", "blog", "content", "letter", "post", "article"]):
        return {"route": "local", "model": "llama3.1:8b", "reason": "Writing task - narrative voice (The Visionary)"}
    
    # DEFAULT: Phi-3 Mini for general tasks (fast, efficient)
    return {"route": "local", "model": "phi3:mini", "reason": "General task - fast classification (The Strategist)"}

def spawn_sub_agent(prompt: str, reason: str) -> dict:
    """Spawn a sub-agent for complex/multi-step tasks"""
    import subprocess
    import uuid
    
    sub_agent_id = f"sub-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    # Create sub-agent task file
    task_file = Path.home() / ".openclaw" / "run" / f"{sub_agent_id}.json"
    task = {
        "id": sub_agent_id,
        "type": "sub_agent",
        "parent_prompt": prompt,
        "delegation_reason": reason,
        "created_at": datetime.now().isoformat(),
        "status": "spawning",
        "autonomy_level": "L5",
        "can_spawn_children": True,
        "max_depth": 2
    }
    
    with open(task_file, "w") as f:
        json.dump(task, f, indent=2)
    
    # Spawn sub-agent via sessions_spawn
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "spawn", "--task", prompt, 
             "--label", sub_agent_id, "--mode", "run", "--timeout", "3600"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "id": sub_agent_id,
            "status": "spawned",
            "task_file": str(task_file),
            "reason": reason,
            "message": f"Sub-agent {sub_agent_id} spawned for: {reason}"
        }
    except Exception as e:
        return {
            "id": sub_agent_id,
            "status": "error",
            "error": str(e),
            "fallback": "Executing in main agent"
        }

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    DAILY_SPEND_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for summary command
    if len(sys.argv) > 1 and sys.argv[1] in ['--summary', '-s', 'stats']:
        log_routing_summary()
        sys.exit(0)
    
    # Check for budget command
    if len(sys.argv) > 1 and sys.argv[1] in ['--budget', '-b', 'budget']:
        spent = get_daily_spend()
        remaining = DAILY_BUDGET - spent
        print(f"Daily Budget: ${spent:.2f} / $5.00 spent")
        print(f"Remaining: ${remaining:.2f}")
        print(f"Status: {'OK' if remaining > 0 else 'EXCEEDED'}")
        sys.exit(0)
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        source = "cli"
    else:
        # Read from stdin
        prompt = sys.stdin.read().strip()
        source = "stdin"
    
    if prompt:
        result = process_request(prompt, source)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: autonomous-agent 'your prompt'")
        print("   or: echo 'prompt' | autonomous-agent")
        print("   or: autonomous-agent --summary (routing stats)")
        print("   or: autonomous-agent --budget (spend tracking)")
