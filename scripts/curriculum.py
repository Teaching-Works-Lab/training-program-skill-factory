from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from curriculum_core.io import load_program
from curriculum_core.validation import validate_program
from curriculum_core.query import AmbiguousCourseError, trace_course
from curriculum_core.render import render_catalog, render_validation_report
from curriculum_core.diff import diff_programs
from curriculum_core.ingest import scaffold_source

def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "render"):
        p = sub.add_parser(name); p.add_argument("program", type=Path); p.add_argument("--output", type=Path)
    p = sub.add_parser("query"); p.add_argument("program", type=Path); p.add_argument("--course", required=True); p.add_argument("--format", choices=("json", "markdown"), default="json")
    p = sub.add_parser("diff"); p.add_argument("old", type=Path); p.add_argument("new", type=Path); p.add_argument("--output", type=Path)
    p = sub.add_parser("scaffold"); p.add_argument("pdf", type=Path); p.add_argument("output_dir", type=Path)
    p = sub.add_parser("extract-matrix"); p.add_argument("pdf", type=Path); p.add_argument("output", type=Path); p.add_argument("--indicators", nargs="+", required=True); p.add_argument("--page", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        if args.command == "scaffold":
            result = scaffold_source(args.pdf, args.output_dir); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result["status"] != "failed" else 2
        if args.command == "extract-matrix":
            import fitz
            from curriculum_core.matrix_pdf import extract_matrix_page
            with fitz.open(args.pdf) as document:
                rows = extract_matrix_page(document[args.page - 1], args.indicators)
            args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 0
        if args.command == "validate":
            program = load_program(args.program); issues = validate_program(program); text = render_validation_report(program, issues); print(text, end=""); return 1 if any(i.severity == "error" for i in issues) else 0
        if args.command == "query":
            result = trace_course(load_program(args.program), args.course)
            if args.format == "json": print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"# {result['course'].get('title', result['course']['id'])}\n\n## official\n")
                for row in result["official_indicator_relations"]: print(f"- {row['source']} -> {row['target']}")
                print("\n## derived\n")
                for row in result["derived_objective_relations"]: print(f"- {row['source']} -> {row['target']}")
            return 0
        if args.command == "render":
            program = load_program(args.program); issues = validate_program(program); catalog = render_catalog(program); report = render_validation_report(program, issues)
            if args.output:
                args.output.mkdir(parents=True, exist_ok=True)
                (args.output / "catalog.md").write_text(catalog, encoding="utf-8")
                (args.output / "validation-report.md").write_text(report, encoding="utf-8")
            else:
                print(catalog + "\n" + report, end="")
            return 1 if any(i.severity == "error" for i in issues) else 0
        result = diff_programs(load_program(args.old), load_program(args.new)); text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output: args.output.write_text(text, encoding="utf-8")
        else: print(text, end="")
        return 0
    except AmbiguousCourseError as exc:
        print(str(exc), file=sys.stderr); return 1
    except (FileNotFoundError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr); return 2

if __name__ == "__main__": sys.exit(main())
