# Combinatorial-Testing-Of-Arrays

Quality metrics for combinatorial test designs (covering arrays, orthogonal
arrays, supersaturated designs), packaged as the Python library and CLI
**`cit-tools`**.

| Metric | What it measures |
|---|---|
| **t-way coverage** | fraction of all t-way value combinations present in the design |
| **chi-square (t ≥ 1)** | imbalance of every t-column projection (0 = perfectly balanced) |
| **chi-square efficiency** | pairwise chi-square lower bound ÷ actual total (1 = optimal) |
| **degree of saturation** | `Σ(levels − 1) / (N − 1)`; > 1 means super-saturated |

This is a port of the original C++ programs, which are preserved unchanged in
[`old/`](old/). The port is verified against their output and against an
independent R reference (see [Verification](#verification)).

## Installation

Requires Python ≥ 3.10; no runtime dependencies.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"   # or: pip install .
```

## Command line

```bash
cit-tools report old/new_test.txt                 # every metric (like chi^2_efficiency.cpp)
cit-tools coverage old/*.txt -t 2 3               # t-way coverage, several files at once
cit-tools chi-square design.txt -t 3 --values     # per-combination chi-square values
cit-tools saturation design.txt --format json     # machine-readable output
cit-tools report design.txt -o report.txt         # write to a file
```

`python -m cit_tools ...` is equivalent. With `--format json`, one file gives
a JSON object and several files give an array. Exit status: 0 success,
1 invalid file / parameter, 2 usage error.

## Library

```python
from cit_tools import load_design, coverage, chi_square, chi_square_efficiency

design = load_design("old/new_test.txt")
coverage(design, 2).ratio  # Fraction(...)
chi_square(design, 2).total  # Fraction(707, 1)
float(chi_square_efficiency(design))  # 0.898161...
```

Designs can also be built directly: `Design(levels=[2, 3], rows=[[0, 1], [1, 2]])`.
Exact quantities are returned as `fractions.Fraction`; use `float()` if needed.

## Input format

Whitespace-separated integers (line breaks are not significant):

```text
N k                 # rows, columns
l1 l2 ... lk        # levels of each column
0 ... 0             # k + 1 reserved zeros
x11 x12 ... x1k     # N rows of k values, value j in 0 .. lj-1
...
```

The parser is strict and reports a clear error for files that do not match
their header, which the C++ tools silently mis-read.

## Changes from the C++ programs

| C++ behaviour | Python |
|---|---|
| Interactive `cin` prompts | Command-line arguments, batch processing, JSON output |
| `chi^2_efficiency.cpp` rounds every chi-square term **up** to 4 decimals (707.077 instead of 707 for `new_test.txt`) | Exact rational arithmetic |
| Frequency table keyed by `double`, so equal values could appear as separate rows | Exact values, grouped correctly |
| t-way coverage silently drops combinations containing a value ≥ 10 | Correct for any number of levels |
| `1 << n` bit mask overflows for 31+ columns | `itertools.combinations` |
| Out-of-range values and header mismatches are accepted and produce wrong numbers | Rejected with an error message |
| Needs GCC (`<bits/stdc++.h>`) | Pure Python |

### Issues found in the original sample files

- `old/test2.txt`: the header says `5 4` but the data has 5 columns.
- `old/test4.txt`, `old/test5.txt`: columns declared with 2 levels contain the value 2.

The C++ tools report numbers for these files anyway (e.g. coverage 359/400 for
`test4.txt`, which counts combinations that cannot exist), so they are left
out of the parity tests, and `cit-tools` rejects them.

## Verification

- **C++ parity**: `scripts/capture_legacy_outputs.sh` compiles the original,
  unmodified C++ and records its output in `tests/fixtures/legacy/` for the
  valid samples and three seeded random designs
  (`scripts/generate_random_designs.py`). `tests/test_legacy_parity.py`
  checks every number against them.
- **Independent reference**: `old/13mixed2l3l.txt` is the output of an R
  implementation for the design in `old/new_test.txt`. The port reproduces it
  exactly (sum 707, lower bound 635, efficiency 0.898161, the full frequency
  table and all 325 pairwise values).
- **Math checks**: closed forms are checked against brute-force definitions on
  random designs.

## Development

```bash
.venv/bin/pytest --cov          # tests + coverage
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy                  # strict type checking
scripts/capture_legacy_outputs.sh   # regenerate C++ golden files (needs a C++ compiler)
```

CI runs all of the above on Python 3.10–3.13 (`.github/workflows/ci.yml`).

## Layout

```text
src/cit_tools/      library: design.py, io.py, metrics/, report.py, cli.py
tests/              pytest suite and fixtures (golden C++ outputs, random designs)
scripts/            golden-file capture and random-design generation
old/                original C++ sources and sample data, unchanged
```
