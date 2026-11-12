"""Parity with the original C++ programs, using their captured golden output.

Tolerances reflect how the C++ printed each number:
* ``cout`` default: 6 significant digits      -> rel 5e-6
* ``fixed << setprecision(6)``: 6 decimals     -> abs 5e-7
* ``setprecision(4)`` (t-way chi-square tool): 4 significant digits -> rel 5e-4
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Any

import pytest

import legacy_output as legacy
from cit_tools import (
    Design,
    chi_square,
    chi_square_lower_bound,
    coverage,
    degree_of_saturation,
    load_design,
    pairwise_chi_square_matrix,
)
from support import design_path, parity_datasets

DATASETS = parity_datasets()


def approx_sig6(expected: float) -> Any:
    return pytest.approx(expected, rel=5.01e-6, abs=1e-12)


def approx_fixed6(expected: float) -> Any:
    return pytest.approx(expected, rel=0.0, abs=5.01e-7)


def approx_sig4(expected: float) -> Any:
    return pytest.approx(expected, rel=5.01e-4, abs=1e-12)


def test_golden_files_present() -> None:
    # 6 valid original samples + 3 generated designs; guards against a silently
    # empty parametrisation.
    assert len(DATASETS) == 9


@pytest.fixture(params=DATASETS)
def dataset(request: pytest.FixtureRequest) -> str:
    name: str = request.param
    return name


@pytest.fixture
def design(dataset: str) -> Design:
    return load_design(design_path(dataset))


def test_degree_of_saturation(dataset: str, design: Design) -> None:
    value, supersaturated = legacy.saturation(dataset)
    dos = degree_of_saturation(design)
    assert float(dos) == approx_sig6(value)
    assert (dos > 1) == supersaturated


def test_coverage_t2(dataset: str, design: Design) -> None:
    expected = legacy.coverage(dataset, "coverage_t2")
    result = coverage(design, 2)
    assert (result.covered, result.possible) == (expected.covered, expected.possible)
    assert float(result.ratio) == approx_sig6(expected.ratio)


@pytest.mark.parametrize("strength", [2, 3, 4])
def test_coverage_general(dataset: str, design: Design, strength: int) -> None:
    kind = f"coverage_t{strength}.general"
    if not legacy.golden_exists(dataset, kind):
        assert strength > design.num_columns
        pytest.skip(f"t={strength} exceeds the number of columns")
    expected = legacy.coverage(dataset, kind)
    result = coverage(design, strength)
    assert (result.covered, result.possible) == (expected.covered, expected.possible)
    assert float(result.ratio) == approx_sig6(expected.ratio)


def test_pairwise_chi_square(dataset: str, design: Design) -> None:
    expected = legacy.pairwise(dataset)
    result = chi_square(design, 2)

    assert float(degree_of_saturation(design)) == approx_sig6(expected.degree_of_saturation)
    assert float(result.total) == approx_sig6(expected.total)
    assert float(result.minimum) == approx_fixed6(expected.minimum)
    assert float(result.maximum) == approx_fixed6(expected.maximum)

    matrix = pairwise_chi_square_matrix(design)
    k = design.num_columns
    assert len(expected.matrix) == k
    for i in range(k):
        assert matrix[i][i] is None
        assert expected.matrix[i][i] == 0.0  # the C++ printed 0 on the diagonal
        for j in range(k):
            if i != j:
                assert float(matrix[i][j]) == approx_fixed6(expected.matrix[i][j])  # type: ignore[arg-type]


def test_pairwise_frequency_table(dataset: str, design: Design) -> None:
    # The C++ keyed its table by double, so floating-point noise can split one
    # exact value over several rows; merge those rows before comparing.
    ours = dict(chi_square(design, 2).frequency_table())
    merged: dict[Fraction, int] = dict.fromkeys(ours, 0)
    for value, freq in legacy.pairwise(dataset).frequency_table:
        matches = [v for v in ours if abs(float(v) - value) <= 5.01e-7]
        assert len(matches) == 1, f"legacy value {value} matches {matches}"
        merged[matches[0]] += freq
    assert merged == ours


def test_rounded_chi_square_efficiency(dataset: str, design: Design) -> None:
    """``chi^2_efficiency.cpp`` rounds every term *up* to 4 decimals.

    Its total must therefore exceed the exact total by no more than the
    accumulated rounding, and its efficiency must equal our exact lower bound
    divided by its (rounded) total.
    """
    expected = legacy.efficiency(dataset)
    exact_total = float(chi_square(design, 2).total)
    n = design.num_rows
    max_rounding = 0.0
    for i, j in combinations(range(design.num_columns), 2):
        cells = design.levels[i] * design.levels[j]
        # each of the `cells` terms gains < 1e-4, then is scaled by cells / n;
        # the pair's result is rounded up once more.
        max_rounding += cells * cells / n * 1e-4 + 1e-4
    printed_slack = 5.01e-6 * expected.rounded_total
    assert exact_total - printed_slack <= expected.rounded_total
    assert expected.rounded_total <= exact_total + max_rounding + printed_slack

    assert float(degree_of_saturation(design)) == approx_sig6(expected.degree_of_saturation)
    bound = float(chi_square_lower_bound(design))
    assert bound / expected.rounded_total == pytest.approx(expected.efficiency, rel=1.1e-5)


@pytest.mark.parametrize("strength", [2, 3, 4])
def test_chi_square_t_way(dataset: str, design: Design, strength: int) -> None:
    kind = f"chi2_t{strength}"
    if not legacy.golden_exists(dataset, kind):
        assert strength > design.num_columns
        pytest.skip(f"t={strength} exceeds the number of columns")
    expected = legacy.chi_t(dataset, strength)
    result = chi_square(design, strength)
    assert set(expected.values) == set(result.values)
    for columns, value in result.values.items():
        assert float(value) == approx_sig4(expected.values[columns])
    assert float(result.total) == approx_sig4(expected.total)
