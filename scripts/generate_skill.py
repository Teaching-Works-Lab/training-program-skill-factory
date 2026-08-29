"""Generate one portable syllabus Skill from a validated program JSON file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from curriculum_core.io import load_program
from curriculum_core.validation import validate_program

FACTORY_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = FACTORY_ROOT / "templates" / "syllabus-skill"
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEMPLATE_DIGEST_ALGORITHM = (
    "sha256(canonical JSON array of sorted {path, sha256} entries; UTF-8; "
    "sort_keys=true; separators=(',', ':'); __pycache__ and *.pyc excluded)"
)


def template_tree_digest(template_root: Path = TEMPLATE_ROOT) -> str:
    """Return a deterministic digest of the copyable template file tree."""
    entries = []
    for path in sorted(template_root.rglob("*"), key=lambda item: item.relative_to(template_root).as_posix()):
        relative = path.relative_to(template_root)
        if not path.is_file() or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        entries.append({
            "path": relative.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    canonical = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    program = load_program(source)
    if not isinstance(program, dict) or not isinstance(program.get("schema_version"), str):
        raise ValueError("program_path must contain a program JSON object with schema_version")
    issues = validate_program(program)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ValueError("program validation failed: " + ", ".join(issue.code for issue in errors))
    warnings = [issue for issue in issues if issue.severity == "warning"]

    output = Path(output_dir)
    shutil.copytree(TEMPLATE_ROOT, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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
        "template_digest": f"sha256:{template_tree_digest()}",
        "template_digest_algorithm": TEMPLATE_DIGEST_ALGORITHM,
        "source_program": "data/program.json",
        "source_schema_version": program["schema_version"],
        "template": "syllabus-skill",
        "validator": "curriculum_core.validation.validate_program",
        "error_count": 0,
        "warning_count": len(warnings),
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
