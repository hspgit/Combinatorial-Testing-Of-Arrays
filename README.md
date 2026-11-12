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
cit-tools coverage design.csv -t 2 3              # standard CSV with categorical strings
cit-tools coverage matrix.txt --levels 3 3 2      # raw matrix with explicit levels override
cit-tools chi-square design.tsv -t 3 --values     # TSV with combination values
cit-tools saturation design.txt --format json     # machine-readable output
cit-tools report design.txt -o report.txt         # write to a file
```

`python -m cit_tools ...` is equivalent. With `--format json`, one file gives
a JSON object and several files give an array. Exit status: 0 success,
1 invalid file / parameter, 2 usage error.

## Library

```python
from cit_tools import load_design, coverage, chi_square, chi_square_efficiency

# Load legacy files, raw numeric matrices, or CSV/TSV with categorical strings:
design = load_design("design.csv")
coverage(design, 2).ratio  # Fraction(...)
chi_square(design, 2).total  # Fraction(707, 1)
float(chi_square_efficiency(design))  # 0.898161...

# Override levels when some levels are unobserved in the test design:
design_explicit = load_design("matrix.txt", levels=[3, 4, 3])
```

Designs can also be built directly: `Design(levels=[2, 3], rows=[[0, 1], [1, 2]])`.
Exact quantities are returned as `fractions.Fraction`; use `float()` if needed.

## Input formats

`cit-tools` supports modern data formats out of the box with auto-detection,
while maintaining full backward compatibility with the legacy format:

### 1. Raw Numeric Matrices
Whitespace- or tab-separated rows of integers without upfront declarations:

```text
0 1 0
1 2 1
0 0 1
```

`N` (rows), `k` (columns), and factor levels (`max(val) + 1` per column) are
automatically inferred.

### 2. Standard Delimited Files (CSV / TSV)
Comma-, semicolon-, or tab-delimited files with optional headers and categorical
strings:

```csv
Browser,OS,Resolution
Chrome,Windows,1080p
Firefox,Linux,4k
Chrome,MacOS,1080p
```

Categorical strings are automatically mapped to zero-indexed integers in order of
appearance, and factor levels are inferred from distinct categories. Headers are
auto-detected (or controlled explicitly with `--header` / `--no-header`).

### 3. Overriding Inferred Levels (`--levels`)
When some factor levels are unobserved in the data (e.g. testing an incomplete
covering array), specify explicit levels using the `--levels` CLI flag or `levels`
parameter:

```bash
cit-tools coverage design.csv --levels 3 4 3
```

```python
design = load_design("design.csv", levels=[3, 4, 3])
```

### 4. Legacy Text Format
Preserved with full backward compatibility:

```text
N k                 # rows, columns
l1 l2 ... lk        # levels of each column
0 ... 0             # k + 1 reserved zeros
x11 x12 ... x1k     # N rows of k values, value j in 0 .. lj-1
...
```

The parser is strict and reports clear errors for malformed or out-of-range designs.

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
