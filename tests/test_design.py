"""Unit tests for cit_tools.design."""

from __future__ import annotations

import pytest

from cit_tools.design import Design, DesignError, column_label, interaction_label


def test_design_valid() -> None:
    levels = [2, 3]
    rows = [[0, 0], [1, 2]]
    d = Design(levels, rows)
    assert d.num_rows == 2
    assert d.num_columns == 2
    assert d.levels == (2, 3)
    assert d.rows == ((0, 0), (1, 2))
    assert d.column(0) == (0, 1)
    assert d.column(1) == (0, 2)


def test_design_immutable() -> None:
    d = Design([2, 2], [[0, 0]])
    with pytest.raises((AttributeError, TypeError)):
        d.levels = (3, 3)  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        d.rows = ()  # type: ignore[misc]


def test_design_validation_errors() -> None:
    # Empty levels
    with pytest.raises(DesignError, match="at least one column"):
        Design([], [[0]])

    # Invalid level values
    with pytest.raises(DesignError, match="must be a positive integer"):
        Design([0], [[0]])
    with pytest.raises(DesignError, match="must be a positive integer"):
        Design([-1], [[0]])
    with pytest.raises(DesignError, match="must be a positive integer"):
        Design([True], [[0]])  # bools rejected

    # Empty rows
    with pytest.raises(DesignError, match="at least one row"):
        Design([2], [])

    # Row length mismatch
    with pytest.raises(DesignError, match="row 0 has 1 values, expected 2"):
        Design([2, 2], [[0]])

    # Value type check
    with pytest.raises(DesignError, match="not an integer"):
        Design([2], [[False]])  # bool rejected
    with pytest.raises(DesignError, match="not an integer"):
        Design([2], [[1.5]])  # type: ignore[list-item]

    # Value out of range
    with pytest.raises(DesignError, match=r"outside the column's range 0\.\.1"):
        Design([2], [[2]])
    with pytest.raises(DesignError, match=r"outside the column's range 0\.\.1"):
        Design([2], [[-1]])


def test_check_strength() -> None:
    d = Design([2, 3, 2], [[0, 0, 0]])
    d.check_strength(1)
    d.check_strength(2)
    d.check_strength(3)

    with pytest.raises(DesignError, match="must be between 1 and the number of columns"):
        d.check_strength(0)
    with pytest.raises(DesignError, match="must be between 1 and the number of columns"):
        d.check_strength(4)
    with pytest.raises(DesignError, match="must be an integer"):
        d.check_strength(True)


def test_column_and_interaction_labels() -> None:
    assert column_label(0) == "a"
    assert column_label(1) == "b"
    assert column_label(25) == "z"
    assert column_label(26) == "aa"
    assert column_label(27) == "ab"
    assert column_label(51) == "az"
    assert column_label(52) == "ba"

    with pytest.raises(ValueError, match="non-negative"):
        column_label(-1)

    assert interaction_label([0, 1]) == "a*b"
    assert interaction_label([0, 2, 26]) == "a*c*aa"
