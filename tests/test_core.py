from pathlib import Path
import tempfile
import unittest

from env_drift_report.core import compare_env_files, parse_env_file, strip_inline_comment


class CoreTests(unittest.TestCase):
    def test_parse_file_reads_export_and_commented_examples(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env.example"
            path.write_text(
                "API_KEY=\nexport PORT=3000\n# OPTIONAL_FLAG=true\n",
                encoding="utf-8",
            )

            env_file = parse_env_file(path)

        self.assertEqual(set(env_file.keys), {"API_KEY", "PORT", "OPTIONAL_FLAG"})
        self.assertTrue(env_file.keys["OPTIONAL_FLAG"].commented)

    def test_compare_reports_missing_empty_extra_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            reference.write_text("API_KEY=\nPORT=3000\nREDIS_URL=\n", encoding="utf-8")
            target.write_text(
                "API_KEY=   # fill me\nPORT=3000\nPORT=4000\nEXTRA=value\n",
                encoding="utf-8",
            )

            report = compare_env_files(reference, target)

        self.assertFalse(report.ok)
        self.assertEqual(report.missing, ["REDIS_URL"])
        self.assertEqual(report.empty, ["API_KEY"])
        self.assertEqual(report.extra, ["EXTRA"])
        self.assertTrue(any(key.endswith(".env:PORT") for key in report.duplicate_keys))

    def test_extra_key_fails_unless_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            reference.write_text("API_KEY=\n", encoding="utf-8")
            target.write_text("API_KEY=value\nDEBUG_SQL=true\n", encoding="utf-8")

            report = compare_env_files(reference, target)
            ignored = compare_env_files(reference, target, ignore_extra=True)

        self.assertFalse(report.ok)
        self.assertEqual(report.extra, ["DEBUG_SQL"])
        self.assertTrue(ignored.ok)

    def test_ignore_commented_excludes_comment_examples(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            reference.write_text("# OPTIONAL_FLAG=true\n", encoding="utf-8")
            target.write_text("", encoding="utf-8")

            report = compare_env_files(reference, target, include_commented=False)

        self.assertTrue(report.ok)

    def test_strip_inline_comment_preserves_hash_inside_quotes(self) -> None:
        self.assertEqual(strip_inline_comment('"abc#def" # note'), '"abc#def" ')


if __name__ == "__main__":
    unittest.main()
