"""Command-line interface.

Examples::

    loganalyzer access.log
    loganalyzer access.log --format json --top 20
    cat access.log | loganalyzer -
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Sequence

from loganalyzer.parser import iter_entries
from loganalyzer.report import render_json, render_text
from loganalyzer.stats import summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loganalyzer",
        description="Summarise nginx and Apache access logs.",
    )
    parser.add_argument(
        "logfile",
        nargs="?",
        default="-",
        help="path to an access log, or '-' to read from stdin (default)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="how many paths and user agents to list (default: 10)",
    )
    return parser


def _analyze(lines: Iterable[str], *, top: int, output_format: str) -> int:
    malformed = 0

    def count_malformed(_line: str) -> None:
        nonlocal malformed
        malformed += 1

    summary = summarize(iter_entries(lines, on_malformed=count_malformed), top=top)
    summary.malformed_lines = malformed

    rendered = render_json(summary) if output_format == "json" else render_text(summary)
    sys.stdout.write(rendered)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top must be at least 1")

    if args.logfile == "-":
        return _analyze(sys.stdin, top=args.top, output_format=args.format)

    try:
        with open(args.logfile, encoding="utf-8", errors="replace") as handle:
            return _analyze(handle, top=args.top, output_format=args.format)
    except OSError as exc:
        print(f"loganalyzer: cannot open {args.logfile}: {exc.strerror}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
