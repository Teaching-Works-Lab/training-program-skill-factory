"""Deterministic, non-mutating checks for training-program data."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any, Mapping

from jsonschema import ValidationError

from .io import validate_schema


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    message: str
    entity_id: str | None = None


def _issue(code: str, severity: str, message: str, entity_id: str | None = None) -> Issue:
    return Issue(code, severity, message, entity_id)


def _number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _hours(value: Any) -> tuple[float | None, bool]:
    """Return known total and whether at least one component is non-null."""
    if value is None:
        return None, False
    if _number(value):
        return float(value), True
    if not isinstance(value, Mapping):
        return None, True
    components = [v for k, v in value.items() if k != "total_hours"]
    if not components and "total_hours" in value:
        stated = value["total_hours"]
        return (float(stated), True) if _number(stated) else (None, True)
    known = [v for v in components if v is not None]
    if not known:
        return None, False
    if not all(_number(v) for v in known):
        return None, True
    return sum(float(v) for v in known), True


def _entities(program: Mapping[str, Any]) -> tuple[dict[str, set[str]], list[Issue]]:
    buckets: dict[str, set[str]] = {
        "objective": set(), "requirement": set(), "indicator": set(),
        "course": set(), "group": set(), "all": set(),
    }
    issues: list[Issue] = []
    rows = (
        ("objective", program.get("training_objectives", [])),
        ("requirement", program.get("graduation_requirements", [])),
        ("indicator", program.get("indicators", [])),
        ("course", program.get("courses", [])),
        ("group", program.get("course_groups", [])),
    )
    for kind, values in rows:
        for row in values if isinstance(values, list) else []:
            if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
                continue
            ident = row["id"]
            if ident in buckets["all"]:
                issues.append(_issue("duplicate-id", "error", f"实体 ID 重复：{ident}", ident))
            buckets[kind].add(ident)
            buckets["all"].add(ident)
            if kind == "requirement":
                for indicator in row.get("indicators", []):
                    if isinstance(indicator, Mapping) and isinstance(indicator.get("id"), str):
                        iid = indicator["id"]
                        if iid in buckets["all"]:
                            issues.append(_issue("duplicate-id", "error", f"实体 ID 重复：{iid}", iid))
                        buckets["indicator"].add(iid)
                        buckets["all"].add(iid)
    return buckets, issues


def validate_program(program: Mapping[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    try:
        validate_schema(program)
    except ValidationError as exc:
        issues.append(_issue("schema-invalid", "error", f"方案不符合数据结构：{exc.message}"))

    buckets, duplicate_issues = _entities(program)
    issues.extend(duplicate_issues)
    all_ids = buckets["all"]

    relations = program.get("relations", [])
    support_course: dict[str, set[str]] = {x: set() for x in buckets["course"]}
    support_indicator: dict[str, set[str]] = {x: set() for x in buckets["indicator"]}
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, Mapping):
            continue
        source = relation.get("source", relation.get("source_id"))
        target = relation.get("target", relation.get("target_id"))
        if source not in all_ids:
            issues.append(_issue("relation-source-missing", "error", f"关系源实体不存在：{source}", source if isinstance(source, str) else None))
        if target not in all_ids:
            issues.append(_issue("relation-target-missing", "error", f"关系目标实体不存在：{target}", target if isinstance(target, str) else None))
        if relation.get("type") == "course_supports_indicator":
            if source in support_course and target in support_indicator:
                support_course[source].add(target)
                support_indicator[target].add(source)

    for course in program.get("courses", []) if isinstance(program.get("courses", []), list) else []:
        if not isinstance(course, Mapping) or not isinstance(course.get("id"), str):
            continue
        cid = course["id"]
        value = course.get("hours")
        total, known = _hours(value)
        nonnegative = all(
            v is None or (_number(v) and float(v) >= 0)
            for v in (value.values() if isinstance(value, Mapping) else [value])
        )
        if value is not None and ((known and total is None) or not nonnegative):
            issues.append(_issue("hours-value-invalid", "error", f"课程学时值无效：{cid}", cid))
        if isinstance(value, Mapping) and "total_hours" in value and known and total is not None:
            stated = value["total_hours"]
            if not _number(stated) or float(stated) != total:
                issues.append(_issue("course-hours-mismatch", "error", f"课程分项学时与总学时不一致：{cid}", cid))

    for iid, supporters in support_indicator.items():
        if not supporters:
            issues.append(_issue("indicator-support-zero", "warning", f"指标点暂无课程关系支持：{iid}", iid))
        elif len(supporters) < 3:
            issues.append(_issue("indicator-support-count-low", "warning", f"指标点课程支持数低于建议范围（3–5）：{iid}", iid))
        elif len(supporters) > 5:
            issues.append(_issue("indicator-support-count-high", "warning", f"指标点课程支持数高于建议范围（3–5）：{iid}", iid))
    for cid, supporters in support_course.items():
        if not supporters:
            issues.append(_issue("course-support-zero", "warning", f"课程暂无指标点关系支持：{cid}", cid))
        elif len(supporters) < 2:
            issues.append(_issue("course-support-count-low", "warning", f"课程指标点支持数低于建议范围（2–5）：{cid}", cid))
        elif len(supporters) > 5:
            issues.append(_issue("course-support-count-high", "warning", f"课程指标点支持数高于建议范围（2–5）：{cid}", cid))

    course_totals: dict[str, float] = {}
    for course in program.get("courses", []) if isinstance(program.get("courses", []), list) else []:
        if isinstance(course, Mapping) and isinstance(course.get("id"), str):
            total, known = _hours(course.get("hours"))
            if known and total is not None:
                course_totals[course["id"]] = total
    aggregate = program.get("aggregates", {})
    requirement_totals: dict[str, float] = {}
    for requirement in program.get("graduation_requirements", []) if isinstance(program.get("graduation_requirements", []), list) else []:
        if isinstance(requirement, Mapping) and isinstance(requirement.get("id"), str):
            total, known = _hours(requirement.get("hours"))
            if known and total is not None and total >= 0:
                requirement_totals[requirement["id"]] = total
    course_rows = [c for c in program.get("courses", []) if isinstance(c, Mapping) and isinstance(c.get("id"), str)] if isinstance(program.get("courses", []), list) else []
    course_hours_complete = all(c.get("id") in course_totals for c in course_rows)
    if isinstance(aggregate, Mapping) and course_hours_complete and (course_totals or requirement_totals):
        stated_total = aggregate.get("total_hours")
        calculated_total = sum(course_totals.values()) + sum(requirement_totals.values())
        if _number(stated_total) and float(stated_total) != calculated_total:
            issues.append(_issue("aggregate-total-hours-mismatch", "error", "汇总总学时与课程计算值不一致"))
        by_group = aggregate.get("hours_by_group")
        if isinstance(by_group, Mapping):
            groups = {g.get("id"): g for g in program.get("course_groups", []) if isinstance(g, Mapping)}
            for gid, stated in by_group.items():
                group = groups.get(gid)
                if not group or not _number(stated):
                    continue
                members = group.get("course_ids", [])
                if not isinstance(members, list) or any(cid not in course_totals for cid in members):
                    continue
                calculated = sum(course_totals[cid] for cid in members)
                if float(stated) != calculated:
                    issues.append(_issue("aggregate-group-hours-mismatch", "error", f"课程组汇总学时与计算值不一致：{gid}", gid))
    return issues
