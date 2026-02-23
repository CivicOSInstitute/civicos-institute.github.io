---
name: skill-creator
description: Create new AgentSkills from a short description, including valid SKILL.md frontmatter, correct directory structure, optional scripts/references/assets folders, examples, and packaging/validation helpers. Use when a user asks to build a new skill quickly and consistently.
---

# Skill Creator

Generate a complete skill scaffold from a short prompt.

## Core workflow

1. Normalize the requested skill name to lowercase hyphen-case.
2. Create folder: `<output_dir>/<skill-name>/`.
3. Generate `SKILL.md` with required frontmatter fields only:
   - `name`
   - `description`
4. Add optional resource folders as needed:
   - `scripts/`
   - `references/`
   - `assets/`
5. Add starter examples for input/output contracts and edge-case handling.
6. Return next commands for validate/package.

## Use the scaffold script

Run:

```bash
python3 scripts/create_skill.py \
  --name "stock-checker" \
  --description "Check stock prices and summarize changes" \
  --output-dir ~/.openclaw/workspace/skills \
  --resources scripts,references,assets \
  --with-examples \
  --with-readme
```

## Validate and package

```bash
python3 scripts/validate_skill.py ~/.openclaw/workspace/skills/stock-checker
python3 scripts/package_skill.py ~/.openclaw/workspace/skills/stock-checker --out-dir ~/.openclaw/workspace/skills
```

One-command create + package:

```bash
bash scripts/create_and_package.sh "Stock Checker" "Check stock prices and summarize moves"
```

## Input pattern

- Skill name
- One-line purpose
- Optional resources
- Optional examples flag

## Output guarantees

- Correct skill directory structure
- Valid SKILL.md frontmatter format
- Practical starter instructions for the generated skill
- Helper files for quick iteration

## Edge-case handling

- If name has spaces/symbols, normalize to hyphen-case.
- If destination exists, fail unless `--force` is passed.
- If description is empty, fail with actionable error.
- If resource list is invalid, show accepted values.
