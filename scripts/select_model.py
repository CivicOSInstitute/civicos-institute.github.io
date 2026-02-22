#!/usr/bin/env python3
import argparse


def select_model(task: str, priority: str = "normal") -> str:
    t = (task or "").lower()

    # High-confidence technical escalation
    if any(k in t for k in ["debug", "bug", "fix", "refactor", "script", "automation", "deploy", "infra", "database", "docker", "ci", "build"]):
        return "Codex"

    # Research
    if any(k in t for k in ["research", "compare", "scan", "summarize", "analyze"]):
        return "Qwen" if priority != "high" else "Gemini"

    # Writing/comms
    if any(k in t for k in ["email", "post", "copy", "announcement", "draft", "proposal"]):
        return "Qwen" if priority != "high" else "GPT-4o"

    # Default local-first
    return "Qwen"


def main():
    p = argparse.ArgumentParser(description="Select model alias using local-first matrix")
    p.add_argument("task", help="Task description")
    p.add_argument("--priority", choices=["low", "normal", "high"], default="normal")
    args = p.parse_args()
    print(select_model(args.task, args.priority))


if __name__ == "__main__":
    main()
