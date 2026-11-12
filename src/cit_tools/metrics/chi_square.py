"""Chi-square balance metrics.

Port of ``chi^2_efficiency.cpp``, ``new_chi_square_for_2_columns.cpp`` and
``chi_square_t_greater_than_2.cpp``.

For a set ``C`` of columns with ``L = prod(levels[c] for c in C)`` cells, a
perfectly balanced design puts ``e = N / L`` runs in every cell.  The
chi-square statistic of the projection is::

    chi2(C) = sum over all L cells of (n_cell - e)^2 / e  =  (L * sum(n_cell^2) - N^2) / N

where empty cells count with ``n_cell = 0``.  All values are computed exactly as
:class:`~fractions.Fraction`.  (``chi^2_efficiency.cpp`` rounded every term up
to 4 decimals, which inflated its totals, e.g. 707.077 instead of the exact
707 for ``new_test.txt``.)
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import prod
from operator import itemgetter

from cit_tools.design import Design, DesignError

__all__ = [
    "ChiSquareResult",
    "chi_square",
    "chi_square_efficiency",
    "chi_square_lower_bound",
    "efficiency_from",
    "interaction_chi_square",
    "pairwise_chi_square_matrix",
]


def interaction_chi_square(design: Design, columns: Sequence[int]) -> Fraction:
    """Chi-square statistic of the projection of ``design`` onto ``columns``."""
    cols = tuple(columns)
    if not cols:
        raise DesignError("at least one column is required")
    if len(set(cols)) != len(cols):
        raise DesignError(f"columns must be distinct, got {cols}")
    for c in cols:
        if not 0 <= c < design.num_columns:
            raise DesignError(f"column index {c} out of range 0..{design.num_columns - 1}")
    project = itemgetter(*cols)
    counts = Counter(project(row) for row in design.rows)
    cells = prod(design.levels[c] for c in cols)
    n = design.num_rows
    return Fraction(cells * sum(m * m for m in counts.values()) - n * n, n)


@dataclass(frozen=True, slots=True)
class ChiSquareResult:
    """Outcome of :func:`chi_square`.

    Attributes:
        strength: the interaction strength t.
        values: chi-square of every t-column combination, keyed by the sorted
            tuple of column indices, in lexicographic order.
    """

    strength: int
    values: Mapping[tuple[int, ...], Fraction]

    @property
    def total(self) -> Fraction:
        """Sum of the chi-square values over all column combinations."""
        return sum(self.values.values(), Fraction(0))

    @property
    def average(self) -> Fraction:
        """Mean chi-square value per column combination."""
        return self.total / len(self.values)

    @property
    def minimum(self) -> Fraction:
        """Smallest chi-square value."""
        return min(self.values.values())

    @property
    def maximum(self) -> Fraction:
        """Largest chi-square value."""
        return max(self.values.values())

    def frequency_table(self) -> list[tuple[Fraction, int]]:
        """Distinct chi-square values with how often each occurs, ascending."""
        return sorted(Counter(self.values.values()).items())


def chi_square(design: Design, strength: int = 2) -> ChiSquareResult:
    """Chi-square statistic of every ``strength``-column projection."""
    design.check_strength(strength)
    values = {
        cols: interaction_chi_square(design, cols)
        for cols in combinations(range(design.num_columns), strength)
    }
    return ChiSquareResult(strength=strength, values=values)


def pairwise_chi_square_matrix(design: Design) -> list[list[Fraction | None]]:
    """Symmetric ``k x k`` matrix of pairwise chi-square values.

    The diagonal is ``None`` (a column paired with itself is not an interaction;
    the C++ tools printed 0 there).
    """
    k = design.num_columns
    matrix: list[list[Fraction | None]] = [[None] * k for _ in range(k)]
    if k >= 2:
        for (i, j), value in chi_square(design, 2).values.items():
            matrix[i][j] = matrix[j][i] = value
    return matrix


def chi_square_lower_bound(design: Design) -> Fraction:
    """Lower bound on the total pairwise chi-square of a design of this shape.

    Depends only on ``N`` and the level counts (exact port of the bound in
    ``chi^2_efficiency.cpp``; it matches the "Lower bound for Sum.chi.sqr
    near-balanced design" reported by the R reference ``13mixed2l3l.txt``).

    With ``k_j = N // l_j`` and ``r_j = N mod l_j``::

        S   = sum_j l_j * k_j * (N - l_j + r_j)
        u1  = floor(S / (N (N - 1))),  u2 = u1 + 1
        Nu1 = N (N - 1) u2 - S,        Nu2 = S - N (N - 1) u1
        C   = (sum_j l_j)^2 / 2 - N m (m - 1) / 2
              - sum_j l_j^2 (l_j k_j^2 + 2 r_j k_j + r_j) / (2 N)
        bound = C + (Nu1 u1^2 + Nu2 u2^2) / (2 N)

    where ``m`` is the number of columns.

    Raises:
        DesignError: if the design has fewer than 2 rows.
    """
    n = design.num_rows
    m = design.num_columns
    if n < 2:
        raise DesignError("the chi-square lower bound needs at least 2 rows")
    levels = design.levels
    ks = [n // level for level in levels]
    rs = [n - k * level for k, level in zip(ks, levels, strict=True)]

    pairs = n * (n - 1)
    s = sum(level * k * (n - level + r) for level, k, r in zip(levels, ks, rs, strict=True))
    u1 = s // pairs
    u2 = u1 + 1
    nu1 = pairs * u2 - s
    nu2 = s - pairs * u1

    c = Fraction(sum(levels) ** 2, 2) - Fraction(n * m * (m - 1), 2)
    c -= Fraction(
        sum(
            level * level * (level * k * k + 2 * r * k + r)
            for level, k, r in zip(levels, ks, rs, strict=True)
        ),
        2 * n,
    )
    return c + Fraction(nu1 * u1 * u1 + nu2 * u2 * u2, 2 * n)


def chi_square_efficiency(design: Design) -> Fraction:
    """Pairwise chi-square efficiency: lower bound / actual total (1 is optimal).

    A design whose every pair of columns is perfectly balanced has total
    chi-square 0; its efficiency is defined as 1.

    Raises:
        DesignError: if the design has fewer than 2 rows or 2 columns.
    """
    if design.num_columns < 2:
        raise DesignError("chi-square efficiency needs at least 2 columns")
    return efficiency_from(chi_square_lower_bound(design), chi_square(design, 2).total)


def efficiency_from(lower_bound: Fraction, total: Fraction) -> Fraction:
    """``lower_bound / total``, defined as 1 when ``total`` is 0."""
    if total == 0:
        return Fraction(1)
    return lower_bound / total
