#!/usr/bin/env python3
import sys

task = ' '.join(sys.argv[1:]).lower().strip()
if not task:
    print('Usage: recommend_subagent_model.py "task description"')
    sys.exit(1)

code_kw = ['code','debug','refactor','script','python','javascript','playwright','automation','bug','regex','selector']
rewrite_kw = ['rewrite','polish','rephrase','tighten','style','copy edit','tone']
research_kw = ['research','scan','summarize','brief','monitor','digest','analysis','report']

if any(k in task for k in code_kw):
    print('qwen2.5-coder:32b-instruct-q3_K_L')
elif any(k in task for k in rewrite_kw):
    print('mistral-small3.2:24b-instruct-2506-q4_K_M')
elif any(k in task for k in research_kw):
    print('qwen2.5:14b')
else:
    print('qwen2.5:14b')
