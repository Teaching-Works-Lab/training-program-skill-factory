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
    lines.append("\n## 毕业要求")
    for row in sorted(program.get("graduation_requirements", []), key=_num_key):
        lines.append(f"- {row.get('id')}: {row.get('title', '待编制')}")
    lines.append("\n## 指标点")
    for row in sorted(program.get("indicators", []), key=_num_key):
        lines.append(f"- {row.get('id')}: {row.get('title', '待编制')}")
    lines.append("\n## 课程")
    courses = sorted(program.get("courses", []), key=lambda c: (str(c.get("semester", "")), str(c.get("id", ""))))
    pages: dict[str, set[int]] = {}
    for relation in program.get("relations", []):
        if isinstance(relation, Mapping) and isinstance(relation.get("provenance", {}).get("source_page"), int):
            pages.setdefault(str(relation.get("source")), set()).add(relation["provenance"]["source_page"])
    for course in courses:
        title = course.get("title") or "待编制"
        lines.append(f"- {course.get('id')}: {title}")
        if not course.get("objectives") and not course.get("course_objectives"):
            lines.append("  - 课程目标：待编制")
        course_pages = sorted(pages.get(str(course.get("id")), set()))
        if course_pages:
            lines.append(f"  - 来源页：{'、'.join(map(str, course_pages))}")
        else:
            lines.append("  - 来源页：待核")
    return "\n".join(lines) + "\n"

def render_validation_report(program: Mapping[str, Any], issues: Sequence[Issue]) -> str:
    lines = ["# 校验报告", ""]
    entity_pages: dict[str, set[int]] = {}
    for relation in program.get("relations", []):
        if not isinstance(relation, Mapping):
            continue
        page = relation.get("provenance", {}).get("source_page")
        if isinstance(page, int):
            for endpoint in (relation.get("source"), relation.get("target")):
                if endpoint:
                    entity_pages.setdefault(str(endpoint), set()).add(page)
    for severity, label in (("error", "错误"), ("warning", "警告")):
        lines.append(f"## {label}")
        for issue in sorted((i for i in issues if i.severity == severity), key=lambda i: (i.entity_id or "", i.code)):
            suffix = f"（实体：{issue.entity_id}）" if issue.entity_id else ""
            if issue.entity_id in entity_pages:
                suffix += f" 来源页：{'、'.join(map(str, sorted(entity_pages[issue.entity_id])))}"
            lines.append(f"- [{issue.code}] {issue.message}{suffix}")
        lines.append("")
    return "\n".join(lines)
