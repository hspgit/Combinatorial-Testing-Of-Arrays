"""Full design report (the modern equivalent of ``chi^2_efficiency.cpp``)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from cit_tools._format import fmt, to_json_number
from cit_tools.design import Design, column_label, interaction_label
from cit_tools.metrics.chi_square import (
    ChiSquareResult,
    chi_square,
    chi_square_lower_bound,
    efficiency_from,
    pairwise_chi_square_matrix,
)
from cit_tools.metrics.coverage import CoverageResult, coverage
from cit_tools.metrics.saturation import degree_of_saturation

__all__ = ["DesignReport", "build_report"]

DEFAULT_COVERAGE_STRENGTHS = (2, 3)


@dataclass(frozen=True, slots=True)
class DesignReport:
    """All metrics of one design.

    Metrics that are undefined for the design's shape are ``None``: degree of
    saturation, the lower bound and efficiency need ``N >= 2``; the pairwise
    chi-square metrics need ``k >= 2``.
    """

    design: Design
    source: str | None
    degree_of_saturation: Fraction | None
    coverage: tuple[CoverageResult, ...]
    pairwise_chi_square: ChiSquareResult | None
    chi_square_lower_bound: Fraction | None
    chi_square_efficiency: Fraction | None

    @property
    def is_supersaturated(self) -> bool | None:
        """``True`` if the degree of saturation exceeds 1 (``None`` if undefined)."""
        dos = self.degree_of_saturation
        return None if dos is None else dos > 1

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation."""
        chi = self.pairwise_chi_square
        return {
            "source": self.source,
            "rows": self.design.num_rows,
            "columns": self.design.num_columns,
            "levels": list(self.design.levels),
            "degree_of_saturation": to_json_number(self.degree_of_saturation),
            "supersaturated": self.is_supersaturated,
            "coverage": [
                {
                    "strength": c.strength,
                    "covered": c.covered,
                    "possible": c.possible,
                    "ratio": to_json_number(c.ratio),
                }
                for c in self.coverage
            ],
            "chi_square": None
            if chi is None
            else {
                "strength": 2,
                "total": to_json_number(chi.total),
                "average": to_json_number(chi.average),
                "min": to_json_number(chi.minimum),
                "max": to_json_number(chi.maximum),
                "lower_bound": to_json_number(self.chi_square_lower_bound),
                "efficiency": to_json_number(self.chi_square_efficiency),
                "frequency_table": [
                    {"value": to_json_number(v), "frequency": n} for v, n in chi.frequency_table()
                ],
                "values": {
                    interaction_label(cols): to_json_number(v) for cols, v in chi.values.items()
                },
            },
        }

    def format_text(self) -> str:
        """Human-readable multi-section report."""
        d = self.design
        out: list[str] = []
        out.append(f"Design: {self.source or '<in-memory>'}")
        out.append(f"  runs (N): {d.num_rows}   columns (k): {d.num_columns}")
        out.append(f"  levels: {' '.join(map(str, d.levels))}")
        out.append("")

        if self.degree_of_saturation is not None:
            kind = "super-saturated" if self.is_supersaturated else "not super-saturated"
            out.append(f"Degree of saturation: {fmt(self.degree_of_saturation)} ({kind})")
            out.append("")

        if self.coverage:
            out.append("Coverage")
            for c in self.coverage:
                out.append(f"  t={c.strength}: {c.covered} / {c.possible} = {fmt(c.ratio)}")
            out.append("")

        chi = self.pairwise_chi_square
        if chi is not None:
            out.append("Pairwise chi-square (t=2)")
            out.append(
                f"  total: {fmt(chi.total)}   average: {fmt(chi.average)}   "
                f"min: {fmt(chi.minimum)}   max: {fmt(chi.maximum)}"
            )
            if self.chi_square_lower_bound is not None:
                out.append(
                    f"  lower bound: {fmt(self.chi_square_lower_bound)}   "
                    f"efficiency: {fmt(self.chi_square_efficiency)}"
                )
            out.append("")
            out.append("  Frequency table")
            table = [(fmt(v), str(n)) for v, n in chi.frequency_table()]
            out.extend(_table(["chi-square", "frequency"], table, indent=4))
            out.append("")
            out.append("  Matrix")
            labels = [column_label(j) for j in range(d.num_columns)]
            matrix = pairwise_chi_square_matrix(d)
            rows = [[labels[i], *(fmt(v) for v in matrix[i])] for i in range(d.num_columns)]
            out.extend(_table(["", *labels], rows, indent=4))
        return "\n".join(out).rstrip() + "\n"


def _table(header: list[str], rows: Sequence[Sequence[str]], indent: int) -> list[str]:
    widths = [max(len(r[i]) for r in [header, *rows]) for i in range(len(header))]
    pad = " " * indent
    return [
        pad + "  ".join(cell.ljust(w) for cell, w in zip(r, widths, strict=True)).rstrip()
        for r in [header, *rows]
    ]


def build_report(
    design: Design,
    *,
    source: str | None = None,
    coverage_strengths: Sequence[int] | None = None,
) -> DesignReport:
    """Compute every metric for ``design``.

    Args:
        design: the design to evaluate.
        source: optional name (e.g. file path) to include in the report.
        coverage_strengths: strengths t for which to report coverage.  Defaults
            to 2 and 3, restricted to those not exceeding the number of columns.
    """
    if coverage_strengths is None:
        coverage_strengths = [t for t in DEFAULT_COVERAGE_STRENGTHS if t <= design.num_columns]
    enough_rows = design.num_rows >= 2
    enough_cols = design.num_columns >= 2

    chi = chi_square(design, 2) if enough_cols else None
    bound = chi_square_lower_bound(design) if enough_rows and enough_cols else None
    efficiency = None if chi is None or bound is None else efficiency_from(bound, chi.total)

    return DesignReport(
        design=design,
        source=source,
        degree_of_saturation=degree_of_saturation(design) if enough_rows else None,
        coverage=tuple(coverage(design, t) for t in coverage_strengths),
        pairwise_chi_square=chi,
        chi_square_lower_bound=bound,
        chi_square_efficiency=efficiency,
    )
