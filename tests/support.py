"""Shared helpers for the test suite."""

from __future__ import annotations

import random
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
from math import prod
from pathlib import Path

from cit_tools import Design

ROOT = Path(__file__).resolve().parent.parent
OLD_DIR = ROOT / "old"
LEGACY_DIR = ROOT / "tests" / "fixtures" / "legacy"
DESIGNS_DIR = ROOT / "tests" / "fixtures" / "designs"


def design_path(name: str) -> Path:
    """Path of a parity dataset: an original sample or a generated design."""
    for directory in (OLD_DIR, DESIGNS_DIR):
        path = directory / f"{name}.txt"
        if path.exists():
            return path
    raise FileNotFoundError(name)


def parity_datasets() -> list[str]:
    """Every dataset for which golden C++ output was captured."""
    return sorted(
        p.name.removesuffix(".saturation.txt") for p in LEGACY_DIR.glob("*.saturation.txt")
    )


def random_design(
    rng: random.Random, max_rows: int = 15, max_cols: int = 6, max_level: int = 12
) -> Design:
    """A random valid design (levels may exceed 9 on purpose)."""
    levels = [rng.randint(1, max_level) for _ in range(rng.randint(1, max_cols))]
    rows = [[rng.randrange(level) for level in levels] for _ in range(rng.randint(1, max_rows))]
    return Design(levels, rows)


# --- brute-force reference implementations, straight from the definitions ---


def brute_chi_square(design: Design, columns: tuple[int, ...]) -> Fraction:
    """sum over all cells of (observed - expected)^2 / expected."""
    n = design.num_rows
    cells = prod(design.levels[c] for c in columns)
    expected = Fraction(n, cells)
    observed = Counter(tuple(row[c] for c in columns) for row in design.rows)
    total = Fraction(0)
    for cell in product(*(range(design.levels[c]) for c in columns)):
        total += (observed[cell] - expected) ** 2 / expected
    return total


def brute_coverage(design: Design, strength: int) -> tuple[int, int]:
    """(covered, possible) by enumerating every possible value combination."""
    covered = possible = 0
    for columns in combinations(range(design.num_columns), strength):
        for cell in product(*(range(design.levels[c]) for c in columns)):
            possible += 1
            covered += any(tuple(row[c] for c in columns) == cell for row in design.rows)
    return covered, possible
