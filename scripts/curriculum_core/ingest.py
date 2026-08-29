from __future__ import annotations
import hashlib, json, subprocess, time
from pathlib import Path
from typing import Any, Callable

def _write(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def scaffold_source(pdf_path: Path, output_dir: Path, *, runner: Callable | None = None, clock: Callable[[], float] | None = None) -> dict[str, Any]:
    pdf_path, output_dir = Path(pdf_path), Path(output_dir)
    if not pdf_path.is_file(): raise FileNotFoundError(str(pdf_path))
    runner = runner or (lambda command: subprocess.run(command, capture_output=True, text=True))
    clock = clock or time.perf_counter
    data = pdf_path.read_bytes()
    result: dict[str, Any] = {"source_file": str(pdf_path), "source_file_hash": hashlib.sha256(data).hexdigest(), "status": "extracted", "candidate_count": 0, "errors": []}
    started = clock()
    command = ["markitdown", str(pdf_path)]
    try:
        raw = runner(command)
        stdout = raw.get("stdout", "") if isinstance(raw, dict) else getattr(raw, "stdout", "")
        code = raw.get("returncode", 0) if isinstance(raw, dict) else getattr(raw, "returncode", 0)
        if code:
            raise RuntimeError("markitdown_failed")
        pages = len([line for line in stdout.splitlines() if line.strip().lower().startswith(("# page", "<!-- page"))])
        result["page_count"] = pages or max(1, stdout.count("\f") + 1 if stdout else 0)
        result["markdown_path"] = str(output_dir / "source.md")
        (output_dir).mkdir(parents=True, exist_ok=True)
        (output_dir / "source.md").write_text(stdout, encoding="utf-8")
        result["stage_elapsed_ms"] = {"markitdown": round((clock() - started) * 1000)}
        result["tool_command"] = command
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append({"category": "markitdown_failed", "message": str(exc)})
        result["stage_elapsed_ms"] = {"markitdown": round((clock() - started) * 1000)}
        result["tool_command"] = command
    _write(output_dir / "candidates.json", [])
    _write(output_dir / "ingest-run.json", result)
    return result
