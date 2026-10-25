"""Aggregations over parsed log entries."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from statistics import fmean

from loganalyzer.parser import LogEntry


@dataclass(slots=True)
class Summary:
    """Aggregated view of an access log."""

    total_requests: int = 0
    malformed_lines: int = 0
    unique_visitors: int = 0
    bytes_sent: int = 0
    status_classes: dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0
    top_paths: list[tuple[str, int]] = field(default_factory=list)
    top_user_agents: list[tuple[str, int]] = field(default_factory=list)
    requests_per_hour: dict[str, int] = field(default_factory=dict)
    latency_ms: dict[str, float] | None = None


def normalise_path(path: str) -> str:
    """Drop the query string so ``/items?page=2`` and ``/items?page=3`` count together."""
    return path.split("?", 1)[0] or "/"


def percentile(sorted_values: Sequence[float], pct: float) -> float:
    """Return the nearest-rank percentile of an ascending, non-empty sequence."""
    if not sorted_values:
        raise ValueError("cannot take a percentile of an empty sequence")
    if not 0 < pct <= 100:
        raise ValueError(f"pct must be in (0, 100], received {pct}")
    rank = math.ceil(pct / 100 * len(sorted_values))
    return sorted_values[rank - 1]


def summarize(entries: Iterable[LogEntry], *, top: int = 10) -> Summary:
    """Aggregate entries in a single pass. Memory grows with distinct keys and latency samples."""
    status_counts: Counter[str] = Counter()
    paths: Counter[str] = Counter()
    agents: Counter[str] = Counter()
    hours: Counter[str] = Counter()
    visitors: set[str] = set()
    latencies: list[float] = []
    total = 0
    bytes_sent = 0

    for entry in entries:
        total += 1
        visitors.add(entry.ip)
        bytes_sent += entry.bytes_sent
        status_counts[f"{entry.status // 100}xx"] += 1
        paths[normalise_path(entry.path)] += 1
        agents[entry.user_agent or "-"] += 1
        hours[entry.timestamp.strftime("%Y-%m-%d %H:00")] += 1
        if entry.request_time is not None:
            latencies.append(entry.request_time * 1000)

    errors = status_counts["4xx"] + status_counts["5xx"]
    return Summary(
        total_requests=total,
        unique_visitors=len(visitors),
        bytes_sent=bytes_sent,
        status_classes=dict(sorted(status_counts.items())),
        error_rate=round(errors / total, 4) if total else 0.0,
        top_paths=paths.most_common(top),
        top_user_agents=agents.most_common(top),
        requests_per_hour=dict(sorted(hours.items())),
        latency_ms=_latency_profile(latencies),
    )


def _latency_profile(samples: list[float]) -> dict[str, float] | None:
    if not samples:
        return None
    samples.sort()
    return {
        "mean": round(fmean(samples), 2),
        "p50": round(percentile(samples, 50), 2),
        "p95": round(percentile(samples, 95), 2),
        "p99": round(percentile(samples, 99), 2),
    }
