"""The :class:`Design` data model."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

__all__ = ["Design", "DesignError", "column_label", "interaction_label"]


class DesignError(ValueError):
    """Raised when a design, or a parameter used to evaluate it, is invalid."""


def _is_int(value: object) -> bool:
    # bool is a subclass of int, but True/False are never meaningful here.
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True, slots=True, init=False)
class Design:
    """An ``N x k`` test design.

    Attributes:
        levels: number of levels of each column (factor); ``levels[j] >= 1``.
        rows: the runs (test cases); ``rows[i][j]`` is in ``range(levels[j])``.

    Both attributes are stored as tuples, so a ``Design`` is immutable and
    hashable.  All invariants are checked on construction.
    """

    levels: tuple[int, ...]
    rows: tuple[tuple[int, ...], ...]

    def __init__(self, levels: Iterable[int], rows: Iterable[Iterable[int]]) -> None:
        levels_t = tuple(levels)
        rows_t = tuple(tuple(row) for row in rows)
        _validate(levels_t, rows_t)
        object.__setattr__(self, "levels", levels_t)
        object.__setattr__(self, "rows", rows_t)

    @property
    def num_rows(self) -> int:
        """Number of runs ``N``."""
        return len(self.rows)

    @property
    def num_columns(self) -> int:
        """Number of columns (factors) ``k``."""
        return len(self.levels)

    def column(self, index: int) -> tuple[int, ...]:
        """Return the values of column ``index``."""
        return tuple(row[index] for row in self.rows)

    def check_strength(self, strength: int) -> None:
        """Raise :class:`DesignError` unless ``1 <= strength <= num_columns``."""
        if not _is_int(strength):
            raise DesignError(f"strength t must be an integer, got {strength!r}")
        if not 1 <= strength <= self.num_columns:
            raise DesignError(
                f"strength t must be between 1 and the number of columns "
                f"({self.num_columns}), got {strength}"
            )


def _validate(levels: tuple[int, ...], rows: tuple[tuple[int, ...], ...]) -> None:
    if not levels:
        raise DesignError("a design needs at least one column")
    for j, level in enumerate(levels):
        if not _is_int(level) or level < 1:
            raise DesignError(f"levels[{j}] must be a positive integer, got {level!r}")
    if not rows:
        raise DesignError("a design needs at least one row")
    k = len(levels)
    for i, row in enumerate(rows):
        if len(row) != k:
            raise DesignError(f"row {i} has {len(row)} values, expected {k}")
        for j, (value, level) in enumerate(zip(row, levels, strict=True)):
            if not _is_int(value):
                raise DesignError(f"value at row {i}, column {j} is not an integer: {value!r}")
            if not 0 <= value < level:
                raise DesignError(
                    f"value {value} at row {i}, column {j} is outside the column's "
                    f"range 0..{level - 1}"
                )


def column_label(index: int) -> str:
    """Spreadsheet-style column name: 0 -> 'a', 25 -> 'z', 26 -> 'aa', ...

    For the first 26 columns this matches the letters used by the original C++
    tools.
    """
    if index < 0:
        raise ValueError(f"column index must be non-negative, got {index}")
    label = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        label = chr(ord("a") + rem) + label
    return label


def interaction_label(columns: Sequence[int]) -> str:
    """Name of a column combination, e.g. ``(0, 2) -> 'a*c'``."""
    return "*".join(column_label(c) for c in columns)
