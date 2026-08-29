from pathlib import Path

import pytest
from jsonschema import ValidationError

from curriculum_core.io import load_program, validate_schema, write_json


FIXTURE = Path(__file__).parent / "fixtures" / "minimal-program.json"


def test_minimal_program_matches_schema():
    program = load_program(FIXTURE)
    validate_schema(program)


def test_schema_rejects_relation_without_provenance():
    program = load_program(FIXTURE)
    del program["relations"][0]["provenance"]
    with pytest.raises(ValidationError):
        validate_schema(program)


def test_write_json_round_trips_chinese(tmp_path: Path):
    target = tmp_path / "培养方案.json"
    payload = {"title": "智能制造工程", "hours": None}
    write_json(target, payload)
    assert load_program(target) == payload
    assert "智能制造工程" in target.read_text(encoding="utf-8")


def test_course_component_hours_zero_and_null_are_schema_valid(minimal_program):
    course = minimal_program["courses"][0]
    course["hours"] = {"lecture_hours": None, "practice_hours": 0}
    validate_schema(minimal_program)
