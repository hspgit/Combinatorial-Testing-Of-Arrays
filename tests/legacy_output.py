"""Parsers for the golden output files written by the legacy C++ programs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from support import LEGACY_DIR

_NUM = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|inf|nan)"


def read(dataset: str, kind: str) -> str:
    return (LEGACY_DIR / f"{dataset}.{kind}.txt").read_text(encoding="utf-8")


def golden_exists(dataset: str, kind: str) -> bool:
    return (LEGACY_DIR / f"{dataset}.{kind}.txt").exists()


def number_after(label: str, text: str) -> float:
    match = re.search(re.escape(label) + r"\s*" + _NUM, text)
    if match is None:
        raise AssertionError(f"{label!r} not found in legacy output")
    return float(match.group(1))


@dataclass
class LegacyCoverage:
    possible: int
    covered: int
    ratio: float


def coverage(dataset: str, kind: str) -> LegacyCoverage:
    text = read(dataset, kind)
    ratio_label = "Coverage ratio =" if kind == "coverage_t2" else "Covering ratio ="
    return LegacyCoverage(
        possible=int(number_after("Total unique Combinations possible =", text)),
        covered=int(number_after("Total combinations covered =", text)),
        ratio=number_after(ratio_label, text),
    )


@dataclass
class LegacyPairwise:
    degree_of_saturation: float
    supersaturated: bool
    total: float
    frequency_table: list[tuple[float, int]]
    minimum: float
    maximum: float
    matrix: list[list[float]]


def pairwise(dataset: str) -> LegacyPairwise:
    """``new_chi_square_for_2_columns.cpp`` output (unrounded chi-square)."""
    text = read(dataset, "chi2_pairwise")
    lines = text.splitlines()
    table_start = lines.index("Chi_square\t|\tFrequency") + 1
    table: list[tuple[float, int]] = []
    for line in lines[table_start:]:
        if "|" not in line:
            break
        value, freq = line.split("|")
        table.append((float(value), int(freq)))
    matrix_start = lines.index("chi_square Array: ") + 1
    matrix = [[float(x) for x in line.split()] for line in lines[matrix_start:] if line.strip()]
    return LegacyPairwise(
        degree_of_saturation=number_after("Degree Of Saturation =", text),
        supersaturated="SUPER-SATURATED" in text,
        total=number_after("Chi_square value for t=2 is", text),
        frequency_table=table,
        minimum=number_after("Min chi_square_value in Design is", text),
        maximum=number_after("Max chi_square_value in Design is", text),
        matrix=matrix,
    )


@dataclass
class LegacyEfficiency:
    degree_of_saturation: float
    rounded_total: float
    efficiency: float


def efficiency(dataset: str) -> LegacyEfficiency:
    """``chi^2_efficiency.cpp`` output (chi-square terms rounded up)."""
    text = read(dataset, "chi2_efficiency")
    return LegacyEfficiency(
        degree_of_saturation=number_after("Degree Of Saturation =", text),
        rounded_total=number_after("Chi_square value for t=2 is", text),
        efficiency=number_after("Chi_square efficiency is =", text),
    )


@dataclass
class LegacyChiT:
    values: dict[tuple[int, ...], float]
    total: float


def chi_t(dataset: str, strength: int) -> LegacyChiT:
    """``chi_square_t_greater_than_2.cpp`` output (4 significant digits)."""
    text = read(dataset, f"chi2_t{strength}")
    values: dict[tuple[int, ...], float] = {}
    for match in re.finditer(r"^([a-z]+)\t-\t" + _NUM + r"$", text, flags=re.MULTILINE):
        columns = tuple(ord(ch) - ord("a") for ch in match.group(1))
        values[columns] = float(match.group(2))
    return LegacyChiT(
        values=values, total=number_after("Total chi-square-value of design is", text)
    )


def saturation(dataset: str) -> tuple[float, bool]:
    text = read(dataset, "saturation")
    return number_after("Degree Of Saturation =", text), "SUPER-SATURATED" in text
