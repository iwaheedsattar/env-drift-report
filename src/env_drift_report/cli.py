from __future__ import annotations

import argparse
import html
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
        choices=("text", "json", "html"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write the report to a file instead of stdout.",
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
        content = json.dumps([report_to_dict(report) for report in reports], indent=2)
    elif args.format == "html":
        content = reports_to_html(reports)
    else:
        content = reports_to_text(reports)

    if args.output:
        Path(args.output).write_text(content + "\n", encoding="utf-8")
    else:
        print(content)

    return 0 if all(report.ok for report in reports) else 1


def reports_to_text(reports: list[DriftReport]) -> str:
    lines: list[str] = []
    for index, report in enumerate(reports):
        if index:
            lines.append("")
        status = "PASS" if report.ok else "FAIL"
        lines.append(f"{status} {report.target.path}")
        lines.append(f"Reference: {report.reference.path}")

        if report.missing:
            lines.append("Missing:")
            for key in report.missing:
                lines.append(f"  - {key}")
        if report.empty:
            lines.append("Empty:")
            for key in report.empty:
                line = report.target.keys[key].line
                lines.append(f"  - {key} (line {line})")
        if report.extra:
            lines.append("Extra:")
            for key in report.extra:
                lines.append(f"  - {key}")
        if report.duplicate_keys:
            lines.append("Duplicates:")
            for key, duplicate_lines in report.duplicate_keys.items():
                joined = ", ".join(str(line) for line in duplicate_lines)
                lines.append(f"  - {key} (lines {joined})")
        if report.invalid_lines:
            lines.append("Invalid lines:")
            for line in report.invalid_lines:
                lines.append(f"  - line {line}")
    return "\n".join(lines)


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


def reports_to_html(reports: list[DriftReport]) -> str:
    total = len(reports)
    failed = sum(1 for report in reports if not report.ok)
    cards = "\n".join(report_to_html_card(report) for report in reports)
    status_class = "pass" if failed == 0 else "fail"
    title = "Env Drift Report"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --line: #d8dee7;
      --pass: #11683c;
      --fail: #a92727;
      --warn: #8a5a00;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 20px;
    }}
    h1, h2, p {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
      font-weight: 700;
    }}
    .summary {{
      color: var(--muted);
      margin-top: 4px;
    }}
    .badge {{
      border: 1px solid currentColor;
      border-radius: 999px;
      padding: 5px 10px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .badge.pass {{
      color: var(--pass);
    }}
    .badge.fail {{
      color: var(--fail);
    }}
    article {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 14px;
      overflow: hidden;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }}
    .path {{
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    section {{
      padding: 12px 16px 16px;
    }}
    h3 {{
      margin: 14px 0 6px;
      font-size: 14px;
    }}
    ul {{
      margin: 0;
      padding-left: 22px;
    }}
    li {{
      margin: 3px 0;
      overflow-wrap: anywhere;
    }}
    .empty {{
      color: var(--pass);
      font-weight: 600;
    }}
    .problem {{
      color: var(--fail);
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{title}</h1>
        <p class="summary">{total} target file{"s" if total != 1 else ""} checked, {failed} failed</p>
      </div>
      <span class="badge {status_class}">{"PASS" if failed == 0 else "FAIL"}</span>
    </header>
    {cards}
  </main>
</body>
</html>"""


def report_to_html_card(report: DriftReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    status_class = "pass" if report.ok else "fail"
    sections = [
        html_section("Missing", report.missing),
        html_section(
            "Empty",
            [f"{key} (line {report.target.keys[key].line})" for key in report.empty],
        ),
        html_section("Extra", report.extra),
        html_section(
            "Duplicates",
            [
                f"{key} (lines {', '.join(str(line) for line in lines)})"
                for key, lines in report.duplicate_keys.items()
            ],
        ),
        html_section("Invalid lines", [f"line {line}" for line in report.invalid_lines]),
    ]
    body = "\n".join(section for section in sections if section)
    if not body:
        body = '<p class="empty">No drift found.</p>'
    return f"""<article>
  <div class="card-head">
    <div>
      <h2>{html.escape(str(report.target.path))}</h2>
      <p class="path">Reference: {html.escape(str(report.reference.path))}</p>
    </div>
    <span class="badge {status_class}">{status}</span>
  </div>
  <section>{body}</section>
</article>"""


def html_section(title: str, items: list[str]) -> str:
    if not items:
        return ""
    rows = "\n".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f'<h3 class="problem">{html.escape(title)}</h3><ul>{rows}</ul>'


if __name__ == "__main__":
    raise SystemExit(main())
