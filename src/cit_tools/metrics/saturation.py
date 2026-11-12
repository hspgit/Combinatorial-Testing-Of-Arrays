"""Degree of saturation (port of ``degree_of_saturation.cpp``)."""

from __future__ import annotations

from fractions import Fraction

from cit_tools.design import Design, DesignError

__all__ = ["degree_of_saturation", "is_supersaturated"]


def degree_of_saturation(design: Design) -> Fraction:
    """Degrees of freedom of the factors relative to those of the runs.

    ``DoS = sum_j (levels[j] - 1) / (N - 1)``.  A design with ``DoS > 1`` is
    *super-saturated*: it has more factor degrees of freedom than runs can
    estimate.

    Raises:
        DesignError: if the design has a single row (``N - 1 == 0``).
    """
    if design.num_rows < 2:
        raise DesignError("degree of saturation needs at least 2 rows")
    return Fraction(sum(level - 1 for level in design.levels), design.num_rows - 1)


def is_supersaturated(design: Design) -> bool:
    """``True`` when :func:`degree_of_saturation` exceeds 1."""
    return degree_of_saturation(design) > 1
