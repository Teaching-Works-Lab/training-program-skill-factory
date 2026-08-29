from __future__ import annotations

import re
from typing import Any, Mapping


class AmbiguousCourseError(ValueError):
    def __init__(self, course_ids: list[str]):
        self.course_ids = sorted(course_ids)
        super().__init__(f"ambiguous course: {', '.join(self.course_ids)}")


def normalize_term(value: str) -> str:
    table = str.maketrans("，。；：、（）【】［］", ",.;:,()[][]")
    return re.sub(r"\s+", "", value.translate(table)).strip()


def find_course(program: Mapping[str, Any], term: str) -> dict[str, Any]:
    courses = [c for c in program.get("courses", []) if isinstance(c, Mapping)]
    exact = [c for c in courses if c.get("id") == term]
    if exact:
        return dict(exact[0])
    wanted = normalize_term(term)
    matches = [c for c in courses if normalize_term(str(c.get("title", ""))) == wanted]
    if len(matches) > 1:
        raise AmbiguousCourseError([str(c.get("id")) for c in matches])
    if not matches:
        raise KeyError(f"course not found: {term}")
    return dict(matches[0])


def trace_course(program: Mapping[str, Any], course_id: str) -> dict[str, Any]:
    course = find_course(program, course_id)
    course_id = str(course["id"])
    relations = [r for r in program.get("relations", []) if isinstance(r, Mapping) and "source" in r and "target" in r]
    direct = [dict(r) for r in relations if r["source"] == course_id and r.get("type") == "course_supports_indicator"]
    official = [r for r in direct if r.get("provenance", {}).get("source_kind") == "official_direct"]
    indicator_requirements = {
        str(indicator.get("id")): indicator.get("graduation_requirement_id")
        for indicator in program.get("indicators", [])
        if isinstance(indicator, Mapping) and "id" in indicator and "graduation_requirement_id" in indicator
    }
    derived: list[dict[str, Any]] = []
    objectives = {str(x.get("id")): x for x in program.get("training_objectives", []) if isinstance(x, Mapping)}
    for relation in official:
        indicator = str(relation["target"])
        if indicator in indicator_requirements:
            parent_value = indicator_requirements[indicator]
            parent = str(parent_value) if parent_value is not None else None
        else:
            # Legacy fixtures may omit the explicit parent field (GR-1.1 -> GR-1).
            parent = indicator.rsplit(".", 1)[0] if "." in indicator else indicator
        for upper in relations:
            if (upper.get("source") == parent and upper.get("target") in objectives
                    and upper.get("type") == "requirement_supports_objective"
                    and upper.get("provenance", {}).get("source_kind") == "official_direct"):
                derived.append({"source": course_id, "target": upper["target"], "source_kind": "derived_transitive", "via": [indicator, parent]})
    return {"course": course, "official_indicator_relations": official, "derived_objective_relations": derived}
