from __future__ import annotations
import re
from typing import Any, Mapping, Sequence
from .validation import Issue

def _num_key(row: Mapping[str, Any]):
    return tuple(int(x) if x.isdigit() else x for x in re.split(r"(\d+)", str(row.get("id", ""))))

def render_catalog(program: Mapping[str, Any]) -> str:
    lines = [f"# {program.get('program', {}).get('title', '培养方案')}", ""]
    lines.append("## 培养目标")
    for row in sorted(program.get("training_objectives", []), key=_num_key):
        lines.append(f"- {row.get('id')}: {row.get('title', '课程目标：待编制')}")
    lines.append("\n## 课程")
    courses = sorted(program.get("courses", []), key=lambda c: (str(c.get("semester", "")), str(c.get("id", ""))))
    pages = {r.get("source"): r.get("provenance", {}).get("source_page") for r in program.get("relations", []) if isinstance(r, Mapping)}
    for course in courses:
        title = course.get("title") or "待编制"
        lines.append(f"- {course.get('id')}: {title}")
        if not course.get("objectives") and not course.get("course_objectives"):
            lines.append("  - 课程目标：待编制")
        page = pages.get(course.get("id"))
        if page is not None:
            lines.append(f"  - 来源页：{page}")
        else:
            lines.append("  - 来源页：待核")
    return "\n".join(lines) + "\n"

def render_validation_report(program: Mapping[str, Any], issues: Sequence[Issue]) -> str:
    lines = ["# 校验报告", ""]
    for severity, label in (("error", "错误"), ("warning", "警告")):
        lines.append(f"## {label}")
        for issue in sorted((i for i in issues if i.severity == severity), key=lambda i: (i.entity_id or "", i.code)):
            suffix = f"（实体：{issue.entity_id}）" if issue.entity_id else ""
            lines.append(f"- [{issue.code}] {issue.message}{suffix}")
        lines.append("")
    return "\n".join(lines)
