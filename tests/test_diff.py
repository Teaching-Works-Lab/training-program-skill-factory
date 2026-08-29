from copy import deepcopy

from curriculum_core.diff import diff_programs


def test_diff_reports_relation_change_without_overwriting_old(minimal_program):
    old = deepcopy(minimal_program)
    new = deepcopy(minimal_program)
    new["relations"][1]["target"] = "GR-1.2"
    result = diff_programs(old, new)
    assert len(result["relation_changes"]) == 1
    assert old["relations"][1]["target"] == "GR-1.1"


def test_diff_reports_unmatched_normalized_name_as_review_candidate(minimal_program):
    old = deepcopy(minimal_program)
    new = deepcopy(minimal_program)
    new["courses"][0]["id"] = "NEW"
    result = diff_programs(old, new)
    assert result["review_candidates"]

def test_diff_keeps_multiple_same_source_type_relations_distinct(minimal_program):
    old = deepcopy(minimal_program)
    old["relations"].append(deepcopy(old["relations"][1]) | {"target": "GR-1.2"})
    new = deepcopy(old)
    new["relations"].pop()
    assert len(diff_programs(old, new)["relation_changes"]) == 1
