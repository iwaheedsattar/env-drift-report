from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from env_drift_report.cli import main


class CliTests(unittest.TestCase):
    def test_cli_returns_failure_for_missing_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            reference.write_text("API_KEY=\n", encoding="utf-8")
            target.write_text("", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--reference", str(reference), str(target)])

        self.assertEqual(exit_code, 1)

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            reference.write_text("API_KEY=\n", encoding="utf-8")
            target.write_text("API_KEY=value\n", encoding="utf-8")

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(
                    ["--reference", str(reference), "--format", "json", str(target)]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn('"ok": true', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
