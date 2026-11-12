"""Number formatting shared by the report and the CLI."""

from __future__ import annotations

from fractions import Fraction

__all__ = ["fmt", "to_json_number"]


def fmt(value: Fraction | int | None, digits: int = 6) -> str:
    """Integers exactly, everything else with ``digits`` significant digits."""
    if value is None:
        return "-"
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.{digits}g}"


def to_json_number(value: Fraction | int | None) -> int | float | None:
    """Integers as ``int``, other fractions as ``float``, ``None`` unchanged."""
    if value is None:
        return None
    value = Fraction(value)
    if value.denominator == 1:
        return value.numerator
    return float(value)
