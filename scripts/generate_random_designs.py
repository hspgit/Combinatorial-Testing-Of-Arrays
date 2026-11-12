#!/usr/bin/env python3
"""Generate the seeded random designs in tests/fixtures/designs/.

They supplement the original samples for the C++ parity tests (two of the
original samples, test4.txt and test5.txt, contain out-of-range values and
cannot be used).  Levels are kept <= 9 because the C++ t-way tools mishandle
values >= 10.  Deterministic: re-running produces identical files.

Usage: python3 scripts/generate_random_designs.py
"""

from __future__ import annotations

import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "designs"

# name: (seed, rows, levels)
SPECS: dict[str, tuple[int, int, list[int]]] = {
    "random_mixed": (1, 30, [2, 3, 4, 5, 6, 2, 3, 4]),
    "random_wide": (2, 50, [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]),
    # fewer rows than some level counts, plus a single-level column
    "random_edge": (3, 4, [6, 2, 1, 3, 5]),
}


def dump(rows: list[list[int]], levels: list[int]) -> str:
    lines = [f"{len(rows)} {len(levels)}", " ".join(map(str, levels))]
    lines += ["0"] * (len(levels) + 1)
    lines += [" ".join(map(str, row)) for row in rows]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (seed, n, levels) in SPECS.items():
        rng = random.Random(seed)
        rows = [[rng.randrange(level) for level in levels] for _ in range(n)]
        (OUT / f"{name}.txt").write_text(dump(rows, levels), encoding="utf-8")
        print(f"wrote {name}.txt ({n} x {len(levels)})")


if __name__ == "__main__":
    main()
