# Task 4 report

- RED: `py -3.12 -m pytest tests/test_query.py tests/test_render.py tests/test_diff.py tests/test_ingest.py -q` (imports failed because the four modules were absent).
- GREEN: `py -3.12 -m pytest tests -q` — 41 passed, 1 skipped.
- CLI smoke: `py -3.12 scripts/curriculum.py validate tests/fixtures/minimal-program.json` — exit 0; validation report contained zero errors (two warnings).
- `git diff --check` passed.

Implemented deterministic course lookup/tracing, catalog and validation Markdown rendering, stable-ID program diffs with review candidates, injectable MarkItDown ingestion scaffolding with provenance metrics and failure preservation, and explicit CLI exit codes/subcommands.

Concern: matrix extraction remains source-specific at the page/indicator selection boundary; the CLI now accepts those explicit parameters and delegates cell extraction to the existing conservative extractor.
