from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


ASSIGNMENT_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


@dataclass(frozen=True)
class EnvKey:
    name: str
    value: str
    line: int
    commented: bool = False

    @property
    def is_empty(self) -> bool:
        return strip_inline_comment(self.value).strip().strip("'\"") == ""


@dataclass(frozen=True)
class EnvFile:
    path: Path
    keys: dict[str, EnvKey]
    duplicates: dict[str, list[int]]
    invalid_lines: list[int]


@dataclass(frozen=True)
class DriftReport:
    reference: EnvFile
    target: EnvFile
    missing: list[str]
    extra: list[str]
    empty: list[str]
    duplicate_keys: dict[str, list[int]]
    invalid_lines: list[int]

    @property
    def ok(self) -> bool:
        return not (
            self.missing
            or self.extra
            or self.empty
            or self.duplicate_keys
            or self.invalid_lines
        )


def parse_env_file(path: str | Path, *, include_commented: bool = True) -> EnvFile:
    env_path = Path(path)
    keys: dict[str, EnvKey] = {}
    seen: dict[str, list[int]] = {}
    invalid_lines: list[int] = []

    with env_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            parsed = parse_line(raw_line)
            if parsed is None:
                stripped = raw_line.strip()
                if stripped and not stripped.startswith("#"):
                    invalid_lines.append(line_number)
                continue

            name, value, commented = parsed
            if commented and not include_commented:
                continue

            seen.setdefault(name, []).append(line_number)
            keys[name] = EnvKey(name=name, value=value, line=line_number, commented=commented)

    duplicates = {key: lines for key, lines in seen.items() if len(lines) > 1}
    return EnvFile(path=env_path, keys=keys, duplicates=duplicates, invalid_lines=invalid_lines)


def parse_line(raw_line: str) -> tuple[str, str, bool] | None:
    line = raw_line.strip()
    if not line:
        return None

    commented = False
    if line.startswith("#"):
        candidate = line[1:].strip()
        if not ASSIGNMENT_RE.match(candidate):
            return None
        line = candidate
        commented = True

    match = ASSIGNMENT_RE.match(line)
    if not match:
        return None

    return match.group(1), match.group(2), commented


def compare_env_files(
    reference_path: str | Path,
    target_path: str | Path,
    *,
    include_commented: bool = True,
    ignore_extra: bool = False,
) -> DriftReport:
    reference = parse_env_file(reference_path, include_commented=include_commented)
    target = parse_env_file(target_path, include_commented=include_commented)
    reference_keys = set(reference.keys)
    target_keys = set(target.keys)

    missing = sorted(reference_keys - target_keys)
    extra = [] if ignore_extra else sorted(target_keys - reference_keys)
    empty = sorted(key for key in reference_keys & target_keys if target.keys[key].is_empty)
    duplicates = merge_duplicates(reference, target)
    invalid_lines = sorted(set(reference.invalid_lines + target.invalid_lines))

    return DriftReport(
        reference=reference,
        target=target,
        missing=missing,
        extra=extra,
        empty=empty,
        duplicate_keys=duplicates,
        invalid_lines=invalid_lines,
    )


def merge_duplicates(*env_files: EnvFile) -> dict[str, list[int]]:
    merged: dict[str, list[int]] = {}
    for env_file in env_files:
        for key, lines in env_file.duplicates.items():
            merged[f"{env_file.path}:{key}"] = lines
    return merged


def strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
            continue
        if char == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index]
    return value


def summarize_reports(reports: Iterable[DriftReport]) -> tuple[int, int]:
    total = 0
    failed = 0
    for report in reports:
        total += 1
        if not report.ok:
            failed += 1
    return total, failed
