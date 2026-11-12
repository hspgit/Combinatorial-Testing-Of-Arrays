"""Design quality metrics."""

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

__all__ = [
    "ChiSquareResult",
    "CoverageResult",
    "chi_square",
    "chi_square_efficiency",
    "chi_square_lower_bound",
    "count_possible_interactions",
    "coverage",
    "degree_of_saturation",
    "interaction_chi_square",
    "is_supersaturated",
    "pairwise_chi_square_matrix",
]
