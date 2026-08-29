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
        (2.0, 5.0, 10.0, 15.0, "CourseA", 0, 0, 0),
            (symbol_x - 2.0, 5.0, symbol_x + 2.0, 15.0, "●", 1, 0, 0),
        ]

    def get_drawings(self):
        return self._drawings

    def get_text(self, kind):
        assert kind == "words"
        return self._words


def _page(words, drawings=None, columns=(0, 10, 20), rows=(0, 20)):
    page = _Page()
    page._words = words
    page._drawings = [
        {"items": [("l", fitz.Point(x, 0), fitz.Point(x, 100))]}
        for x in columns
    ] + [
        {"items": [("l", fitz.Point(0, y), fitz.Point(columns[-1], y))]}
        for y in rows
    ]
    if drawings:
        page._drawings.extend(drawings)
    return page


def test_extract_matrix_page_maps_filled_circle_to_indicator_cell():
    relations = extract_matrix_page(_Page(), ("1.1",))
    assert relations == [
        {
            "course_label": "CourseA",
            "indicator_id": "1.1",
            "page": 1,
            "symbol_coordinates": {"x": 15.0, "y": 10.0},
            "verification_status": "extracted",
        }
    ]


def test_extract_matrix_page_rejects_symbol_outside_detected_cell():
    with pytest.raises(MatrixExtractionError, match="page 1.*45"):
        extract_matrix_page(_Page(symbol_x=45.0), ("1.1",))


def test_extract_skips_header_and_outside_grid_words():
    words = [
        (2, 5, 8, 10, "CourseA", 0, 0, 0),
        (12, 5, 16, 10, "●", 1, 0, 0),
        (999, 5, 1000, 10, "页脚", 9, 0, 0),
    ]
    assert len(extract_matrix_page(_page(words), ("1.1",))) == 1


def test_extract_rejects_indicator_column_count_mismatch():
    with pytest.raises(MatrixExtractionError, match="indicator columns"):
        extract_matrix_page(_Page(), ("1.1", "1.2"))


def test_extract_ignores_unfilled_bezier_and_filled_rectangle_drawings():
    drawings = [
        {"rect": fitz.Rect(12, 5, 18, 15), "items": [("c",) ], "fill": None},
        {"rect": fitz.Rect(12, 5, 18, 15), "items": [("re", fitz.Rect(12, 5, 18, 15), 0)], "fill": (0, 0, 0)},
    ]
    words = [(2, 5, 8, 10, "课程A", 0, 0, 0)]
    assert extract_matrix_page(_page(words, drawings), ("1.1",)) == []


def test_replacement_glyph_is_not_a_text_symbol_candidate():
    words = [
        (2, 5, 8, 10, "CourseA", 0, 0, 0),
        (12, 5, 16, 10, "�", 1, 0, 0),
    ]
    assert extract_matrix_page(_page(words), ("1.1",)) == []


def test_filled_closed_near_circle_is_not_automatically_a_symbol():
    drawings = [{
        "rect": fitz.Rect(12, 5, 18, 11),
        "items": [("c",), ("c",), ("c",), ("c",)],
        "fill": (0, 0, 0),
        "closePath": True,
    }]
    words = [(2, 5, 8, 10, "CourseA", 0, 0, 0)]
    assert extract_matrix_page(_page(words, drawings), ("1.1",)) == []


def test_extract_preserves_multiline_label_reading_order():
    words = [
        (2, 14, 8, 19, "Bottom", 0, 1, 0),
        (12, 5, 16, 10, "●", 1, 0, 0),
        (8, 2, 9, 4, "Top", 0, 0, 0),
    ]
    assert extract_matrix_page(_page(words), ("1.1",))[0]["course_label"] == "Top Bottom"


def test_same_label_in_distinct_rows_is_allowed():
    words = [
        (2, 5, 8, 10, "Same", 0, 0, 0),
        (12, 5, 16, 10, "●", 1, 0, 0),
        (2, 25, 8, 30, "Same", 0, 1, 0),
        (12, 25, 16, 30, "●", 1, 1, 0),
    ]
    page = _page(words, rows=(0, 20, 40))
    assert len(extract_matrix_page(page, ("1.1",))) == 2


def test_same_cell_duplicate_symbols_are_ambiguous():
    words = [
        (2, 5, 8, 10, "CourseA", 0, 0, 0),
        (12, 5, 13, 10, "●", 1, 0, 0),
        (17, 5, 18, 10, "●", 1, 1, 0),
    ]
    with pytest.raises(MatrixExtractionError, match="ambiguous"):
        extract_matrix_page(_page(words), ("1.1",))


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
    assert len(relations) == 103
    assert all(item["indicator_id"] in indicators for item in relations)
    assert all(item["verification_status"] == "extracted" for item in relations)
    anchors = {(item["indicator_id"], round(item["symbol_coordinates"]["x"], 2), round(item["symbol_coordinates"]["y"], 2)) for item in relations}
    assert ("6.1", 468.94, 155.84) in anchors
    assert ("12.2", 766.06, 520.40) in anchors
