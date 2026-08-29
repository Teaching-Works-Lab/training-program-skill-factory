"""Extract candidate course-to-indicator relations from a PDF matrix page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


_EPSILON = 0.75
_MIN_LINE_LENGTH = 20.0
_SYMBOL_GLYPHS = frozenset("●•·○◉■▪⬤◆�")


class MatrixExtractionError(ValueError):
    """Raised when a matrix page cannot be assigned without guessing."""


@dataclass(frozen=True)
class Grid:
    columns: tuple[float, ...]
    rows: tuple[float, ...]


def _merge(values: Sequence[float], tolerance: float = _EPSILON) -> tuple[float, ...]:
    if not values:
        return ()
    ordered = sorted(float(value) for value in values)
    groups: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return tuple(sum(group) / len(group) for group in groups)


def cell_index(position: float, boundaries: Sequence[float]) -> int:
    """Return the half-open cell containing *position* (last edge excluded)."""
    if len(boundaries) < 2:
        raise ValueError("outside grid: fewer than two boundaries")
    for index, (left, right) in enumerate(zip(boundaries, boundaries[1:])):
        if left <= position < right:
            return index
    raise ValueError(f"position {position} outside grid {tuple(boundaries)}")


def _grid_from_page(page: Any) -> Grid:
    vertical: list[float] = []
    horizontal: list[float] = []
    for drawing in page.get_drawings():
        for item in drawing.get("items", ()):
            if not item or item[0] != "l":
                continue
            start, end = item[1], item[2]
            if abs(start.x - end.x) <= _EPSILON and abs(start.y - end.y) >= _MIN_LINE_LENGTH:
                vertical.append((start.x + end.x) / 2)
            elif abs(start.y - end.y) <= _EPSILON and abs(start.x - end.x) >= _MIN_LINE_LENGTH:
                horizontal.append((start.y + end.y) / 2)
    columns = _merge(vertical)
    rows = _merge(horizontal)
    return Grid(columns=columns, rows=rows)


def _is_symbol(text: str) -> bool:
    value = text.strip()
    return bool(value) and all(char in _SYMBOL_GLYPHS for char in value)


def _drawing_symbols(page: Any) -> list[tuple[float, float]]:
    """Return centers of small filled circle/square drawing marks."""
    symbols: list[tuple[float, float]] = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None or not (1.5 <= rect.width <= 12 and 1.5 <= rect.height <= 12):
            continue
        items = drawing.get("items", ())
        has_curve = any(item and item[0] in {"c", "re"} for item in items)
        fill = drawing.get("fill")
        if has_curve and (fill is not None or any(item and item[0] == "c" for item in items)):
            symbols.append(((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2))
    return symbols


def extract_matrix_page(page: Any, indicator_ids: Sequence[str]) -> list[dict[str, Any]]:
    """Extract relation candidates from one matrix page without spatial guessing."""
    grid = _grid_from_page(page)
    page_number = int(getattr(page, "number", 0)) + 1
    expected_columns = len(indicator_ids)
    actual_columns = len(grid.columns) - 2
    if actual_columns != expected_columns:
        raise MatrixExtractionError(
            f"page {page_number}: detected {actual_columns} indicator columns, expected "
            f"{expected_columns}; boundaries={grid.columns}"
        )
    if len(grid.rows) < 2:
        raise MatrixExtractionError(f"page {page_number}: no table rows detected")

    words = page.get_text("words")
    candidates: list[tuple[float, float]] = []
    for word in words:
        x0, y0, x1, y1, text = word[:5]
        if _is_symbol(text):
            center = ((x0 + x1) / 2, (y0 + y1) / 2)
            if not (grid.columns[0] <= center[0] < grid.columns[-1]):
                raise MatrixExtractionError(
                    f"page {page_number}: symbol at ({center[0]:.2f}, {center[1]:.2f}) outside grid"
                )
            candidates.append(center)
    candidates.extend(_drawing_symbols(page))

    relations: list[dict[str, Any]] = []
    for x, y in candidates:
        try:
            col = cell_index(x, grid.columns)
            row = cell_index(y, grid.rows)
        except ValueError as exc:
            raise MatrixExtractionError(
                f"page {page_number}: symbol at ({x:.2f}, {y:.2f}) outside detected cell"
            ) from exc
        if col == 0:
            raise MatrixExtractionError(
                f"page {page_number}: symbol at ({x:.2f}, {y:.2f}) is in course-label cell"
            )
        course_words = []
        for word in words:
            x0, y0, x1, y1, text = word[:5]
            center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
            if cell_index(center_x, grid.columns) == 0 and grid.rows[row] <= center_y < grid.rows[row + 1]:
                course_words.append((x0, text))
        if not course_words:
            raise MatrixExtractionError(
                f"page {page_number}: symbol at ({x:.2f}, {y:.2f}) has no course label in row {row}"
            )
        if sum(1 for item in relations if item["course_label"] == " ".join(t for _, t in sorted(course_words)) and item["indicator_id"] == indicator_ids[col - 1]) > 0:
            raise MatrixExtractionError(f"page {page_number}: ambiguous duplicate symbol at ({x:.2f}, {y:.2f})")
        label = " ".join(text for _, text in sorted(course_words))
        relations.append({
            "course_label": label,
            "indicator_id": indicator_ids[col - 1],
            "page": page_number,
            "symbol_coordinates": {"x": x, "y": y},
            "verification_status": "extracted",
        })
    return relations
