"""Quality metrics for combinatorial test designs.

A *design* (covering array, orthogonal array, ...) is an ``N x k`` array whose
column ``j`` takes values ``0 .. levels[j] - 1``.  This package evaluates such
designs with:

* :func:`coverage` - fraction of all t-way value combinations that appear;
* :func:`chi_square` - chi-square (im)balance of every t-column projection;
* :func:`chi_square_efficiency` - pairwise chi-square relative to its lower bound;
* :func:`degree_of_saturation` - degrees of freedom relative to the run size.

Exact quantities are returned as :class:`fractions.Fraction`; call ``float()``
on them when a floating-point value is preferred.
"""

from cit_tools.design import Design, DesignError
from cit_tools.io import DesignFormatError, dump_design, load_design, parse_design
from cit_tools.metrics.chi_square import (
    ChiSquareResult,
    chi_square,
    chi_square_efficiency,
    chi_square_lower_bound,
    interaction_chi_square,
    pairwise_chi_square_matrix,
)
from cit_tools.metrics.coverage import CoverageResult, count_possible_interactions, coverage
from cit_tools.metrics.saturation import degree_of_saturation, is_supersaturated
from cit_tools.report import DesignReport, build_report

__version__ = "1.0.0"

__all__ = [
    "ChiSquareResult",
    "CoverageResult",
    "Design",
    "DesignError",
    "DesignFormatError",
    "DesignReport",
    "__version__",
    "build_report",
    "chi_square",
    "chi_square_efficiency",
    "chi_square_lower_bound",
    "count_possible_interactions",
    "coverage",
    "degree_of_saturation",
    "dump_design",
    "interaction_chi_square",
    "is_supersaturated",
    "load_design",
    "pairwise_chi_square_matrix",
    "parse_design",
]
