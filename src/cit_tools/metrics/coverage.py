"""t-way combination coverage.

Port of ``coverage_ratio_for_2_columns.cpp`` (t = 2) and
``coverage_for_t_greater_than_2.cpp`` (any t).  Fixes two defects of the latter:
combinations containing a value >= 10 were silently dropped, and designs with
31+ columns overflowed a ``1 << n`` bit mask.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from operator import itemgetter

from cit_tools.design import Design, DesignError

__all__ = ["CoverageResult", "count_possible_interactions", "coverage"]


@dataclass(frozen=True, slots=True)
class CoverageResult:
    """Outcome of :func:`coverage`.

    Attributes:
        strength: the interaction strength t.
        covered: number of distinct t-way (columns, values) combinations present.
        possible: number of t-way combinations that could exist.
    """

    strength: int
    covered: int
    possible: int

    @property
    def ratio(self) -> Fraction:
        """``covered / possible``; 1 means the design is a strength-t covering array."""
        return Fraction(self.covered, self.possible)

    @property
    def is_complete(self) -> bool:
        """``True`` if every t-way combination is covered."""
        return self.covered == self.possible


def count_possible_interactions(levels: tuple[int, ...] | list[int], strength: int) -> int:
    """Number of t-way value combinations over all t-column subsets.

    This is the elementary symmetric polynomial ``e_t(levels)``, i.e. the sum,
    over every set of t columns, of the product of their level counts.  It is
    computed in ``O(k * t)`` rather than by enumerating subsets.
    """
    if strength < 0:
        raise DesignError(f"strength must be non-negative, got {strength}")
    e = [1] + [0] * strength
    for level in levels:
        for t in range(strength, 0, -1):
            e[t] += e[t - 1] * level
    return e[strength]


def coverage(design: Design, strength: int = 2) -> CoverageResult:
    """Fraction of all t-way value combinations that appear in the design.

    For every set of ``strength`` columns, count the distinct value tuples that
    occur in some row; the sum over all column sets is ``covered``.
    """
    design.check_strength(strength)
    covered = 0
    for columns in combinations(range(design.num_columns), strength):
        project = itemgetter(*columns)
        covered += len({project(row) for row in design.rows})
    return CoverageResult(
        strength=strength,
        covered=covered,
        possible=count_possible_interactions(design.levels, strength),
    )
