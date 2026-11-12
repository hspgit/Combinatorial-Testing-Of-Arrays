"""Unit tests for cit_tools.io."""

from __future__ import annotations

import pytest

from cit_tools.design import Design
from cit_tools.io import DesignFormatError, dump_design, load_design, parse_design
from support import OLD_DIR


def test_parse_and_dump_roundtrip() -> None:
    original = Design([2, 3, 2], [[0, 1, 0], [1, 2, 1]])
    text = dump_design(original)
    parsed = parse_design(text)
    assert parsed.levels == original.levels
    assert parsed.rows == original.rows


def test_parse_design_whitespace_flexibility() -> None:
    content = """
    2   3
    2   3   2

    0   0   0   0

    0   1   0
    1   2   1
    """
    d = parse_design(content)
    assert d.num_rows == 2
    assert d.num_columns == 3
    assert d.levels == (2, 3, 2)
    assert d.rows == ((0, 1, 0), (1, 2, 1))


def test_parse_design_format_errors() -> None:
    # Empty
    with pytest.raises(DesignFormatError, match="unexpected end of file"):
        parse_design("")

    # Invalid header numbers
    with pytest.raises(DesignFormatError, match="at least one row and one column"):
        parse_design("0 3\n2 2 2\n0 0 0 0\n")

    # Non-integer token
    with pytest.raises(DesignFormatError, match="expected an integer"):
        parse_design("2 three\n")

    # Non-zero in reserved zeros
    with pytest.raises(DesignFormatError, match="expected 3 reserved zeros"):
        parse_design("1 2\n2 2\n0 1 0\n0 0\n")

    # Truncated data
    with pytest.raises(DesignFormatError, match="unexpected end of file"):
        parse_design("2 2\n2 2\n0 0 0\n0 0\n")

    # Trailing unexpected tokens
    with pytest.raises(DesignFormatError, match="unexpected value"):
        parse_design("1 2\n2 2\n0 0 0\n0 0\n99\n")


def test_legacy_corrupted_files_rejected() -> None:
    # test2.txt has 4 declared cols but 5 columns of data (fails on reserved zeros)
    with pytest.raises(DesignFormatError, match="expected 5 reserved zeros"):
        load_design(OLD_DIR / "test2.txt")

    # test4.txt and test5.txt have value 2 in a 2-level column
    with pytest.raises(DesignFormatError, match="outside the column's range"):
        load_design(OLD_DIR / "test4.txt")

    with pytest.raises(DesignFormatError, match="outside the column's range"):
        load_design(OLD_DIR / "test5.txt")
