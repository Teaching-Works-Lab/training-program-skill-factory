from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).parents[2] / "references" / "program.schema.json"


def load_program(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_schema(program: Mapping[str, Any]) -> None:
    Draft202012Validator(load_program(SCHEMA_PATH)).validate(program)
