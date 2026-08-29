import json
import os
from pathlib import Path
import subprocess
import sys


def test_generate_skill_creates_a_standalone_skill(tmp_path: Path, minimal_program_path: Path):
    from generate_skill import generate_skill

    output = generate_skill(
        minimal_program_path,
        tmp_path / "generated-syllabus",
        skill_name="demo-syllabus",
        display_name="示例课程大纲 Skill",
        factory_commit="test-factory-commit",
    )

    required = [
        "SKILL.md",
        "agents/openai.yaml",
        "data/program.json",
        "generated-from.json",
        "scripts/curriculum.py",
        "scripts/curriculum_core/io.py",
        "scripts/curriculum_core/query.py",
        "scripts/curriculum_core/validation.py",
    ]
    assert all((output / relative).is_file() for relative in required)

    manifest = json.loads((output / "generated-from.json").read_text(encoding="utf-8"))
    assert manifest["factory_commit"] == "test-factory-commit"
    assert manifest["source_program"] == "data/program.json"

    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output.rglob("*")
        if path.is_file()
    )
    assert str(Path(__file__).parents[1]).lower() not in rendered.lower()

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    validation = subprocess.run(
        [sys.executable, "scripts/curriculum.py", "validate", "data/program.json"],
        cwd=output,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert validation.returncode == 0, validation.stderr
