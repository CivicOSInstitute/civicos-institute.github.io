#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="Validate and package a skill into .skill zip")
    p.add_argument("skill_dir", help="Path to skill directory")
    p.add_argument("--out-dir", default=".", help="Output directory for .skill file")
    args = p.parse_args()

    here = Path(__file__).resolve().parent
    validator = here / "validate_skill.py"
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # run validator
    rc = shutil.which("python3")
    if not rc:
        print("python3 not found")
        raise SystemExit(1)

    import subprocess
    v = subprocess.run([rc, str(validator), str(skill_dir)])
    if v.returncode != 0:
        raise SystemExit(v.returncode)

    base_name = out_dir / skill_dir.name
    archive = shutil.make_archive(str(base_name), "zip", root_dir=str(skill_dir.parent), base_dir=skill_dir.name)
    skill_archive = str(base_name) + ".skill"
    Path(archive).replace(skill_archive)
    print(f"Packaged: {skill_archive}")


if __name__ == "__main__":
    main()
