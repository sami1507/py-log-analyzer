"""Renders a Summary as plain text or JSON."""

from __future__ import annotations

import json
from dataclasses import asdict

from loganalyzer.stats import Summary


def format_bytes(value: int) -> str:
    """Format a byte count with binary units, e.g. 16030 becomes '15.7 KiB'."""
    size = float(value)
    for unit in ("B", "KiB", "MiB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GiB"


def render_json(summary: Summary) -> str:
    """Serialise the summary as indented JSON for pipelines and dashboards."""
    return json.dumps(asdict(summary), indent=2) + "\n"


def render_text(summary: Summary) -> str:
    """Render a human-readable report with aligned columns."""
    lines = [
        "Access log summary",
        "==================",
        f"Total requests    : {summary.total_requests:,}",
        f"Unique visitors   : {summary.unique_visitors:,}",
        f"Bytes sent        : {format_bytes(summary.bytes_sent)}",
        f"Error rate        : {summary.error_rate:.2%}",
        f"Malformed lines   : {summary.malformed_lines:,}",
        "",
        "Status classes",
    ]
    lines += [f"  {status:<6}{count:>8,}" for status, count in summary.status_classes.items()]

    lines += ["", "Top paths"]
    lines += [f"  {count:>8,}  {path}" for path, count in summary.top_paths]

    lines += ["", "Top user agents"]
    lines += [f"  {count:>8,}  {agent[:70]}" for agent, count in summary.top_user_agents]

    if summary.latency_ms is not None:
        lines += ["", "Latency (ms)"]
        lines += [f"  {name:<6}{value:>10.2f}" for name, value in summary.latency_ms.items()]

    lines += ["", "Requests per hour"]
    lines += [f"  {hour:<18}{count:>6,}" for hour, count in summary.requests_per_hour.items()]

    return "\n".join(lines) + "\n"
