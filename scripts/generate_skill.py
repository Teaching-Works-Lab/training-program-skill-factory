"""Generate one portable syllabus Skill from a validated program JSON file."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


FACTORY_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = FACTORY_ROOT / "templates" / "syllabus-skill"
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _replace_tokens(path: Path, *, skill_name: str, display_name: str) -> None:
    if path.suffix not in {".md", ".yaml"}:
        return
    text = path.read_text(encoding="utf-8")
    text = text.replace("{{SKILL_NAME}}", skill_name).replace("{{DISPLAY_NAME}}", display_name)
    path.write_text(text, encoding="utf-8")


def generate_skill(
    program_path: Path | str,
    output_dir: Path | str,
    *,
    skill_name: str,
    display_name: str,
    factory_commit: str,
) -> Path:
    """Copy the one syllabus template, substitute its identity, and bundle program data."""
    if not SKILL_NAME_PATTERN.fullmatch(skill_name):
        raise ValueError("skill_name must use lowercase letters, numbers, and hyphens")
    if not display_name.strip():
        raise ValueError("display_name must not be blank")
    if not factory_commit.strip():
        raise ValueError("factory_commit must not be blank")

    source = Path(program_path)
    program = json.loads(source.read_text(encoding="utf-8-sig"))
    if not isinstance(program, dict) or not isinstance(program.get("schema_version"), str):
        raise ValueError("program_path must contain a program JSON object with schema_version")

    output = Path(output_dir)
    shutil.copytree(TEMPLATE_ROOT, output)
    for candidate in output.rglob("*"):
        if candidate.is_file():
            _replace_tokens(candidate, skill_name=skill_name, display_name=display_name)

    data_dir = output / "data"
    data_dir.mkdir()
    (data_dir / "program.json").write_text(
        json.dumps(program, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_skill": skill_name,
        "factory_commit": factory_commit,
        "source_program": "data/program.json",
        "source_schema_version": program["schema_version"],
        "template": "syllabus-skill",
    }
    (output / "generated-from.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--factory-commit", required=True)
    args = parser.parse_args(argv)
    try:
        generated = generate_skill(
            args.program_path,
            args.output_dir,
            skill_name=args.skill_name,
            display_name=args.display_name,
            factory_commit=args.factory_commit,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
