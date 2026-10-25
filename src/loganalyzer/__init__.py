"""Fast, dependency-free analyzer for nginx and Apache access logs."""

from loganalyzer.parser import LogEntry, iter_entries, parse_line
from loganalyzer.stats import Summary, summarize

__version__ = "0.1.0"

__all__ = ["LogEntry", "Summary", "__version__", "iter_entries", "parse_line", "summarize"]
