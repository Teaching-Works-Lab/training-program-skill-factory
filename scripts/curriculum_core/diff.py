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
    def groups(program):
        grouped = {}
        for relation in program.get("relations", []):
            if isinstance(relation, Mapping):
                grouped.setdefault((relation.get("source"), relation.get("type")), []).append(relation)
        return grouped
    old_rel, new_rel = groups(old), groups(new)
    for key in sorted(set(old_rel) | set(new_rel), key=str):
        before = {tuple((r.get("source"), r.get("target"), r.get("type"))): r for r in old_rel.get(key, [])}
        after = {tuple((r.get("source"), r.get("target"), r.get("type"))): r for r in new_rel.get(key, [])}
        changed = [before[x] for x in sorted(set(before) & set(after), key=str) if before[x] != after[x]]
        changed_new = [after[x] for x in sorted(set(before) & set(after), key=str) if before[x] != after[x]]
        if before != after:
            removed = changed + [before[x] for x in sorted(set(before) - set(after), key=str)]
            added = changed_new + [after[x] for x in sorted(set(after) - set(before), key=str)]
            if len(changed) == 1 and not (set(before) - set(after)) and not (set(after) - set(before)):
                result["relation_changes"].append({"old": changed[0], "new": changed_new[0]})
            else:
                result["relation_changes"].append({"old": removed or None, "new": added or None})
    return result
