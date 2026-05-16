"""Compare dotenv files and report configuration drift."""

from .core import DriftReport, EnvFile, EnvKey, compare_env_files, parse_env_file

__all__ = [
    "DriftReport",
    "EnvFile",
    "EnvKey",
    "compare_env_files",
    "parse_env_file",
]

__version__ = "0.1.0"
