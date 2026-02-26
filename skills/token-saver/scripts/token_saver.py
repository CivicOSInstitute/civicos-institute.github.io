#!/usr/bin/env python3
"""
token-saver: Intelligent model selection with Kimi K2.5 as primary.
Uses K2.5 by default; only falls back when K2.5 unsuitable (context limits, quotas).
Local models are last-resort fallback when APIs unavailable.

Usage:
  token-saver select "<task description>" [--tokens <est_tokens>]
  token-saver rank [--by <cost|capability|efficiency>]
  token-saver models [--local-only|--api-only]
  token-saver config --primary-model <model_id>
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
import argparse

class TaskComplexity(Enum):
    TRIVIAL = 1      # Simple Q&A, formatting
    SIMPLE = 2       # Basic analysis, summarization
    MODERATE = 3     # Multi-step reasoning, code review
    COMPLEX = 4      # Complex analysis, creative writing
    EXPERT = 5       # Research, synthesis, advanced coding

class TaskType(Enum):
    CHAT = "chat"
    SUMMARIZE = "summarize"
    CODE = "code"
    ANALYZE = "analyze"
    CREATIVE = "creative"
    RESEARCH = "research"
    TRANSLATE = "translate"
    EXTRACT = "extract"
    CLASSIFY = "classify"
    DEBUG = "debug"

@dataclass
class ModelSpec:
    id: str
    name: str
    provider: str
    local: bool
    context_window: int
    complexity_max: TaskComplexity
    strengths: List[str]
    weaknesses: List[str]
    cost_per_1k_input: float
    cost_per_1k_output: float
    speed: str  # fast/medium/slow
    reliability: float  # 0-1

# Define all known models
MODEL_REGISTRY = {
    # Local Models (Ollama) - FREE PRIORITY
    "qwen3:14b": ModelSpec(
        id="qwen3:14b",
        name="Qwen 3 14B",
        provider="ollama",
        local=True,
        context_window=32768,
        complexity_max=TaskComplexity.COMPLEX,
        strengths=["chat", "code", "analyze", "summarize", "translate", "extract"],
        weaknesses=["research", "creative", "expert reasoning"],
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        speed="fast",
        reliability=0.85
    ),
    "qwen2.5-coder:32b-instruct-q3_K_L": ModelSpec(
        id="qwen2.5-coder:32b-instruct-q3_K_L",
        name="Qwen 2.5 Coder 32B",
        provider="ollama",
        local=True,
        context_window=131072,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["code", "debug", "analyze", "chat", "long context"],
        weaknesses=["creative", "research", "very slow - background tasks only"],
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        speed="slow",  # 32B model - very slow on MacBook
        reliability=0.88
    ),
    "mistral-small3.2:24b": ModelSpec(
        id="mistral-small3.2:24b",
        name="Mistral Small 3.2 24B",
        provider="ollama",
        local=True,
        context_window=32768,
        complexity_max=TaskComplexity.COMPLEX,
        strengths=["chat", "analyze", "code", "classify", "summarize"],
        weaknesses=["creative", "research", "long context"],
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        speed="fast",
        reliability=0.82
    ),
    "llama3.3:70b": ModelSpec(
        id="llama3.3:70b",
        name="Llama 3.3 70B",
        provider="ollama",
        local=True,
        context_window=128000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["chat", "code", "analyze", "research", "creative", "debug"],
        weaknesses=["very slow on local hardware"],
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        speed="slow",
        reliability=0.88
    ),
    "gemma2:27b": ModelSpec(
        id="gemma2:27b",
        name="Gemma 2 27B",
        provider="ollama",
        local=True,
        context_window=8192,
        complexity_max=TaskComplexity.MODERATE,
        strengths=["chat", "summarize", "classify"],
        weaknesses=["code", "complex reasoning", "research"],
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        speed="medium",
        reliability=0.78
    ),
    
    # API Models (Paid)
    "gpt-4o-mini": ModelSpec(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        local=False,
        context_window=128000,
        complexity_max=TaskComplexity.MODERATE,
        strengths=["chat", "summarize", "extract", "classify", "simple code"],
        weaknesses=["complex reasoning", "research", "expert tasks"],
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        speed="fast",
        reliability=0.90
    ),
    "gpt-4o": ModelSpec(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        local=False,
        context_window=128000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["chat", "code", "analyze", "creative", "research", "debug", "vision"],
        weaknesses=["costly for simple tasks"],
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        speed="fast",
        reliability=0.94
    ),
    "claude-3-haiku": ModelSpec(
        id="claude-3-haiku",
        name="Claude 3 Haiku",
        provider="anthropic",
        local=False,
        context_window=200000,
        complexity_max=TaskComplexity.MODERATE,
        strengths=["chat", "summarize", "long context", "extract"],
        weaknesses=["complex reasoning", "code", "creative"],
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        speed="very fast",
        reliability=0.88
    ),
    "claude-3-sonnet": ModelSpec(
        id="claude-3-sonnet",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        local=False,
        context_window=200000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["chat", "code", "analyze", "research", "creative", "long context"],
        weaknesses=["cost"],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        speed="fast",
        reliability=0.93
    ),
    "claude-3-opus": ModelSpec(
        id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        local=False,
        context_window=200000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["research", "complex analysis", "expert reasoning", "creative", "code"],
        weaknesses=["expensive", "slow"],
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        speed="slow",
        reliability=0.95
    ),
    "kimi-k2.5": ModelSpec(
        id="kimi-k2.5",
        name="Kimi K2.5",
        provider="moonshot",
        local=False,
        context_window=256000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["chat", "analyze", "code", "long context", "research"],
        weaknesses=["creative tasks"],
        cost_per_1k_input=0.002,
        cost_per_1k_output=0.008,
        speed="fast",
        reliability=0.91
    ),
    "gemini-1.5-flash": ModelSpec(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        local=False,
        context_window=1000000,
        complexity_max=TaskComplexity.MODERATE,
        strengths=["chat", "summarize", "very long context", "extract"],
        weaknesses=["complex reasoning", "code", "creative"],
        cost_per_1k_input=0.00035,
        cost_per_1k_output=0.00105,
        speed="very fast",
        reliability=0.87
    ),
    "gemini-1.5-pro": ModelSpec(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        local=False,
        context_window=2000000,
        complexity_max=TaskComplexity.EXPERT,
        strengths=["chat", "analyze", "research", "very long context", "multimodal"],
        weaknesses=["consistency"],
        cost_per_1k_input=0.0035,
        cost_per_1k_output=0.0105,
        speed="medium",
        reliability=0.89
    ),
}

# Task classification patterns
TASK_PATTERNS = {
    TaskType.SUMMARIZE: ["summarize", "summary", "tl;dr", "tldr", "condense", "brief"],
    TaskType.CODE: ["code", "program", "function", "script", "debug", "refactor", "implement"],
    TaskType.ANALYZE: ["analyze", "analysis", "compare", "evaluate", "assess", "review"],
    TaskType.RESEARCH: ["research", "investigate", "find", "search", "explore", "synthesize"],
    TaskType.CREATIVE: ["write", "creative", "story", "poem", "draft", "compose", "generate content"],
    TaskType.TRANSLATE: ["translate", "translation", "convert language", "in spanish", "in french"],
    TaskType.EXTRACT: ["extract", "pull out", "find in", "get from", "parse"],
    TaskType.CLASSIFY: ["classify", "categorize", "label", "tag", "sort"],
    TaskType.DEBUG: ["fix", "debug", "error", "bug", "broken", "not working"],
    TaskType.CHAT: ["chat", "talk", "conversation", "discuss"],
}

class TokenSaver:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.openclaw/token-saver")
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config = self._load_config()
        self.available_local_models = self._get_available_local_models()
    
    def _load_config(self) -> dict:
        """Load or create config."""
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                return json.load(f)
        default = {
            "primary_model": "kimi-k2.5",  # Always use K2.5 unless can't handle task
            "fallback_order": ["claude-3-sonnet", "gpt-4o", "gemini-1.5-pro"],  # If K2.5 fails
            "local_fallback": True,  # Use local only if all APIs fail
        }
        with open(self.config_file, "w") as f:
            json.dump(default, f, indent=2)
        return default
    
    def _get_available_local_models(self) -> List[str]:
        """Detect which Ollama models are available."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                models = []
                for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                    parts = line.split()
                    if parts:
                        model_name = parts[0].split(":")[0]
                        models.append(parts[0])
                return models
        except Exception:
            pass
        return []
    
    def classify_task(self, task: str) -> tuple[TaskType, TaskComplexity]:
        """Classify task type and complexity."""
        task_lower = task.lower()
        
        # Determine task type
        detected_type = TaskType.CHAT
        for task_type, patterns in TASK_PATTERNS.items():
            if any(p in task_lower for p in patterns):
                detected_type = task_type
                break
        
        # Estimate complexity based on task characteristics
        complexity = TaskComplexity.SIMPLE
        
        # Length/complexity indicators
        word_count = len(task.split())
        if word_count > 500:
            complexity = TaskComplexity(complexity.value + 1)
        if word_count > 1000:
            complexity = TaskComplexity(complexity.value + 1)
        
        # Complexity keywords
        expert_indicators = [
            "novel", "byzantine", "fault tolerance", "formal verification",
            "distributed systems", "consensus algorithm", "phd", "doctoral",
            "groundbreaking", "invention", "theorem", "proof"
        ]
        complex_indicators = [
            "research", "synthesize", "complex", "detailed", "comprehensive",
            "compare and contrast", "in-depth", "thorough", "expert analysis",
            "architect", "design system", "algorithm design", "optimize"
        ]
        
        if any(ind in task_lower for ind in expert_indicators):
            complexity = TaskComplexity.EXPERT
        elif any(ind in task_lower for ind in complex_indicators):
            complexity = TaskComplexity(min(complexity.value + 1, 5))
        
        # Code complexity
        if detected_type == TaskType.CODE:
            code_indicators = ["architect", "design", "system", "framework", "library"]
            if any(ind in task_lower for ind in code_indicators):
                complexity = TaskComplexity.COMPLEX
        
        # Research is inherently complex
        if detected_type == TaskType.RESEARCH:
            complexity = TaskComplexity(max(complexity.value, TaskComplexity.COMPLEX.value))
        
        return detected_type, complexity
    
    def select_model(self, task: str, estimated_tokens: int = 1000,
                     require_certainty: bool = False, background_task: bool = False) -> dict:
        """Select optimal model for task."""
        task_type, complexity = self.classify_task(task)
        
        # Get candidate models that can handle this complexity
        candidates = []
        for model_id, spec in MODEL_REGISTRY.items():
            # Check if local model is actually available
            if spec.local:
                if not any(spec.id in avail or avail in spec.id for avail in self.available_local_models):
                    continue
            
            # Check complexity match
            if spec.complexity_max.value >= complexity.value:
                candidates.append(spec)
        
        if not candidates:
            # Fallback to most capable API model
            candidates = [MODEL_REGISTRY["gpt-4o"], MODEL_REGISTRY["claude-3-opus"]]
        
        # Score candidates
        scored = []
        for spec in candidates:
            score = self._score_model(spec, task_type, complexity, estimated_tokens, background_task)
            scored.append((score, spec))
        
        # Sort by score (descending)
        scored.sort(reverse=True, key=lambda x: x[0])
        
        best = scored[0][1]
        
        return {
            "selected_model": best.id,
            "provider": best.provider,
            "local": best.local,
            "cost_estimate": self._estimate_cost(best, estimated_tokens),
            "task_type": task_type.value,
            "complexity": complexity.name,
            "confidence": scored[0][0],
            "alternatives": [s.id for _, s in scored[1:3]],
            "reasoning": self._explain_selection(best, task_type, complexity, estimated_tokens)
        }
    
    def _score_model(self, spec: ModelSpec, task_type: TaskType, 
                     complexity: TaskComplexity, tokens: int, 
                     background_task: bool = False) -> float:
        """Score a model for the task. Higher = better match.
        
        PRIORITY ORDER:
        1. Kimi K2.5 (primary model) - ALWAYS preferred unless can't handle task
        2. Other API models - Only if K2.5 can't handle (context/quotas)
        3. Local models - Last resort when APIs unavailable
        4. Qwen 2.5 Coder 32B - Background tasks ONLY (very slow)
        """
        score = 0.0
        
        # Qwen 2.5 Coder 32B is VERY SLOW - only for background tasks during off-peak hours
        if spec.id == "qwen2.5-coder:32b-instruct-q3_K_L":
            current_hour = datetime.now().hour
            # Off-peak hours: 10 PM - 8 AM (when more resources available)
            is_off_peak = current_hour >= 22 or current_hour < 8
            
            if background_task and is_off_peak:
                score += 200  # OK for background tasks during off-peak hours
            else:
                score -= 5000  # NEVER use for interactive tasks or during peak hours - too slow
        
        # PRIMARY MODEL: Kimi K2.5 gets massive priority
        elif spec.id == "kimi-k2.5":
            score += 5000  # Dominant priority - use K2.5 for everything it can handle
            # K2.5 has 256K context, good at most tasks
            if task_type.value in spec.strengths:
                score += 50
        
        # Local models are LAST RESORT - only when APIs unavailable
        elif spec.local:
            score += 50  # Small bonus only - prefer APIs (especially K2.5)
            if spec.speed == "fast":
                score += 10
        
        # Other API models - only use if K2.5 can't handle
        else:
            score += 100  # Base API score - way below K2.5's 5000
        
        # Task strength match
        if task_type.value in spec.strengths:
            score += 20
        
        # Complexity match (closer = better, but must meet minimum)
        complexity_diff = spec.complexity_max.value - complexity.value
        if complexity_diff >= 0:
            score += 15 - (complexity_diff * 2)
        else:
            score -= 1000  # Heavy penalty for insufficient capability
        
        # Reliability
        score += spec.reliability * 10
        
        # Context window - CRITICAL for K2.5 fallback decisions
        if tokens > spec.context_window * 0.9:
            score -= 5000  # Don't use if context exceeded
        elif tokens > spec.context_window * 0.7:
            score -= 100  # Getting tight
        
        return score
    
    def _estimate_cost(self, spec: ModelSpec, tokens: int) -> float:
        """Estimate cost for given token count."""
        if spec.local:
            return 0.0
        # Assume 70/30 input/output split
        input_cost = (tokens * 0.7 / 1000) * spec.cost_per_1k_input
        output_cost = (tokens * 0.3 / 1000) * spec.cost_per_1k_output
        return round(input_cost + output_cost, 4)
    
    def _explain_selection(self, spec: ModelSpec, task_type: TaskType,
                          complexity: TaskComplexity, tokens: int = 1000) -> str:
        """Generate human-readable explanation."""
        reasons = []
        
        if spec.id == "kimi-k2.5":
            reasons.append("Primary model (K2.5)")
        elif spec.local:
            reasons.append("Fallback - local model (APIs unavailable)")
        else:
            reasons.append(f"Fallback - {spec.name}")
        
        # Explain why fallback happened
        k2 = MODEL_REGISTRY.get("kimi-k2.5")
        if k2 and spec.id != "kimi-k2.5":
            if tokens > k2.context_window * 0.8:
                reasons.append(f"K2.5 context limit exceeded ({k2.context_window:,} tokens)")
            else:
                reasons.append("K2.5 quota exhausted or unavailable")
        
        # Special note for Qwen 2.5 Coder 32B
        if spec.id == "qwen2.5-coder:32b-instruct-q3_K_L":
            current_hour = datetime.now().hour
            if current_hour >= 22 or current_hour < 8:
                reasons.append("Off-peak hours (10 PM - 8 AM)")
            else:
                reasons.append("WARNING: Peak hours - very slow")
        
        if task_type.value in spec.strengths:
            reasons.append(f"Strong at {task_type.value}")
        
        if spec.complexity_max.value >= complexity.value:
            reasons.append(f"Can handle {complexity.name} complexity")
        
        return "; ".join(reasons)
    
    def rank_models(self, by: str = "efficiency") -> List[dict]:
        """Rank all available models."""
        models = []
        for model_id, spec in MODEL_REGISTRY.items():
            # Skip unavailable local models
            if spec.local and not any(spec.id in avail or avail in spec.id 
                                     for avail in self.available_local_models):
                continue
            
            models.append({
                "id": spec.id,
                "name": spec.name,
                "provider": spec.provider,
                "local": spec.local,
                "cost_per_1k": f"${(spec.cost_per_1k_input + spec.cost_per_1k_output)/2:.4f}" if not spec.local else "FREE",
                "context": spec.context_window,
                "max_complexity": spec.complexity_max.name,
                "strengths": spec.strengths[:3],
                "speed": spec.speed,
            })
        
        # Sort based on criteria
        if by == "cost":
            models.sort(key=lambda x: 0 if x["local"] else float(x["cost_per_1k"].replace("$", "")))
        elif by == "capability":
            complexity_order = {"TRIVIAL": 1, "SIMPLE": 2, "MODERATE": 3, "COMPLEX": 4, "EXPERT": 5}
            models.sort(key=lambda x: complexity_order.get(x["max_complexity"], 0), reverse=True)
        elif by == "efficiency":
            # Score: capability per dollar (local models always win)
            def efficiency_score(m):
                complexity_order = {"TRIVIAL": 1, "SIMPLE": 2, "MODERATE": 3, "COMPLEX": 4, "EXPERT": 5}
                cap = complexity_order.get(m["max_complexity"], 1)
                if m["local"]:
                    return cap * 1000  # Huge bonus for free
                cost = float(m["cost_per_1k"].replace("$", "")) if "$" in m["cost_per_1k"] else 0.0001
                return cap / cost
            models.sort(key=efficiency_score, reverse=True)
        
        return models

def main():
    parser = argparse.ArgumentParser(description="Token Saver - Smart Model Selection")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Select command
    select_parser = subparsers.add_parser("select", help="Select best model for task")
    select_parser.add_argument("task", help="Task description")
    select_parser.add_argument("--tokens", type=int, default=1000, help="Estimated token count")
    select_parser.add_argument("--background", action="store_true", help="Background task (allows slow models)")
    select_parser.add_argument("--json", action="store_true", help="Output JSON")
    
    # Rank command
    rank_parser = subparsers.add_parser("rank", help="Rank available models")
    rank_parser.add_argument("--by", choices=["cost", "capability", "efficiency"], 
                            default="efficiency", help="Sort criteria")
    
    # Models command
    models_parser = subparsers.add_parser("models", help="List available models")
    models_parser.add_argument("--local-only", action="store_true")
    models_parser.add_argument("--api-only", action="store_true")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configure token-saver")
    config_parser.add_argument("--local-priority", choices=["true", "false"],
                              help="Prioritize local models")
    
    args = parser.parse_args()
    saver = TokenSaver()
    
    if args.command == "select":
        result = saver.select_model(args.task, args.tokens, background_task=args.background)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n🎯 Selected: {result['selected_model']}")
            print(f"   Provider: {result['provider']}")
            print(f"   Local: {'✓ YES (FREE)' if result['local'] else '✗ API ($)'}")
            print(f"   Est. cost: ${result['cost_estimate']:.4f}")
            print(f"   Task type: {result['task_type']}")
            print(f"   Complexity: {result['complexity']}")
            print(f"   Why: {result['reasoning']}")
            if result['alternatives']:
                print(f"   Alternatives: {', '.join(result['alternatives'])}")
    
    elif args.command == "rank":
        models = saver.rank_models(by=args.by)
        print(f"\n📊 Model Rankings (by {args.by})")
        print(f"{'Rank':<5} {'Model':<25} {'Provider':<12} {'Cost/1K':<10} {'Complexity':<10} {'Speed':<10}")
        print("-" * 75)
        for i, m in enumerate(models[:10], 1):
            local_mark = "🟢 " if m["local"] else "💰 "
            print(f"{i:<5} {local_mark}{m['name'][:22]:<22} {m['provider']:<12} "
                  f"{m['cost_per_1k']:<10} {m['max_complexity']:<10} {m['speed']:<10}")
    
    elif args.command == "models":
        print(f"\n🤖 Available Models")
        print(f"Local models detected: {saver.available_local_models or 'None'}")
        print()
        for model_id, spec in MODEL_REGISTRY.items():
            if args.local_only and not spec.local:
                continue
            if args.api_only and spec.local:
                continue
            
            available = "✓" if not spec.local or any(spec.id in avail or avail in spec.id 
                                                     for avail in saver.available_local_models) else "✗"
            cost = "FREE" if spec.local else f"${(spec.cost_per_1k_input + spec.cost_per_1k_output)/2:.4f}/1K"
            print(f"  [{available}] {spec.name:<30} {cost:<15} {spec.complexity_max.name}")
    
    elif args.command == "config":
        if args.local_priority:
            saver.config["local_priority"] = args.local_priority == "true"
            with open(saver.config_file, "w") as f:
                json.dump(saver.config, f, indent=2)
            print(f"✓ local_priority set to {args.local_priority}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
