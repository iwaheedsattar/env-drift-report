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

    def test_cli_html_output_can_be_written_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / ".env.example"
            target = root / ".env"
            output = root / "env-report.html"
            reference.write_text("API_KEY=\nREDIS_URL=\n", encoding="utf-8")
            target.write_text("API_KEY=value\n", encoding="utf-8")

            exit_code = main(
                [
                    "--reference",
                    str(reference),
                    "--format",
                    "html",
                    "--output",
                    str(output),
                    str(target),
                ]
            )
            html = output.read_text(encoding="utf-8")

            self.assertEqual(exit_code, 1)
            self.assertIn("<!doctype html>", html)
            self.assertIn("Env Drift Report", html)
            self.assertIn("REDIS_URL", html)
            self.assertIn("FAIL", html)


if __name__ == "__main__":
    unittest.main()
