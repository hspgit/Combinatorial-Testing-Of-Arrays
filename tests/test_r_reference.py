"""Comparison with an independent R implementation.

``old/13mixed2l3l.txt`` is R output for the 13-run design with 13 two-level
factors (A-M) and 13 three-level factors (a-m) stored in ``old/new_test.txt``
(columns 0-12 and 13-25 respectively).
"""

from __future__ import annotations

import re
from fractions import Fraction

import pytest

from cit_tools import (
    Design,
    chi_square,
    chi_square_efficiency,
    chi_square_lower_bound,
    degree_of_saturation,
    load_design,
)
from support import OLD_DIR

REFERENCE = (OLD_DIR / "13mixed2l3l.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def design() -> Design:
    return load_design(OLD_DIR / "new_test.txt")


def reference_value(label: str) -> float:
    match = re.search(re.escape(label) + r"\s*=\s*([-+0-9.eE]+)", REFERENCE)
    assert match is not None, label
    return float(match.group(1))


def r_column(name: str) -> int:
    """R names: A-M are columns 0-12, a-m are columns 13-25."""
    return ord(name) - ord("A") if name.isupper() else 13 + ord(name) - ord("a")


def test_design_shape(design: Design) -> None:
    assert design.num_rows == reference_value("number of runs") == 13
    assert design.levels == (2,) * 13 + (3,) * 13


def test_summary_statistics(design: Design) -> None:
    result = chi_square(design, 2)
    assert degree_of_saturation(design) == Fraction(13, 4)
    assert reference_value("degree of saturation") == 3.25
    assert chi_square_lower_bound(design) == 635
    assert reference_value("Lower bound for Sum.chi.sqr near-balanced design") == 635
    assert result.total == 707
    assert reference_value("Sum.chi.sqr") == 707
    assert float(result.average) == pytest.approx(reference_value("Avg.chi.sqr"), abs=5e-7)
    assert float(result.maximum) == pytest.approx(reference_value("Max.chi.sqr"), abs=5e-7)
    # R printed 0.8981610; the exact value is 635/707 = 0.89816124...
    assert chi_square_efficiency(design) == Fraction(635, 707)
    assert float(chi_square_efficiency(design)) == pytest.approx(
        reference_value("chi.sqr efficiency"), abs=5e-7
    )
    # "Lower bound for Avg.chi.sqr" = bound / number of pairs
    assert float(chi_square_lower_bound(design) / len(result.values)) == pytest.approx(
        reference_value("Lower bound for Avg.chi.sqr balanced design"), abs=5e-7
    )


def test_frequency_table(design: Design) -> None:
    section = REFERENCE.split("chi.sqr summary table =")[1].split("=====")[0]
    rows = re.findall(r"^\s*\d+\s+([0-9.]+)\s+(\d+)\s*$", section, flags=re.MULTILINE)
    assert len(rows) == 10
    ours = chi_square(design, 2).frequency_table()
    assert [n for _, n in ours] == [int(freq) for _, freq in rows]
    for (value, _), (ref_value, _) in zip(ours, rows, strict=True):
        assert float(value) == pytest.approx(float(ref_value), abs=1e-12)


def test_every_pairwise_value(design: Design) -> None:
    section = re.split(r"\nchi\.sqr\s*=\s*\n", REFERENCE)[1].split("=====")[0]
    lines = [line for line in section.splitlines() if line.strip()]
    reference: dict[tuple[int, ...], float] = {}
    for header, values in zip(lines[::2], lines[1::2], strict=True):
        labels = header.split()
        numbers = values.split()
        assert numbers[0] == "1"
        assert len(labels) == len(numbers) - 1
        for label, number in zip(labels, numbers[1:], strict=True):
            a, b = label.split("*")
            i, j = sorted((r_column(a), r_column(b)))
            reference[(i, j)] = float(number)

    ours = chi_square(design, 2).values
    assert len(reference) == len(ours) == 325
    for pair, value in ours.items():
        # R printed 7 significant digits
        assert float(value) == pytest.approx(reference[pair], rel=5.01e-7)
