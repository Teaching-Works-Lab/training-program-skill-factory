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

