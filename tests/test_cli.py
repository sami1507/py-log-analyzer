import json
from pathlib import Path

import pytest

from loganalyzer.cli import main

DATA = Path(__file__).parent / "data" / "sample_access.log"


def test_text_report_for_a_file(capsys):
    exit_code = main([str(DATA)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Total requests    : 12" in out
    assert "Malformed lines   : 1" in out
    assert "/api/items" in out


def test_json_report_respects_top(capsys):
    exit_code = main([str(DATA), "--format", "json", "--top", "2"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["total_requests"] == 12
    assert data["malformed_lines"] == 1
    assert len(data["top_paths"]) == 2


def test_reads_from_stdin(monkeypatch, capsys):
    with DATA.open(encoding="utf-8") as handle:
        monkeypatch.setattr("sys.stdin", handle)
        exit_code = main(["-", "--format", "json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["total_requests"] == 12


def test_missing_file_returns_exit_code_two(capsys):
    assert main(["does-not-exist.log"]) == 2
    assert "cannot open" in capsys.readouterr().err


def test_rejects_a_non_positive_top(capsys):
    with pytest.raises(SystemExit):
        main([str(DATA), "--top", "0"])
    assert "--top must be at least 1" in capsys.readouterr().err
