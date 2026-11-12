"""Unit tests for cit_tools metrics and math properties."""

from __future__ import annotations

import random
from fractions import Fraction
from itertools import combinations
from math import prod

import pytest

from cit_tools.design import Design, DesignError
from cit_tools.metrics.chi_square import (
    chi_square,
    chi_square_efficiency,
    chi_square_lower_bound,
    efficiency_from,
    interaction_chi_square,
    pairwise_chi_square_matrix,
)
from cit_tools.metrics.coverage import count_possible_interactions, coverage
from cit_tools.metrics.saturation import degree_of_saturation, is_supersaturated
from cit_tools.report import build_report
from support import brute_chi_square, brute_coverage, random_design


def test_saturation_properties() -> None:
    # 1 row design cannot define DoS
    d1 = Design([2, 3], [[0, 0]])
    with pytest.raises(DesignError, match="at least 2 rows"):
        degree_of_saturation(d1)

    # N=5, levels=[2, 2, 3] -> sum(l - 1) = 4, DoS = 4 / (5 - 1) = 1.0 (not supersaturated)
    d2 = Design([2, 2, 3], [[0, 0, 0], [0, 0, 1], [0, 0, 2], [1, 1, 0], [1, 1, 1]])
    assert degree_of_saturation(d2) == Fraction(1, 1)
    assert not is_supersaturated(d2)

    # N=4, levels=[2, 3, 2] -> sum(l - 1) = 1 + 2 + 1 = 4, DoS = 4 / 3 = 1.333... (supersaturated)
    d3 = Design([2, 3, 2], [[0, 0, 0], [1, 1, 1], [0, 2, 1], [1, 0, 0]])
    assert degree_of_saturation(d3) == Fraction(4, 3)
    assert is_supersaturated(d3)


def test_count_possible_interactions_matches_definition() -> None:
    rng = random.Random(42)
    for _ in range(20):
        k = rng.randint(2, 7)
        levels = [rng.randint(1, 6) for _ in range(k)]
        for t in range(1, k + 1):
            expected = sum(prod(c) for c in combinations(levels, t))
            actual = count_possible_interactions(levels, t)
            assert actual == expected

    with pytest.raises(DesignError, match="non-negative"):
        count_possible_interactions([2, 2], -1)


def test_coverage_matches_brute_force_on_random_designs() -> None:
    rng = random.Random(101)
    for _ in range(10):
        d = random_design(rng, max_rows=10, max_cols=5, max_level=4)
        for t in range(1, d.num_columns + 1):
            result = coverage(d, t)
            brute_covered, brute_possible = brute_coverage(d, t)
            assert result.covered == brute_covered
            assert result.possible == brute_possible
            assert result.ratio == Fraction(brute_covered, brute_possible)
            assert result.is_complete == (brute_covered == brute_possible)


def test_complete_covering_array() -> None:
    # Full factorial 2 x 2
    d = Design([2, 2], [[0, 0], [0, 1], [1, 0], [1, 1]])
    res = coverage(d, 2)
    assert res.covered == 4
    assert res.possible == 4
    assert res.is_complete
    assert res.ratio == 1


def test_interaction_chi_square_matches_brute_force() -> None:
    rng = random.Random(202)
    for _ in range(10):
        d = random_design(rng, max_rows=8, max_cols=5, max_level=3)
        for t in range(1, d.num_columns + 1):
            for cols in combinations(range(d.num_columns), t):
                val = interaction_chi_square(d, cols)
                expected = brute_chi_square(d, cols)
                assert val == expected


def test_interaction_chi_square_validation() -> None:
    d = Design([2, 2], [[0, 0], [1, 1]])
    with pytest.raises(DesignError, match="at least one column"):
        interaction_chi_square(d, [])
    with pytest.raises(DesignError, match="distinct"):
        interaction_chi_square(d, [0, 0])
    with pytest.raises(DesignError, match="out of range"):
        interaction_chi_square(d, [0, 5])


def test_orthogonal_array_has_zero_chi_square() -> None:
    # OA(4, 3, 2, 2): 4 runs, 3 2-level factors, strength 2
    # Columns:
    # 0 0 0
    # 0 1 1
    # 1 0 1
    # 1 1 0
    oa = Design([2, 2, 2], [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]])
    res = chi_square(oa, 2)
    assert res.total == 0
    assert res.average == 0
    assert res.minimum == 0
    assert res.maximum == 0
    assert chi_square_efficiency(oa) == 1


def test_chi_square_lower_bound_and_efficiency_errors() -> None:
    d_1row = Design([2, 2], [[0, 0]])
    with pytest.raises(DesignError, match="at least 2 rows"):
        chi_square_lower_bound(d_1row)

    d_1col = Design([2], [[0], [1]])
    with pytest.raises(DesignError, match="at least 2 columns"):
        chi_square_efficiency(d_1col)


def test_efficiency_from_zero_total() -> None:
    assert efficiency_from(Fraction(0), Fraction(0)) == Fraction(1)


def test_pairwise_matrix_properties() -> None:
    d = Design([2, 3, 2], [[0, 0, 0], [1, 1, 1], [0, 2, 1], [1, 0, 0]])
    mat = pairwise_chi_square_matrix(d)
    k = d.num_columns
    assert len(mat) == k
    for i in range(k):
        assert mat[i][i] is None
        for j in range(k):
            if i != j:
                assert mat[i][j] == mat[j][i]


def test_report_generation() -> None:
    d = Design([2, 2, 2], [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]])
    rep = build_report(d, source="oa4.txt")
    assert rep.degree_of_saturation == Fraction(1, 1)
    assert not rep.is_supersaturated
    assert rep.pairwise_chi_square is not None
    assert rep.pairwise_chi_square.total == 0
    assert rep.chi_square_efficiency == 1

    d_dict = rep.to_dict()
    assert d_dict["rows"] == 4
    assert d_dict["columns"] == 3
    assert d_dict["chi_square"]["total"] == 0

    text = rep.format_text()
    assert "Design: oa4.txt" in text
    assert "Pairwise chi-square" in text

    # Report with 1 row design
    d1 = Design([2, 2], [[0, 0]])
    rep1 = build_report(d1)
    assert rep1.degree_of_saturation is None
    assert rep1.is_supersaturated is None
    assert rep1.chi_square_lower_bound is None
    assert rep1.chi_square_efficiency is None
    assert "Degree of saturation" not in rep1.format_text()
