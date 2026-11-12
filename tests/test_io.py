"""Unit tests for cit_tools.io."""

from __future__ import annotations

from pathlib import Path

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


def test_parse_raw_numeric_matrix() -> None:
    content = """
    0 1 0
    1 2 1
    0 0 1
    """
    d = parse_design(content)
    assert d.num_rows == 3
    assert d.num_columns == 3
    assert d.levels == (2, 3, 2)
    assert d.rows == ((0, 1, 0), (1, 2, 1), (0, 0, 1))

    # Two columns, uniform lines
    content_2col = "0 1\n1 0\n"
    d_2col = parse_design(content_2col)
    assert d_2col.num_rows == 2
    assert d_2col.num_columns == 2
    assert d_2col.levels == (2, 2)
    assert d_2col.rows == ((0, 1), (1, 0))


def test_parse_raw_numeric_matrix_with_unobserved_levels() -> None:
    # Column has 0 and 2; value 1 is unobserved -> auto-inferred level is max(val) + 1 = 3
    content = "0 2\n0 2\n"
    d = parse_design(content)
    assert d.levels == (1, 3)

    # Explicit levels overrides inferred levels
    d_override = parse_design("0 1\n1 2\n", levels=[3, 4])
    assert d_override.levels == (3, 4)
    assert d_override.rows == ((0, 1), (1, 2))


def test_parse_csv_with_header_and_categorical() -> None:
    csv_content = """Browser,OS,Resolution
    Chrome,Windows,1080p
    Firefox,Linux,4k
    Chrome,MacOS,1080p
    """
    d = parse_design(csv_content)
    assert d.num_rows == 3
    assert d.num_columns == 3
    assert d.levels == (2, 3, 2)
    assert d.rows == ((0, 0, 0), (1, 1, 1), (0, 2, 0))


def test_parse_csv_without_header() -> None:
    csv_content = """Chrome,Windows
    Firefox,Linux
    Chrome,MacOS
    """
    d = parse_design(csv_content)
    assert d.num_rows == 3
    assert d.num_columns == 2
    assert d.levels == (2, 3)
    assert d.rows == ((0, 0), (1, 1), (0, 2))

    # Explicit header=False
    d_no_header = parse_design("0,1,0\n1,2,1\n", header=False)
    assert d_no_header.num_rows == 2
    assert d_no_header.levels == (2, 3, 2)


def test_parse_csv_with_quoted_fields() -> None:
    csv_content = '"Windows 11, Pro",Chrome\n"Ubuntu 22.04",Firefox\n'
    d = parse_design(csv_content)
    assert d.num_rows == 2
    assert d.num_columns == 2
    assert d.levels == (2, 2)
    assert d.rows == ((0, 0), (1, 1))


def test_load_real_tsv_file() -> None:
    # old/13mixed2l3l_test.txt has headers and 13 rows x 26 columns
    d = load_design(OLD_DIR / "13mixed2l3l_test.txt")
    assert d.num_rows == 13
    assert d.num_columns == 26
    expected_levels = (2,) * 13 + (3,) * 13
    assert d.levels == expected_levels


def test_modern_format_errors() -> None:
    # Inconsistent row length
    with pytest.raises(DesignFormatError, match="row 1 has 2 values, expected 3"):
        parse_design("0 1 0\n1 2\n0 0 1\n")

    # Negative value in numeric matrix
    with pytest.raises(DesignFormatError, match="must be non-negative"):
        parse_design("0 -1\n1 0\n")

    # Explicit levels count mismatch
    with pytest.raises(DesignFormatError, match="expected 2 levels"):
        parse_design("0 1\n1 0\n", levels=[2])

    # Explicit levels with non-positive integer
    with pytest.raises(DesignFormatError, match="must be a positive integer"):
        parse_design("0 1\n1 0\n", levels=[2, 0])

    # Explicit levels smaller than observed value
    with pytest.raises(DesignFormatError, match="outside the column's range"):
        parse_design("0 2\n1 0\n", levels=[2, 2])

    # Unknown format
    with pytest.raises(ValueError, match="unknown design format"):
        parse_design("0 1\n", format="yaml")


def test_explicit_format_selection() -> None:
    # Explicit format="raw" / "matrix"
    d_raw = parse_design("0 1\n1 0\n", format="matrix")
    assert d_raw.levels == (2, 2)

    # Explicit format="csv"
    d_csv = parse_design("A,B\n0,1\n", format="csv")
    assert d_csv.levels == (1, 2)

    # Explicit format="tsv"
    d_tsv = parse_design("A\tB\n0\t1\n", format="tsv")
    assert d_tsv.levels == (1, 2)

    # Explicit format="legacy" with levels override
    legacy_text = "1 2\n2 2\n0 0 0\n0 0\n"
    d_legacy = parse_design(legacy_text, format="legacy", levels=[3, 3])
    assert d_legacy.levels == (3, 3)

    # Explicit format="auto"
    d_auto = parse_design("0 1\n1 0\n", format="auto")
    assert d_auto.levels == (2, 2)


def test_modern_edge_cases(tmp_path: Path) -> None:
    # Semicolon delimiter
    d_semi = parse_design("0;1;2\n1;0;1\n")
    assert d_semi.num_columns == 3
    assert d_semi.levels == (2, 2, 3)

    # Comments ignored
    d_comments = parse_design("# factor design\n0 1\n# middle comment\n1 0\n")
    assert d_comments.num_rows == 2

    # Single-line legacy format
    d_single_legacy = parse_design("1 2 2 2 0 0 0 0 1")
    assert d_single_legacy.num_rows == 1
    assert d_single_legacy.num_columns == 2
    assert d_single_legacy.levels == (2, 2)

    # load_design with .csv and .tsv extensions
    csv_file = tmp_path / "design.csv"
    csv_file.write_text("0,1\n1,0\n", encoding="utf-8")
    assert load_design(csv_file).levels == (2, 2)

    tsv_file = tmp_path / "design.tsv"
    tsv_file.write_text("0\t1\n1\t0\n", encoding="utf-8")
    assert load_design(tsv_file).levels == (2, 2)


def test_comments_with_commas_and_semicolons() -> None:
    # Raw numeric matrix with commas and semicolons in comments
    raw_content = (
        "# Design: Factor 1, Factor 2; version 1.0\n0 1\n# another comment, with comma\n1 0\n"
    )
    d_raw = parse_design(raw_content)
    assert d_raw.num_rows == 2
    assert d_raw.num_columns == 2
    assert d_raw.levels == (2, 2)
    assert d_raw.rows == ((0, 1), (1, 0))

    # Legacy format with commas in comments
    legacy_content = (
        "# Legacy design v1, tested on linux\n4 3\n2 3 2\n0\n0\n0\n0\n0 2 1\n1 1 1\n0 0 0\n1 2 1\n"
    )
    d_legacy = parse_design(legacy_content)
    assert d_legacy.num_rows == 4
    assert d_legacy.num_columns == 3
    assert d_legacy.levels == (2, 3, 2)


def test_tsv_with_quoted_commas() -> None:
    tsv_content = '"Smith, John"\tEngineer\n"Doe, Jane"\tManager\n'
    d = parse_design(tsv_content)
    assert d.num_rows == 2
    assert d.num_columns == 2
    assert d.levels == (2, 2)
    assert d.rows == ((0, 0), (1, 1))


def test_csv_with_hex_colors_starting_with_hash() -> None:
    csv_content = "#FF0000,Red\n#00FF00,Green\n#0000FF,Blue\n"
    d = parse_design(csv_content)
    assert d.num_rows == 3
    assert d.num_columns == 2
    assert d.levels == (3, 3)
    assert d.rows == ((0, 0), (1, 1), (2, 2))


def test_jagged_raw_matrix_starting_with_two_columns() -> None:
    # A jagged matrix whose first row has 2 columns must report a jagged row error,
    # not be misdiagnosed as an invalid legacy file header.
    with pytest.raises(DesignFormatError, match="row 1 has 3 values, expected 2"):
        parse_design("0 1\n1 2 0\n0 1\n")


def test_csv_malformed_quote_error_handling() -> None:
    with pytest.raises(DesignFormatError, match="expected after"):
        parse_design('"ab"c,d\n', format="csv")
