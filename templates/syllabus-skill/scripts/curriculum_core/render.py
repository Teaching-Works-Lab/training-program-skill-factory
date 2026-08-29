from __future__ import annotations

from typing import Sequence

from .validation import Issue


def render_validation_report(program, issues: Sequence[Issue]) -> str:
    lines = ["# 校验报告", ""]
    for severity, label in (("error", "错误"), ("warning", "警告")):
        lines.append(f"## {label}")
        for issue in sorted((issue for issue in issues if issue.severity == severity), key=lambda issue: (issue.entity_id or "", issue.code)):
            suffix = f"（实体：{issue.entity_id}）" if issue.entity_id else ""
            lines.append(f"- [{issue.code}] {issue.message}{suffix}")
        lines.append("")
    return "\n".join(lines)
