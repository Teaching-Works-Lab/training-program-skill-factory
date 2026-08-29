from pathlib import Path
import sys

import pytest


SKILL_ROOT = Path(__file__).parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def minimal_program_path() -> Path:
    return Path(__file__).parent / "fixtures" / "minimal-program.json"


@pytest.fixture
def minimal_program(minimal_program_path: Path):
    from curriculum_core.io import load_program

    return load_program(minimal_program_path)
