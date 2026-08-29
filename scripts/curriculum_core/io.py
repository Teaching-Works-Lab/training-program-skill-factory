from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).parents[2] / "references" / "program.schema.json"


def load_program(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_schema(program: Mapping[str, Any]) -> None:
    schema = load_program(SCHEMA_PATH)
    Draft202012Validator(schema).validate(program)
