from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from jsonschema import ValidationError

from .io import validate_schema


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    message: str
    entity_id: str | None = None


def _entities(program: Mapping[str, Any]) -> set[str]:
    identifiers = set()
    for key in ("training_objectives", "graduation_requirements", "indicators", "courses", "course_groups"):
        for row in program.get(key, []) if isinstance(program.get(key, []), list) else []:
            if isinstance(row, Mapping) and isinstance(row.get("id"), str):
                identifiers.add(row["id"])
    return identifiers


def validate_program(program: Mapping[str, Any]) -> list[Issue]:
    issues = []
    try:
        validate_schema(program)
    except ValidationError as exc:
        issues.append(Issue("schema-invalid", "error", f"方案不符合数据结构：{exc.message}"))
    identifiers = _entities(program)
    for relation in program.get("relations", []) if isinstance(program.get("relations", []), list) else []:
        if not isinstance(relation, Mapping):
            continue
        for field, code in (("source", "relation-source-missing"), ("target", "relation-target-missing")):
            value = relation.get(field)
            if value not in identifiers:
                issues.append(Issue(code, "error", f"关系端点不存在：{value}", value if isinstance(value, str) else None))
    return issues
