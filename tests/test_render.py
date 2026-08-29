from curriculum_core.render import render_catalog, render_validation_report
from curriculum_core.validation import Issue


def test_catalog_labels_missing_syllabus_fields_as_pending(minimal_program):
    text = render_catalog(minimal_program)
    assert "课程目标：待编制" in text
    assert "来源页：1" in text


def test_validation_report_groups_errors_before_warnings():
    text = render_validation_report({}, [
        Issue("w", "warning", "警告", "X"), Issue("e", "error", "错误", "Y")
    ])
    assert text.index("错误") < text.index("警告")
    assert "Y" in text

def test_catalog_renders_all_entities_in_numeric_order(minimal_program):
    text = render_catalog(minimal_program)
    assert all(token in text for token in ("培养目标", "毕业要求", "指标点", "课程"))

def test_catalog_lists_unique_sorted_course_source_pages(minimal_program):
    relation = minimal_program["relations"][1]
    minimal_program["relations"].append({**relation, "provenance": {**relation["provenance"], "source_page": 3}})
    text = render_catalog(minimal_program)
    assert "来源页：1、3" in text
