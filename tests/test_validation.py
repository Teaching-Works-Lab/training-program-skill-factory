from copy import deepcopy

from curriculum_core.io import load_program
from curriculum_core.validation import validate_program


def issue_codes(program):
    return {issue.code for issue in validate_program(program)}


def test_reports_relation_to_missing_indicator(minimal_program_path):
    program = load_program(minimal_program_path)
    program["relations"][1]["target"] = "GR-9.9"
    assert "relation-target-missing" in issue_codes(program)


def test_blank_hours_and_zero_hours_are_not_equivalent(minimal_program_path):
    program = load_program(minimal_program_path)
    course = program["courses"][0]
    course["hours"] = {"experiment_hours": None, "practice_hours": 0}
    assert "hours-value-invalid" not in issue_codes(program)


def test_support_count_over_five_is_warning(minimal_program_path):
    program = load_program(minimal_program_path)
    relation = deepcopy(program["relations"][1])
    for index in range(2, 7):
        item = deepcopy(relation)
        item["target"] = f"GR-1.{index}"
        program["indicators"].append({"id": item["target"], "title": f"指标点{index}"})
        program["relations"].append(item)
    issues = validate_program(program)
    assert any(i.code == "course-support-count-high" and i.severity == "warning" for i in issues)


def test_duplicate_ids_and_missing_relation_source_are_errors(minimal_program):
    program = deepcopy(minimal_program)
    program["courses"].append({"id": "COURSE-DEMO", "title": "重复课程", "hours": {"total_hours": 1}})
    program["relations"][0]["source"] = "NO-SUCH-ENTITY"
    issues = validate_program(program)
    assert any(i.code == "duplicate-id" and i.severity == "error" for i in issues)
    assert any(i.code == "relation-source-missing" and i.severity == "error" for i in issues)


def test_null_course_components_do_not_claim_hours_mismatch(minimal_program):
    program = deepcopy(minimal_program)
    program["courses"][0]["hours"] = {"lecture_hours": None, "practice_hours": None}
    program["aggregates"]["total_hours"] = 999
    assert "course-hours-mismatch" not in issue_codes(program)
    assert "hours-value-invalid" not in issue_codes(program)


def test_null_indicators_is_reported_without_recovery_crash(minimal_program):
    program = deepcopy(minimal_program)
    program["indicators"] = None
    issues = validate_program(program)
    assert any(issue.code == "schema-invalid" for issue in issues)


def test_null_course_ids_is_reported_without_recovery_crash(minimal_program):
    program = deepcopy(minimal_program)
    program["course_groups"][0]["course_ids"] = None
    issues = validate_program(program)
    assert any(issue.code == "schema-invalid" for issue in issues)


def test_unknown_group_member_skips_exact_group_comparison(minimal_program):
    program = deepcopy(minimal_program)
    program["course_groups"][0]["course_ids"].append("COURSE-UNKNOWN")
    program["aggregates"]["hours_by_group"]["GROUP-DEMO"] = 32
    codes = issue_codes(program)
    assert "aggregate-group-hours-mismatch" not in codes


def test_reports_missing_course_group_member_as_error(minimal_program):
    program = deepcopy(minimal_program)
    program["course_groups"][0]["course_ids"] = ["COURSE-MISSING"]
    issues = validate_program(program)
    assert any(
        issue.code == "course-group-member-missing"
        and issue.severity == "error"
        and issue.entity_id == "GROUP-DEMO"
        for issue in issues
    )


def test_zero_support_entities_are_reported(minimal_program):
    program = deepcopy(minimal_program)
    program["indicators"].append({"id": "GR-1.2", "title": "未支撑指标"})
    program["courses"].append({"id": "COURSE-UNSUPPORTED", "title": "未支撑课程", "hours": {"total_hours": 1}})
    codes = issue_codes(program)
    assert "indicator-support-zero" in codes
    assert "course-support-zero" in codes


def test_aggregate_group_hours_mismatch_is_reported(minimal_program):
    program = deepcopy(minimal_program)
    program["aggregates"]["total_hours"] = 99
    program["aggregates"]["hours_by_group"]["GROUP-DEMO"] = 99
    codes = issue_codes(program)
    assert "aggregate-total-hours-mismatch" in codes
    assert "aggregate-group-hours-mismatch" in codes


def test_canonical_relation_endpoints_take_precedence(minimal_program):
    program = deepcopy(minimal_program)
    program["relations"][1]["source_id"] = "NO-SUCH-SOURCE"
    program["relations"][1]["target_id"] = "NO-SUCH-TARGET"
    codes = issue_codes(program)
    assert "relation-source-missing" not in codes
    assert "relation-target-missing" not in codes


def test_relation_endpoint_aliases_are_recovery_only(minimal_program):
    program = deepcopy(minimal_program)
    relation = program["relations"][1]
    relation.pop("source")
    relation.pop("target")
    relation["source_id"] = "COURSE-DEMO"
    relation["target_id"] = "GR-1.1"
    codes = issue_codes(program)
    assert "relation-source-missing" not in codes
    assert "relation-target-missing" not in codes


def test_aggregate_total_skips_when_any_course_hours_are_unknown(minimal_program):
    program = deepcopy(minimal_program)
    program["courses"].append({"id": "COURSE-UNKNOWN", "title": "学时待核", "hours": {"lecture_hours": None}})
    program["aggregates"]["total_hours"] = 999
    assert "aggregate-total-hours-mismatch" not in issue_codes(program)


def test_null_declared_course_total_is_unknown_not_invalid(minimal_program):
    program = deepcopy(minimal_program)
    program["courses"][0]["hours"] = {"total_hours": None}
    codes = issue_codes(program)
    assert "hours-value-invalid" not in codes
    assert "course-hours-mismatch" not in codes
    assert "aggregate-total-hours-mismatch" not in codes
