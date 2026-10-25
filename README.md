# py-log-analyzer

[![CI](https://github.com/sami1507/py-log-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/sami1507/py-log-analyzer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)

A command-line analyzer for nginx and Apache access logs. It reports traffic per hour, status-code classes, error rate, the busiest paths and user agents, and latency percentiles when the request time is logged.

It uses only the Python standard library and reads the file in a single streaming pass, so it works on logs that are far larger than memory.

## Quick start

```bash
python -m pip install -e ".[dev]"

loganalyzer access.log                              # human-readable report
loganalyzer access.log --format json --top 20       # machine-readable report
cat access.log | loganalyzer -                      # read from stdin
```

To log latency in nginx, add `$request_time` to the format:

```nginx
log_format timed '$remote_addr - $remote_user [$time_local] "$request" '
                 '$status $body_bytes_sent "$http_referer" "$http_user_agent" $request_time';
access_log /var/log/nginx/access.log timed;
```

Lines without a trailing request time still count toward traffic. Latency figures use only the lines that have one.

## Sample output

Output for [`tests/data/sample_access.log`](tests/data/sample_access.log):

```text
Access log summary
==================
Total requests    : 12
Unique visitors   : 5
Bytes sent        : 15.7 KiB
Error rate        : 25.00%
Malformed lines   : 1

Status classes
  2xx          8
  3xx          1
  4xx          1
  5xx          2

Top paths
         5  /api/items
         2  /health
         1  /api/orders
         1  /api/orders/88
         1  /static/app.js
         1  /static/app.css
         1  /about

Latency (ms)
  mean      456.18
  p50        95.00
  p95      2501.00
  p99      2501.00

Requests per hour
  2026-10-25 10:00       6
  2026-10-25 11:00       3
  2026-10-25 12:00       3
```

## How the numbers are calculated

| Metric          | Definition                                                                  |
| --------------- | --------------------------------------------------------------------------- |
| Unique visitors | Distinct client IP addresses                                                |
| Error rate      | Requests with a 4xx or 5xx status, divided by all requests                  |
| Top paths       | Request paths with the query string removed, so `/items?page=2` counts as `/items` |
| Latency         | Nearest-rank percentiles of `$request_time`, converted to milliseconds      |
| Malformed lines | Non-empty lines that do not match the combined log format; they are counted and skipped |

## Design decisions

- **One pass, bounded memory per metric.** Memory grows with the number of distinct paths, user agents, hours and latency samples, not with the number of lines.
- **Bad lines never stop the run.** Each one is counted and reported, so a truncated log still produces a result.
- **Nearest-rank percentiles.** Each reported value is an observed sample, which is easier to explain than interpolated values.
- **Exit codes for scripts.** `0` on success, `2` when the file cannot be opened, and argparse's usual `2` for invalid options.

## Development

```bash
python -m pip install -e ".[dev]"
pytest                # unit and CLI tests
ruff check .          # linting (pycodestyle, pyflakes, isort, pyupgrade, bugbear)
```

Project layout:

```text
src/loganalyzer/
  parser.py    Regex-based parser that yields LogEntry objects
  stats.py     Single-pass aggregation and percentile maths
  report.py    Text and JSON renderers
  cli.py       argparse entry point (also available as `python -m loganalyzer`)
tests/
  data/        Sample access log used by the tests
```

## Roadmap

- `--since` / `--until` time filters
- Apache `%D` (microseconds) support alongside nginx `$request_time`
- Optional CSV output for spreadsheet users

## License

MIT. See [LICENSE](LICENSE).
