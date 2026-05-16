from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import DriftReport, compare_env_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="env-drift-report",
        description="Compare dotenv files and report missing, empty, duplicate, and extra keys.",
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="One or more dotenv files to compare against the reference.",
    )
    parser.add_argument(
        "-r",
        "--reference",
        default=".env.example",
        help="Reference dotenv file. Defaults to .env.example.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--ignore-extra",
        action="store_true",
        help="Do not report keys that exist only in target files.",
    )
    parser.add_argument(
        "--ignore-commented",
        action="store_true",
        help="Ignore commented KEY=value lines in dotenv files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        reports = [
            compare_env_files(
                args.reference,
                target,
                include_commented=not args.ignore_commented,
                ignore_extra=args.ignore_extra,
            )
            for target in args.targets
        ]
    except OSError as exc:
        print(f"env-drift-report: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([report_to_dict(report) for report in reports], indent=2))
    else:
        print_text(reports)

    return 0 if all(report.ok for report in reports) else 1


def print_text(reports: list[DriftReport]) -> None:
    for index, report in enumerate(reports):
        if index:
            print()
        status = "PASS" if report.ok else "FAIL"
        print(f"{status} {report.target.path}")
        print(f"Reference: {report.reference.path}")

        if report.missing:
            print("Missing:")
            for key in report.missing:
                print(f"  - {key}")
        if report.empty:
            print("Empty:")
            for key in report.empty:
                line = report.target.keys[key].line
                print(f"  - {key} (line {line})")
        if report.extra:
            print("Extra:")
            for key in report.extra:
                print(f"  - {key}")
        if report.duplicate_keys:
            print("Duplicates:")
            for key, lines in report.duplicate_keys.items():
                joined = ", ".join(str(line) for line in lines)
                print(f"  - {key} (lines {joined})")
        if report.invalid_lines:
            print("Invalid lines:")
            for line in report.invalid_lines:
                print(f"  - line {line}")


def report_to_dict(report: DriftReport) -> dict[str, object]:
    return {
        "ok": report.ok,
        "reference": str(Path(report.reference.path)),
        "target": str(Path(report.target.path)),
        "missing": report.missing,
        "extra": report.extra,
        "empty": report.empty,
        "duplicates": report.duplicate_keys,
        "invalid_lines": report.invalid_lines,
    }


if __name__ == "__main__":
    raise SystemExit(main())
