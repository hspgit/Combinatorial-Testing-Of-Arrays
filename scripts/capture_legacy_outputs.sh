#!/usr/bin/env bash
# Compile the archived C++ tools in old/ (sources are NOT modified) and record
# their outputs on every valid sample design. The results are committed under
# tests/fixtures/legacy/ and act as golden files for the Python parity tests.
#
# Usage: scripts/capture_legacy_outputs.sh
# Requires: a C++17 compiler (c++ / g++ / clang++).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OLD="$ROOT/old"
BUILD="$ROOT/build/legacy"
OUT="$ROOT/tests/fixtures/legacy"
CXX="${CXX:-c++}"

# Valid original samples (old/) plus seeded random designs
# (tests/fixtures/designs/, see scripts/generate_random_designs.py).
# Excluded on purpose, because the C++ tools silently mis-read them:
#   test2.txt        header declares 4 columns but the data has 5
#   test4/test5.txt  contain the value 2 in columns declared as 2-level
OLD_DATASETS=(test1 test3 test6 test7 new_test LA_SMALL)
GENERATED="$ROOT/tests/fixtures/designs"
T_VALUES=(2 3 4)

mkdir -p "$BUILD/include/bits" "$OUT"

# <bits/stdc++.h> is a GCC-only convenience header; provide a portable shim so
# the unmodified sources also build with Clang / Apple toolchains.
cat > "$BUILD/include/bits/stdc++.h" <<'EOF'
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
EOF

build() { # <source-file> <binary-name>
    "$CXX" -std=c++17 -O2 -I "$BUILD/include" "$OLD/$1" -o "$BUILD/$2"
}
build "degree_of_saturation.cpp"          degree_of_saturation
build "coverage_ratio_for_2_columns.cpp"  coverage_t2
build "coverage_for_t_greater_than_2.cpp" coverage_t
build "chi^2_efficiency.cpp"              chi2_efficiency
build "new_chi_square_for_2_columns.cpp"  chi2_pairwise
build "chi_square_t_greater_than_2.cpp"   chi2_t

# The sample files use CRLF line endings, so strip '\r' before reading the header.
columns_of() { tr -d '\r' < "$1" | awk 'NR==1 {print $2; exit}'; }

capture() { # <directory> <dataset-name>
    # The tools open the data file relative to the working directory.
    cd "$1"
    local ds="$2" f="$2.txt" cols
    cols="$(columns_of "$f")"
    echo "capturing $ds ($cols columns)"

    printf '%s\n' "$f"         | "$BUILD/degree_of_saturation" > "$OUT/$ds.saturation.txt"
    printf '%s\n' "$f"         | "$BUILD/coverage_t2"          > "$OUT/$ds.coverage_t2.txt"
    printf '%s\n%s\n' "$f" "$OUT/$ds.chi2_efficiency.txt" | "$BUILD/chi2_efficiency" > /dev/null
    printf '%s\n%s\nN\n' "$f" "$OUT/$ds.chi2_pairwise.txt" | "$BUILD/chi2_pairwise" > /dev/null

    for t in "${T_VALUES[@]}"; do
        if (( t <= cols )); then
            printf '%s\n%s\n' "$f" "$t" | "$BUILD/coverage_t" > "$OUT/$ds.coverage_t$t.general.txt"
            printf '%s\n%s\n' "$f" "$t" | "$BUILD/chi2_t"     > "$OUT/$ds.chi2_t$t.txt"
        fi
    done
}

rm -f "$OUT"/*.txt
for ds in "${OLD_DATASETS[@]}"; do capture "$OLD" "$ds"; done
for path in "$GENERATED"/*.txt; do capture "$GENERATED" "$(basename "$path" .txt)"; done
echo "golden files written to $OUT"
