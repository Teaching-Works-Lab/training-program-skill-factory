import hashlib
from pathlib import Path

from curriculum_core.ingest import scaffold_source


class FakeClock:
    def __init__(self): self.n = 0
    def __call__(self): self.n += 0.125; return self.n


def test_scaffold_records_provenance_metrics_and_candidate_status(tmp_path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf bytes")
    calls = []

    def runner(command):
        calls.append(command)
        return {"stdout": "# page 1\n\n# page 2", "stderr": "", "returncode": 0}

    result = scaffold_source(source, tmp_path / "out", runner=runner, clock=FakeClock(), page_counter=lambda _: 2)
    assert result["source_file_hash"] == hashlib.sha256(b"pdf bytes").hexdigest()
    assert result["page_count"] == 2
    assert "markitdown" in " ".join(calls[0])
    assert result["stage_elapsed_ms"]
    assert result["candidate_count"] == 0
    assert result["status"] == "extracted"
    assert "visually_verified" not in str(result)
    assert (tmp_path / "out" / "ingest-run.json").exists()
