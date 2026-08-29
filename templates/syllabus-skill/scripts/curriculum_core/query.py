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
    courses = [course for course in program.get("courses", []) if isinstance(course, Mapping)]
    exact = [course for course in courses if course.get("id") == term]
    if exact:
        return dict(exact[0])
    matches = [course for course in courses if normalize_term(str(course.get("title", ""))) == normalize_term(term)]
    if len(matches) > 1:
        raise AmbiguousCourseError([str(course.get("id")) for course in matches])
    if not matches:
        raise KeyError(f"course not found: {term}")
    return dict(matches[0])


def trace_course(program: Mapping[str, Any], course_id: str) -> dict[str, Any]:
    course = find_course(program, course_id)
    relations = [relation for relation in program.get("relations", []) if isinstance(relation, Mapping)]
    direct = [dict(relation) for relation in relations if relation.get("source") == course["id"] and relation.get("type") == "course_supports_indicator"]
    official = [relation for relation in direct if relation.get("provenance", {}).get("source_kind") == "official_direct"]
    parents = {
        str(indicator["id"]): indicator.get("graduation_requirement_id")
        for indicator in program.get("indicators", [])
        if isinstance(indicator, Mapping) and "id" in indicator and "graduation_requirement_id" in indicator
    }
    objectives = {str(objective.get("id")) for objective in program.get("training_objectives", []) if isinstance(objective, Mapping)}
    derived = []
    for relation in official:
        indicator = str(relation["target"])
        parent = str(parents[indicator]) if indicator in parents and parents[indicator] is not None else indicator.rsplit(".", 1)[0]
        for upper in relations:
            if upper.get("source") == parent and upper.get("target") in objectives and upper.get("type") == "requirement_supports_objective" and upper.get("provenance", {}).get("source_kind") == "official_direct":
                derived.append({"source": course["id"], "target": upper["target"], "source_kind": "derived_transitive", "via": [indicator, parent]})
    return {"course": course, "official_indicator_relations": official, "derived_objective_relations": derived}
