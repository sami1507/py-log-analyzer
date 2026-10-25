from pathlib import Path

import pytest

from loganalyzer.parser import LogEntry, iter_entries
from loganalyzer.stats import normalise_path, percentile, summarize

DATA = Path(__file__).parent / "data" / "sample_access.log"


def load_sample() -> list[LogEntry]:
    with DATA.open(encoding="utf-8") as handle:
        return list(iter_entries(handle))


def test_percentile_uses_nearest_rank():
    values = [1, 2, 4, 12, 21, 95, 110, 120, 310, 1842, 2501]

    assert percentile(values, 50) == 95
    assert percentile(values, 95) == 2501
    assert percentile(values, 100) == 2501
    assert percentile([42], 99) == 42


def test_percentile_rejects_invalid_input():
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile([1, 2], 0)


def test_normalise_path_drops_the_query_string():
    assert normalise_path("/items?page=2") == "/items"
    assert normalise_path("/") == "/"
    assert normalise_path("?x=1") == "/"


def test_summary_totals_match_the_sample_file():
    summary = summarize(load_sample())

    assert summary.total_requests == 12
    assert summary.unique_visitors == 5
    assert summary.bytes_sent == 16030
    assert summary.status_classes == {"2xx": 8, "3xx": 1, "4xx": 1, "5xx": 2}
    assert summary.error_rate == 0.25


def test_top_paths_group_query_strings_together():
    summary = summarize(load_sample(), top=3)

    assert summary.top_paths[0] == ("/api/items", 5)
    assert summary.top_paths[1] == ("/health", 2)
    assert len(summary.top_paths) == 3


def test_latency_profile_uses_only_lines_with_request_time():
    latency = summarize(load_sample()).latency_ms

    assert latency is not None
    assert latency["p50"] == pytest.approx(95.0)
    assert latency["p95"] == pytest.approx(2501.0)
    assert latency["mean"] == pytest.approx(456.18, abs=0.01)


def test_requests_are_bucketed_per_hour():
    hours = summarize(load_sample()).requests_per_hour

    assert hours == {
        "2026-10-25 10:00": 6,
        "2026-10-25 11:00": 3,
        "2026-10-25 12:00": 3,
    }


def test_latency_is_none_when_no_line_has_request_time():
    entries = [entry for entry in load_sample() if entry.request_time is None]

    summary = summarize(entries)

    assert summary.total_requests == 1
    assert summary.latency_ms is None
