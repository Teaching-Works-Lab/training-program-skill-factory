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

