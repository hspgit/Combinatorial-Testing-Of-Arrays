"""Reading and writing designs in legacy and modern formats.

Supported input formats:
* Legacy text format: upfront row/column declarations, level counts, and reserved zeros.
* Raw numeric matrices: space/tab-separated rows of integers where N (rows),
  k (columns), and levels (max(val) + 1 per column) are auto-inferred.
* Delimited files (CSV / TSV): comma-, semicolon-, or tab-delimited files with optional
  headers and categorical string values automatically mapped to integers.
* Explicit level counts via the ``levels`` parameter or ``--levels`` CLI flag,
  overriding inferred levels when some levels are unobserved in the data.
"""

from __future__ import annotations

import csv
import os
import re
from collections.abc import Sequence

from cit_tools.design import Design, DesignError

__all__ = ["DesignFormatError", "dump_design", "load_design", "parse_design"]

_INT_RE = re.compile(r"[+-]?[0-9]+")


class DesignFormatError(DesignError):
    """Raised when a design file cannot be parsed."""


class _Tokens:
    def __init__(self, text: str, source: str) -> None:
        self._tokens = text.split()
        self._pos = 0
        self.source = source

    def error(self, message: str) -> DesignFormatError:
        return DesignFormatError(f"{self.source}: {message}")

    @property
    def remaining(self) -> int:
        return len(self._tokens) - self._pos

    def take(self, what: str) -> int:
        if self._pos >= len(self._tokens):
            raise self.error(f"unexpected end of file while reading {what}")
        token = self._tokens[self._pos]
        if not _INT_RE.fullmatch(token):
            raise self.error(f"expected an integer for {what}, found {token!r}")
        self._pos += 1
        return int(token)


def _is_comment_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return False
    if stripped.startswith("# ") or stripped == "#":
        return True
    return not any(c in stripped for c in (",", ";", "\t"))


def _detect_delimiter(text: str) -> str | None:
    lines = [
        line.strip() for line in text.splitlines() if line.strip() and not _is_comment_line(line)
    ]
    if not lines:
        return None
    sample = "\n".join(lines[:20])
    try:
        d = csv.Sniffer().sniff(sample, delimiters=",\t;")
        return d.delimiter
    except Exception:
        first = lines[0]
        for c in (",", ";", "\t"):
            if c in first:
                return c
        return None


def _validate_explicit_levels(levels: Sequence[int], num_cols: int, source: str) -> tuple[int, ...]:
    levels_list = list(levels)
    if len(levels_list) != num_cols:
        raise DesignFormatError(
            f"{source}: expected {num_cols} levels (one per column), got {len(levels_list)}"
        )
    for j, lvl in enumerate(levels_list):
        if not isinstance(lvl, int) or isinstance(lvl, bool) or lvl < 1:
            raise DesignFormatError(
                f"{source}: levels[{j}] must be a positive integer, got {lvl!r}"
            )
    return tuple(levels_list)


def _parse_legacy(
    text: str,
    source: str,
    levels: Sequence[int] | None = None,
) -> Design:
    clean_lines = [line for line in text.splitlines() if not _is_comment_line(line)]
    tokens = _Tokens("\n".join(clean_lines), source)
    num_rows = tokens.take("the number of rows")
    num_cols = tokens.take("the number of columns")
    if num_rows < 1 or num_cols < 1:
        raise tokens.error(
            f"header must declare at least one row and one column, got {num_rows} x {num_cols}"
        )

    header_levels = [tokens.take(f"the level count of column {j}") for j in range(num_cols)]

    for p in range(num_cols + 1):
        value = tokens.take(f"reserved zero #{p + 1} of {num_cols + 1}")
        if value != 0:
            raise tokens.error(
                f"expected {num_cols + 1} reserved zeros after the levels line, but zero "
                f"#{p + 1} is {value}; the header probably declares the wrong number of "
                f"columns ({num_cols})"
            )

    rows = [
        [tokens.take(f"the value at row {i}, column {j}") for j in range(num_cols)]
        for i in range(num_rows)
    ]

    if tokens.remaining:
        raise tokens.error(
            f"{tokens.remaining} unexpected value(s) after the {num_rows} x {num_cols} "
            f"data block; check the row/column counts in the header"
        )

    levels_to_use = (
        _validate_explicit_levels(levels, num_cols, tokens.source)
        if levels is not None
        else tuple(header_levels)
    )

    try:
        return Design(levels_to_use, rows)
    except DesignFormatError:
        raise
    except DesignError as exc:
        raise tokens.error(str(exc)) from exc


def _is_legacy_input(text: str) -> bool:
    lines = [
        line.strip() for line in text.splitlines() if line.strip() and not _is_comment_line(line)
    ]
    if not lines:
        return False

    tokens = " ".join(lines).split()
    if len(tokens) < 2:
        return False

    line0_tokens = lines[0].split()
    # Check invalid legacy header like "2 three"
    if (
        len(line0_tokens) == 2
        and _INT_RE.fullmatch(line0_tokens[0])
        and not _INT_RE.fullmatch(line0_tokens[1])
    ):
        return True

    if not (_INT_RE.fullmatch(tokens[0]) and _INT_RE.fullmatch(tokens[1])):
        return False

    n_decl, k_decl = int(tokens[0]), int(tokens[1])
    if len(lines) == 1:
        return (
            k_decl >= 1
            and n_decl >= 1
            and len(tokens) >= 2 + 2 * k_decl + 1
            and all(t == "0" for t in tokens[2 + k_decl : 2 + 2 * k_decl + 1])
        )

    has_zero_lines = any(line == "0" for line in lines[2:])
    has_all_zero_line = any(set(line.split()) == {"0"} for line in lines[2:])
    has_zeros_at_reserved_pos = (
        n_decl >= 1
        and len(tokens) > 2 + k_decl
        and tokens[2 + k_decl] == "0"
        and (
            (len(tokens) > 2 + 2 * k_decl and tokens[2 + 2 * k_decl] == "0")
            or any(set(line.split()) == {"0"} for line in lines[2:4])
        )
    )
    has_corrupted_zeros_line = (
        n_decl >= 1
        and k_decl >= 1
        and len(lines) >= 3
        and len(lines[2].split()) == k_decl + 1
        and lines[2].split()[0] == "0"
    )

    return len(line0_tokens) == 2 and (
        has_zero_lines or has_all_zero_line or has_zeros_at_reserved_pos or has_corrupted_zeros_line
    )


def _read_cells(text: str, source: str, delimiter: str | None) -> list[list[str]]:
    raw_lines = [
        line.strip() for line in text.splitlines() if line.strip() and not _is_comment_line(line)
    ]
    if not raw_lines:
        raise DesignFormatError(f"{source}: unexpected end of file while reading data rows")

    delim = delimiter
    if delim is None:
        delim = _detect_delimiter(text)

    if delim is not None:
        try:
            reader = csv.reader(raw_lines, delimiter=delim, skipinitialspace=True, strict=True)
            rows_cells = [[cell.strip() for cell in row] for row in reader]
        except csv.Error as exc:
            raise DesignFormatError(f"{source}: {exc}") from exc
    else:
        rows_cells = [line.split() for line in raw_lines]

    rows_cells = [r for r in rows_cells if r]
    if not rows_cells:
        raise DesignFormatError(f"{source}: unexpected end of file while reading data rows")

    k = len(rows_cells[0])
    if k < 1:
        raise DesignFormatError(f"{source}: a design needs at least one column")
    for i, row in enumerate(rows_cells):
        if len(row) != k:
            raise DesignFormatError(f"{source}: row {i} has {len(row)} values, expected {k}")

    return rows_cells


def _detect_has_header(rows_cells: list[list[str]], header: bool | None, num_cols: int) -> bool:
    if header is not None:
        return header
    if len(rows_cells) <= 1:
        return False

    row0 = rows_cells[0]
    if all(_INT_RE.fullmatch(c) for c in row0):
        return False
    if all(_INT_RE.fullmatch(c) for r in rows_cells[1:] for c in r):
        return True

    if any(row0[c] in {r[c] for r in rows_cells[1:]} for c in range(num_cols)):
        return False

    return any(len({r[c] for r in rows_cells[1:]}) < len(rows_cells[1:]) for c in range(num_cols))


def _convert_columns(
    data_cells: list[list[str]], num_cols: int, source: str
) -> tuple[tuple[int, ...], tuple[tuple[int, ...], ...]]:
    inferred_levels: list[int] = []
    cols_data: list[list[int]] = []

    for j in range(num_cols):
        col_values = [row[j] for row in data_cells]
        if all(_INT_RE.fullmatch(v) for v in col_values):
            int_vals = [int(v) for v in col_values]
            for i, v in enumerate(int_vals):
                if v < 0:
                    raise DesignFormatError(
                        f"{source}: value {v} at row {i}, column {j} is outside the "
                        f"column's range (must be non-negative)"
                    )
            inferred_levels.append(max(int_vals) + 1)
            cols_data.append(int_vals)
        else:
            cat_map: dict[str, int] = {}
            mapped_vals: list[int] = []
            for item in col_values:
                if item not in cat_map:
                    cat_map[item] = len(cat_map)
                mapped_vals.append(cat_map[item])
            inferred_levels.append(len(cat_map))
            cols_data.append(mapped_vals)

    num_rows = len(data_cells)
    final_rows = tuple(tuple(cols_data[j][i] for j in range(num_cols)) for i in range(num_rows))
    return tuple(inferred_levels), final_rows


def _parse_modern(
    text: str,
    source: str,
    levels: Sequence[int] | None = None,
    header: bool | None = None,
    delimiter: str | None = None,
) -> Design:
    rows_cells = _read_cells(text, source, delimiter)
    num_cols = len(rows_cells[0])
    has_header = _detect_has_header(rows_cells, header, num_cols)

    data_cells = rows_cells[1:] if has_header else rows_cells
    if not data_cells:
        raise DesignFormatError(f"{source}: a design needs at least one data row")

    inferred_levels, final_rows = _convert_columns(data_cells, num_cols, source)

    final_levels = (
        _validate_explicit_levels(levels, num_cols, source)
        if levels is not None
        else inferred_levels
    )

    try:
        return Design(final_levels, final_rows)
    except DesignError as exc:
        raise DesignFormatError(f"{source}: {exc}") from exc


def parse_design(
    text: str,
    *,
    source: str = "<string>",
    levels: Sequence[int] | None = None,
    header: bool | None = None,
    delimiter: str | None = None,
    format: str | None = None,
) -> Design:
    """Parse a design from text.

    Supports both the legacy text format and modern formats:
    - Raw numeric matrices (space/tab-separated rows of integers) where N, k, and
      levels (max(val) + 1 per column) are auto-inferred.
    - Delimited files (CSV / TSV) with optional headers and categorical string values,
      automatically mapping categorical strings to integers.
    - Overriding inferred levels via the `levels` parameter when some levels are
      unobserved in the data.

    Args:
        text: file or input contents.
        source: name used in error messages (e.g. file path).
        levels: optional explicit level count per column (overrides inferred levels).
        header: whether a header row is present in CSV/TSV (default: auto-detect).
        delimiter: optional field delimiter (e.g. ',' or '\t').
        format: input format ('auto', 'legacy', 'matrix', 'raw', 'csv', 'tsv').

    Raises:
        DesignFormatError: if the text cannot be parsed as a valid design.
    """
    stripped = text.strip()
    if not stripped:
        raise DesignFormatError(
            f"{source}: unexpected end of file while reading the number of rows"
        )

    if format == "legacy":
        return _parse_legacy(text, source, levels=levels)
    if format in ("matrix", "raw"):
        return _parse_modern(text, source, levels=levels, header=False, delimiter=None)
    if format in ("csv", "tsv"):
        delim = "," if format == "csv" else "\t"
        return _parse_modern(text, source, levels=levels, header=header, delimiter=delim)
    if format not in (None, "auto"):
        raise ValueError(f"unknown design format: {format!r}")

    if delimiter is not None and delimiter != "":
        return _parse_modern(text, source, levels=levels, header=header, delimiter=delimiter)

    if _is_legacy_input(text):
        return _parse_legacy(text, source, levels=levels)

    return _parse_modern(text, source, levels=levels, header=header, delimiter=delimiter)


def load_design(
    path: str | os.PathLike[str],
    *,
    levels: Sequence[int] | None = None,
    header: bool | None = None,
    delimiter: str | None = None,
    format: str | None = None,
) -> Design:
    """Read a design from a file (see :func:`parse_design`).

    Auto-detects format (legacy, raw matrix, CSV, TSV) and infers delimiter
    from '.csv' / '.tsv' file extensions if not specified.
    """
    fspath = os.fspath(path)
    if delimiter is None:
        if fspath.lower().endswith(".csv"):
            delimiter = ","
        elif fspath.lower().endswith(".tsv"):
            delimiter = "\t"

    with open(path, encoding="utf-8") as handle:
        return parse_design(
            handle.read(),
            source=fspath,
            levels=levels,
            header=header,
            delimiter=delimiter,
            format=format,
        )


def dump_design(design: Design) -> str:
    """Serialise a design to the legacy text format (readable by the C++ tools)."""
    lines = [
        f"{design.num_rows} {design.num_columns}",
        " ".join(map(str, design.levels)),
        *(["0"] * (design.num_columns + 1)),
        *(" ".join(map(str, row)) for row in design.rows),
    ]
    return "\n".join(lines) + "\n"
