from __future__ import annotations
from typing import Any, Mapping
from .query import normalize_term

def _entities(program: Mapping[str, Any], kind: str):
    return {str(x.get("id")): x for x in program.get(kind, []) if isinstance(x, Mapping) and x.get("id")}

def diff_programs(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result = {"added": [], "removed": [], "changed": [], "relation_changes": [], "review_candidates": []}
    for kind in ("training_objectives", "graduation_requirements", "indicators", "courses", "course_groups"):
        a, b = _entities(old, kind), _entities(new, kind)
        for ident in sorted(set(b) - set(a)): result["added"].append({"kind": kind, "id": ident, "entity": dict(b[ident])})
        for ident in sorted(set(a) - set(b)): result["removed"].append({"kind": kind, "id": ident, "entity": dict(a[ident])})
        for ident in sorted(set(a) & set(b)):
            if dict(a[ident]) != dict(b[ident]): result["changed"].append({"kind": kind, "id": ident, "old": dict(a[ident]), "new": dict(b[ident])})
        old_names = {normalize_term(str(x.get("title", ""))): i for i, x in a.items() if x.get("title")}
        for ident, row in b.items():
            name = normalize_term(str(row.get("title", "")))
            if ident not in a and name in old_names:
                result["review_candidates"].append({"kind": kind, "old_id": old_names[name], "new_id": ident, "normalized_name": name})
    old_rel = {(r.get("source"), r.get("type")): r for r in old.get("relations", []) if isinstance(r, Mapping)}
    new_rel = {(r.get("source"), r.get("type")): r for r in new.get("relations", []) if isinstance(r, Mapping)}
    for key in sorted(set(old_rel) | set(new_rel), key=str):
        if key not in old_rel or key not in new_rel or old_rel[key].get("target") != new_rel[key].get("target"):
            result["relation_changes"].append({"old": old_rel.get(key), "new": new_rel.get(key)})
    return result
