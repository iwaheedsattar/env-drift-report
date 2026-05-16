# env-drift-report

Compare dotenv files and report configuration drift before missing keys reach a deploy, onboarding guide, or CI job.

## Problem

`.env.example` files often drift away from real local or template configuration. A teammate adds `STRIPE_WEBHOOK_SECRET` to one file, leaves another template untouched, and the gap only appears after a failed setup. This CLI checks required keys, empty values, duplicate entries, malformed lines, and unexpected extras with output that works for humans or CI logs.

## Install

```bash
pip install env-drift-report
```

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## CLI Usage

Compare `.env` against `.env.example`:

```bash
env-drift-report .env
```

Compare several files against a reference:

```bash
env-drift-report --reference .env.example .env .env.production.example
```

Emit JSON for scripts:

```bash
env-drift-report --reference .env.example --format json .env
```

Ignore target-only keys when local files are expected to contain private values:

```bash
env-drift-report --ignore-extra .env
```

Ignore commented `KEY=value` examples:

```bash
env-drift-report --ignore-commented .env
```

The command exits with:

- `0` when every target file passes
- `1` when drift is found
- `2` when a file cannot be read

## Python Usage

```python
from env_drift_report import compare_env_files

report = compare_env_files(".env.example", ".env")

if not report.ok:
    print(report.missing)
```

## Example Output

```text
FAIL .env
Reference: .env.example
Missing:
  - REDIS_URL
Empty:
  - API_KEY (line 1)
Extra:
  - DEBUG_SQL
Duplicates:
  - .env:PORT (lines 2, 3)
```

## Supported Dotenv Syntax

The parser intentionally supports the common subset used by templates:

- `KEY=value`
- `export KEY=value`
- commented examples like `# KEY=value`
- quoted values
- inline comments after unquoted values

It does not evaluate shell expansion or source other files.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Build the package:

```bash
python3 -m build
```

## Contributing

Issues and pull requests are welcome. Keep changes focused, include tests for behavior changes, and update the README when command behavior changes.
