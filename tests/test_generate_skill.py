import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


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
    assert manifest["validator"] == "curriculum_core.validation.validate_program"
    assert manifest["error_count"] == 0
    assert isinstance(manifest["warning_count"], int)

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


def test_generate_skill_rejects_duplicate_ids_before_copy(tmp_path: Path, minimal_program: dict):
    from generate_skill import generate_skill

    invalid = dict(minimal_program)
    invalid["courses"] = [*minimal_program["courses"], dict(minimal_program["courses"][0])]
    source = tmp_path / "invalid-program.json"
    source.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "should-not-exist"

    with pytest.raises(ValueError, match="program validation failed"):
        generate_skill(
            source,
            output,
            skill_name="invalid-syllabus",
            display_name="无效输入 Skill",
            factory_commit="test-factory-commit",
        )
    assert not output.exists()


def test_generated_query_keeps_needs_review_relations_unresolved(tmp_path: Path, minimal_program: dict):
    from generate_skill import generate_skill

    reviewable = dict(minimal_program)
    reviewable["relations"] = [dict(relation) for relation in minimal_program["relations"]]
    reviewable["relations"][1]["provenance"] = dict(reviewable["relations"][1]["provenance"])
    reviewable["relations"][1]["provenance"]["verification_status"] = "needs_review"
    source = tmp_path / "reviewable-program.json"
    source.write_text(json.dumps(reviewable, ensure_ascii=False), encoding="utf-8")
    output = generate_skill(
        source,
        tmp_path / "generated-syllabus",
        skill_name="reviewable-syllabus",
        display_name="待复核课程大纲 Skill",
        factory_commit="test-factory-commit",
    )

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "scripts/curriculum.py", "query", "data/program.json", "--course", "COURSE-DEMO"],
        cwd=output,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    trace = json.loads(result.stdout)
    assert trace["official_indicator_relations"] == []
    assert trace["derived_objective_relations"] == []
    assert len(trace["unresolved_indicator_relations"]) == 1

    markdown = subprocess.run(
        [sys.executable, "scripts/curriculum.py", "query", "data/program.json", "--course", "COURSE-DEMO", "--format", "markdown"],
        cwd=output,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "待复核关系" in markdown.stdout
