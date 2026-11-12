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
