"""Reading and writing designs in the legacy text format.

The format, as consumed by the original C++ tools, is a stream of
whitespace-separated integers (line breaks are not significant)::

    N k                      # number of rows, number of columns
    l_1 l_2 ... l_k          # number of levels of every column
    0 0 ... 0                # k + 1 reserved zeros (ignored by the tools)
    x_11 x_12 ... x_1k       # N rows of k values each
    ...

Unlike the C++ tools, the parser is strict: it rejects any file whose token
stream does not match its header exactly, instead of silently mis-reading it.
"""

from __future__ import annotations

import os
import re

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


def parse_design(text: str, *, source: str = "<string>") -> Design:
    """Parse a design from the contents of a legacy-format file.

    Args:
        text: the file contents.
        source: name used in error messages (e.g. the file path).

    Raises:
        DesignFormatError: if the text is not a well-formed design.
    """
    tokens = _Tokens(text, source)
    num_rows = tokens.take("the number of rows")
    num_cols = tokens.take("the number of columns")
    if num_rows < 1 or num_cols < 1:
        raise tokens.error(
            f"header must declare at least one row and one column, got {num_rows} x {num_cols}"
        )

    levels = [tokens.take(f"the level count of column {j}") for j in range(num_cols)]

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

    try:
        return Design(levels, rows)
    except DesignFormatError:
        raise
    except DesignError as exc:
        raise tokens.error(str(exc)) from exc


def load_design(path: str | os.PathLike[str]) -> Design:
    """Read a design from a legacy-format file (see :func:`parse_design`)."""
    with open(path, encoding="utf-8") as handle:
        return parse_design(handle.read(), source=os.fspath(path))


def dump_design(design: Design) -> str:
    """Serialise a design to the legacy text format (readable by the C++ tools)."""
    lines = [
        f"{design.num_rows} {design.num_columns}",
        " ".join(map(str, design.levels)),
        *(["0"] * (design.num_columns + 1)),
        *(" ".join(map(str, row)) for row in design.rows),
    ]
    return "\n".join(lines) + "\n"
