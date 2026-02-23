#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


def fail(msg):
    print(f"FAIL: {msg}")
    return False


def ok(msg):
    print(f"OK: {msg}")
    return True


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return None
    block = m.group(1)
    data = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    return data


def validate(skill_dir: Path) -> int:
    errors = 0
    skill_md = skill_dir / "SKILL.md"

    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"FAIL: skill directory not found: {skill_dir}")
        return 1

    if not skill_md.exists():
        print("FAIL: missing SKILL.md")
        return 1

    text = skill_md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        errors += 1
        fail("SKILL.md missing YAML frontmatter block")
    else:
        if set(fm.keys()) != {"name", "description"}:
            errors += 1
            fail(f"frontmatter keys must be exactly name/description, got: {sorted(fm.keys())}")
        else:
            ok("frontmatter keys valid")

        name = fm.get("name", "")
        if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
            errors += 1
            fail("frontmatter name must match [a-z0-9-]{1,64}")
        else:
            ok("name format valid")

        desc = fm.get("description", "")
        if len(desc) < 16:
            errors += 1
            fail("description too short; include what it does and when to use it")
        else:
            ok("description length looks good")

    folder_name = skill_dir.name
    if not re.fullmatch(r"[a-z0-9-]{1,64}", folder_name):
        errors += 1
        fail("folder name must be lowercase hyphen-case")
    else:
        ok("folder name format valid")

    if (skill_dir / "README.md").exists():
        ok("README.md present (optional)")

    # Warn on noisy docs
    for noisy in ["INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CHANGELOG.md"]:
      if (skill_dir / noisy).exists():
          print(f"WARN: remove non-essential file {noisy}")

    if errors:
        print(f"\nValidation failed with {errors} error(s).")
        return 1
    print("\nValidation passed.")
    return 0


def main():
    p = argparse.ArgumentParser(description="Validate skill structure and frontmatter")
    p.add_argument("skill_dir", help="Path to skill directory")
    args = p.parse_args()
    raise SystemExit(validate(Path(args.skill_dir).expanduser().resolve()))


if __name__ == "__main__":
    main()
