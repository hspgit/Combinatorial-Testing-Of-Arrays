"""Unit tests for the cit-tools CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cit_tools.cli import main
from support import OLD_DIR


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "cit-tools" in capsys.readouterr().out


def test_cli_saturation(capsys: pytest.CaptureFixture[str]) -> None:
    file_path = str(OLD_DIR / "test1.txt")
    code = main(["saturation", file_path])
    assert code == 0
    out = capsys.readouterr().out
    assert "degree of saturation = 1.33333" in out
    assert "super-saturated" in out

    # JSON format
    code_json = main(["saturation", file_path, "--format", "json"])
    assert code_json == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == file_path
    assert data["supersaturated"] is True


def test_cli_coverage(capsys: pytest.CaptureFixture[str]) -> None:
    file_path = str(OLD_DIR / "test1.txt")
    code = main(["coverage", file_path, "-t", "2", "3"])
    assert code == 0
    out = capsys.readouterr().out
    assert "t=2: 10 / 16 covered" in out
    assert "t=3: 4 / 12 covered" in out

    # JSON format
    code_json = main(["coverage", file_path, "-t", "2", "--format", "json"])
    assert code_json == 0
    data = json.loads(capsys.readouterr().out)
    assert data["coverage"][0]["covered"] == 10
    assert data["coverage"][0]["possible"] == 16


def test_cli_chi_square(capsys: pytest.CaptureFixture[str]) -> None:
    file_path = str(OLD_DIR / "test1.txt")
    code = main(["chi-square", file_path, "-t", "2", "--values"])
    assert code == 0
    out = capsys.readouterr().out
    assert "total 9" in out
    assert "a*b" in out

    # JSON format
    code_json = main(["chi-square", file_path, "-t", "2", "--format", "json"])
    assert code_json == 0
    data = json.loads(capsys.readouterr().out)
    assert data["chi_square"][0]["total"] == 9


def test_cli_report_and_output_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    file_path = str(OLD_DIR / "test1.txt")
    out_file = tmp_path / "report.txt"
    code = main(["report", file_path, "-o", str(out_file)])
    assert code == 0
    assert capsys.readouterr().out == ""
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Degree of saturation: 1.33333" in content
    assert "Pairwise chi-square" in content


def test_cli_multiple_files_json(capsys: pytest.CaptureFixture[str]) -> None:
    f1 = str(OLD_DIR / "test1.txt")
    f3 = str(OLD_DIR / "test3.txt")
    code = main(["saturation", f1, f3, "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["source"] == f1
    assert data[1]["source"] == f3


def test_cli_error_handling(capsys: pytest.CaptureFixture[str]) -> None:
    # Non-existent file
    code = main(["saturation", "non_existent_file.txt"])
    assert code == 1
    err = capsys.readouterr().err
    assert "No such file" in err

    # Corrupted design file
    code_corrupt = main(["saturation", str(OLD_DIR / "test2.txt")])
    assert code_corrupt == 1
    assert "error:" in capsys.readouterr().err

    # Invalid strength
    with pytest.raises(SystemExit):
        main(["coverage", str(OLD_DIR / "test1.txt"), "-t", "0"])


def test_cli_raw_numeric_matrix(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("0 1 0\n1 2 1\n0 0 1\n", encoding="utf-8")

    code = main(["coverage", str(matrix_file), "-t", "2"])
    assert code == 0
    out = capsys.readouterr().out
    assert "N=3, k=3" in out
    assert "t=2:" in out


def test_cli_csv_and_explicit_levels(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "Browser,OS,Resolution\nChrome,Windows,1080p\nFirefox,Linux,4k\nChrome,MacOS,1080p\n",
        encoding="utf-8",
    )

    # Inferred levels
    code = main(["coverage", str(csv_file), "-t", "2"])
    assert code == 0
    out = capsys.readouterr().out
    assert "N=3, k=3" in out

    # Explicit --levels with spaces
    code_levels = main(["coverage", str(csv_file), "-t", "2", "--levels", "3", "4", "3"])
    assert code_levels == 0
    out_levels = capsys.readouterr().out
    assert "N=3, k=3" in out_levels

    # Explicit --levels with commas
    code_commas = main(["coverage", str(csv_file), "-t", "2", "--levels", "3,4,3"])
    assert code_commas == 0


def test_cli_header_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("0,1,0\n1,2,1\n", encoding="utf-8")

    # Explicit --no-header
    code = main(["saturation", str(csv_file), "--no-header"])
    assert code == 0
    out = capsys.readouterr().out
    assert "degree of saturation" in out


def test_cli_levels_error_handling(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("0 1 0\n1 2 1\n", encoding="utf-8")

    # Zero level
    with pytest.raises(SystemExit):
        main(["coverage", str(matrix_file), "--levels", "0", "2", "2"])

    # Non-integer level
    with pytest.raises(SystemExit):
        main(["coverage", str(matrix_file), "--levels", "invalid"])

    # Mismatched column count
    code = main(["coverage", str(matrix_file), "--levels", "2", "2"])
    assert code == 1
    err = capsys.readouterr().err
    assert "expected 3 levels" in err


def test_cli_flags_before_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Browser,OS\nChrome,Windows\nFirefox,Linux\n", encoding="utf-8")

    # Space-separated --levels before file
    code_spaces = main(["saturation", "--levels", "3", "4", str(csv_file)])
    assert code_spaces == 0
    out_spaces = capsys.readouterr().out
    assert "degree of saturation" in out_spaces

    # Comma-separated --levels before file
    code_commas = main(["saturation", "--levels", "3,4", str(csv_file)])
    assert code_commas == 0
    out_commas = capsys.readouterr().out
    assert "degree of saturation" in out_commas

    # -t / --strength after file
    code_strength = main(["coverage", str(OLD_DIR / "test1.txt"), "-t", "2"])
    assert code_strength == 0
    out_strength = capsys.readouterr().out
    assert "t=2:" in out_strength


def test_cli_mixed_format_batch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy_file = OLD_DIR / "test1.txt"  # 3 columns: (2, 3, 2)
    csv_file = tmp_path / "matrix3.csv"  # 3 columns
    csv_file.write_text("0,1,0\n1,2,1\n", encoding="utf-8")

    code = main(
        [
            "saturation",
            "--levels",
            "3",
            "4",
            "3",
            str(legacy_file),
            str(csv_file),
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert len(payload) == 2
    assert "degree_of_saturation" in payload[0]
    assert "degree_of_saturation" in payload[1]
