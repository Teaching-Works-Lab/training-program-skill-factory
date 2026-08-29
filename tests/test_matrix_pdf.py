import os
from pathlib import Path

import fitz
import pytest

from curriculum_core.matrix_pdf import (
    MatrixExtractionError,
    cell_index,
    extract_matrix_page,
)


@pytest.mark.parametrize(
    ("position", "boundaries", "expected"),
    [
        (10.0, (0.0, 20.0, 40.0), 0),
        (20.0, (0.0, 20.0, 40.0), 1),
        (39.9, (0.0, 20.0, 40.0), 1),
    ],
)
def test_cell_index_uses_half_open_intervals(position, boundaries, expected):
    assert cell_index(position, boundaries) == expected


def test_cell_index_rejects_outside_grid():
    with pytest.raises(ValueError, match="outside grid"):
        cell_index(41.0, (0.0, 20.0, 40.0))


class _Page:
    number = 0

    def __init__(self, symbol_x=15.0):
        self._drawings = [
            {"items": [("l", fitz.Point(x, 0), fitz.Point(x, 100))]}
            for x in (0, 10, 20)
        ] + [
            {"items": [("l", fitz.Point(0, y), fitz.Point(20, y))]}
            for y in (0, 20)
        ]
        self._words = [
            (2.0, 5.0, 10.0, 15.0, "课程A", 0, 0, 0),
            (symbol_x - 2.0, 5.0, symbol_x + 2.0, 15.0, "●", 1, 0, 0),
        ]

    def get_drawings(self):
        return self._drawings

    def get_text(self, kind):
        assert kind == "words"
        return self._words


def test_extract_matrix_page_maps_filled_circle_to_indicator_cell():
    relations = extract_matrix_page(_Page(), ("1.1",))
    assert relations == [
        {
            "course_label": "课程A",
            "indicator_id": "1.1",
            "page": 1,
            "symbol_coordinates": {"x": 15.0, "y": 10.0},
            "verification_status": "extracted",
        }
    ]


def test_extract_matrix_page_rejects_symbol_outside_detected_cell():
    with pytest.raises(MatrixExtractionError, match="page 1.*45"):
        extract_matrix_page(_Page(symbol_x=45.0), ("1.1",))


@pytest.mark.skipif("TRAINING_PROGRAM_PDF" not in os.environ, reason="real PDF not configured")
def test_real_pdf_first_matrix_page_has_all_indicator_columns():
    path = Path(os.environ["TRAINING_PROGRAM_PDF"])
    doc = fitz.open(path)
    indicators = (
        "1.1", "1.2", "1.3", "2.1", "2.2", "3.1", "3.2", "3.3",
        "4.1", "4.2", "4.3", "5.1", "5.2", "5.3", "6.1", "6.2",
        "6.3", "7.1", "7.2", "7.3", "8.1", "8.2", "9.1", "9.2",
        "10.1", "10.2", "11.1", "11.2", "12.1", "12.2",
    )
    try:
        relations = extract_matrix_page(doc[20], indicators)
    finally:
        doc.close()
    assert relations
    assert all(item["indicator_id"] in indicators for item in relations)
    assert all(item["verification_status"] == "extracted" for item in relations)
