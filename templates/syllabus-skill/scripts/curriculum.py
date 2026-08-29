from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from curriculum_core.io import load_program
from curriculum_core.query import AmbiguousCourseError, trace_course
from curriculum_core.render import render_query, render_validation_report
from curriculum_core.validation import validate_program


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("program", type=Path)
    query = sub.add_parser("query")
    query.add_argument("program", type=Path)
    query.add_argument("--course", required=True)
    query.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        program = load_program(args.program)
        if args.command == "validate":
            issues = validate_program(program)
            print(render_validation_report(program, issues), end="")
            return 1 if any(issue.severity == "error" for issue in issues) else 0
        result = trace_course(program, args.course)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_query(result), end="")
        return 0
    except AmbiguousCourseError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
