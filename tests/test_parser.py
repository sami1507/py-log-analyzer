from datetime import datetime, timezone

from loganalyzer.parser import iter_entries, parse_line

LINE = (
    '203.0.113.7 - - [25/Oct/2026:10:00:01 +0000] "GET /api/items?page=2 HTTP/1.1" '
    '200 512 "-" "Mozilla/5.0" 0.120'
)


def test_parses_a_complete_line():
    entry = parse_line(LINE)

    assert entry is not None
    assert entry.ip == "203.0.113.7"
    assert entry.timestamp == datetime(2026, 10, 25, 10, 0, 1, tzinfo=timezone.utc)
    assert (entry.method, entry.path, entry.status) == ("GET", "/api/items?page=2", 200)
    assert entry.bytes_sent == 512
    assert entry.user_agent == "Mozilla/5.0"
    assert entry.request_time == 0.12


def test_dash_bytes_are_treated_as_zero():
    entry = parse_line(LINE.replace(" 200 512 ", " 304 - "))
    assert entry is not None
    assert entry.bytes_sent == 0
    assert entry.status == 304


def test_request_time_is_optional():
    entry = parse_line(LINE.rsplit(" ", 1)[0])
    assert entry is not None
    assert entry.request_time is None


def test_returns_none_for_lines_that_do_not_match():
    assert parse_line("not a log line") is None


def test_returns_none_for_impossible_dates():
    assert parse_line(LINE.replace("25/Oct/2026", "31/Feb/2026")) is None


def test_iter_entries_skips_blank_lines_and_reports_malformed_ones():
    rejected: list[str] = []

    entries = list(iter_entries([LINE, "", "garbage", LINE], on_malformed=rejected.append))

    assert len(entries) == 2
    assert rejected == ["garbage"]
