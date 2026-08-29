from copy import deepcopy

import pytest

from curriculum_core.query import AmbiguousCourseError, find_course, trace_course


def test_find_course_by_code(minimal_program):
    assert find_course(minimal_program, "COURSE-DEMO")["id"] == "COURSE-DEMO"


def test_find_course_normalizes_name_whitespace_and_width(minimal_program):
    assert find_course(minimal_program, "  智能制造基础 ")["id"] == "COURSE-DEMO"


def test_find_course_rejects_ambiguous_name(minimal_program):
    program = deepcopy(minimal_program)
    program["courses"].append({"id": "COURSE-2", "title": "智能制造基础"})
    with pytest.raises(AmbiguousCourseError) as exc:
        find_course(program, "智能制造基础")
    assert exc.value.course_ids == ["COURSE-2", "COURSE-DEMO"]


def test_trace_keeps_direct_and_derived_relations_separate(minimal_program):
    program = deepcopy(minimal_program)
    program["relations"].append({
        "source": "OBJ-1", "target": "COURSE-DEMO", "type": "objective_supported_by_course",
        "provenance": {"source_kind": "official_direct"},
    })
    result = trace_course(program, "COURSE-DEMO")
    assert result["official_indicator_relations"][0]["target"] == "GR-1.1"
    assert result["derived_objective_relations"][0]["source_kind"] == "derived_transitive"
    assert result["derived_objective_relations"][0]["target"] == "OBJ-1"

def test_trace_uses_canonical_id_after_title_lookup(minimal_program):
    result = trace_course(minimal_program, "智能制造基础")
    assert result["course"]["id"] == "COURSE-DEMO"
    assert result["official_indicator_relations"]

def test_trace_only_derives_from_official_requirement_objective_relation(minimal_program):
    program = deepcopy(minimal_program)
    program["relations"][0]["provenance"]["source_kind"] = "derived_transitive"
    assert trace_course(program, "COURSE-DEMO")["derived_objective_relations"] == []


def test_trace_uses_indicator_requirement_field_for_dataset_style_id(minimal_program):
    program = deepcopy(minimal_program)
    program["indicators"][0]["id"] = "1.1"
    program["indicators"][0]["graduation_requirement_id"] = "GR-1"
    program["relations"][1]["target"] = "1.1"

    derived = trace_course(program, "COURSE-DEMO")["derived_objective_relations"]

    assert derived
    assert derived[0]["target"] == "OBJ-1"
    assert derived[0]["via"] == ["1.1", "GR-1"]
