"""Parsing for nginx and Apache "combined" access log lines.

Lines may optionally end with the request time in seconds, as written by
nginx when `$request_time` is part of `log_format`.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime

LINE_PATTERN = re.compile(
    r"(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "
    r'"(?P<method>[A-Z]+) (?P<path>\S+)(?: [^"]*)?" '
    r"(?P<status>\d{3}) (?P<bytes>\d+|-) "
    r'"(?P<referrer>[^"]*)" "(?P<agent>[^"]*)"'
    r"(?: (?P<request_time>\d+(?:\.\d+)?))?\s*$"
)
TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


@dataclass(frozen=True, slots=True)
class LogEntry:
    """A single parsed request."""

    ip: str
    timestamp: datetime
    method: str
    path: str
    status: int
    bytes_sent: int
    user_agent: str
    request_time: float | None = None


def parse_line(line: str) -> LogEntry | None:
    """Parse one log line. Returns ``None`` when the line does not match the format."""
    match = LINE_PATTERN.match(line.rstrip("\r\n"))
    if match is None:
        return None

    try:
        timestamp = datetime.strptime(match["time"], TIME_FORMAT)
    except ValueError:
        return None

    raw_bytes = match["bytes"]
    raw_request_time = match["request_time"]
    return LogEntry(
        ip=match["ip"],
        timestamp=timestamp,
        method=match["method"],
        path=match["path"],
        status=int(match["status"]),
        bytes_sent=0 if raw_bytes == "-" else int(raw_bytes),
        user_agent=match["agent"],
        request_time=float(raw_request_time) if raw_request_time is not None else None,
    )


def iter_entries(
    lines: Iterable[str],
    on_malformed: Callable[[str], None] | None = None,
) -> Iterator[LogEntry]:
    """Lazily yield parsed entries.

    Blank lines are skipped silently. Lines that do not parse are passed to
    ``on_malformed`` and then skipped, so one bad line never stops an analysis.
    """
    for line in lines:
        if not line.strip():
            continue
        entry = parse_line(line)
        if entry is None:
            if on_malformed is not None:
                on_malformed(line)
            continue
        yield entry
