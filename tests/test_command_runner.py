from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from loop_engineering.command_runner import CommandRunner
from loop_engineering.models import CheckStatus, CommandCheck


class CommandRunnerTests(unittest.TestCase):
    def test_nonzero_exit_is_finding_not_tool_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            check = CommandCheck(
                id="known-failure",
                title="Known failure",
                command=(sys.executable, "-c", "raise SystemExit(7)"),
            )
            result = CommandRunner(Path(directory), 1000).run("backend", check)
            self.assertEqual(result.status, CheckStatus.FINDING)
            self.assertEqual(result.exit_code, 7)
            self.assertIsNone(result.error_kind)

    def test_missing_executable_is_tool_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            check = CommandCheck(
                id="missing-tool",
                title="Missing tool",
                command=("definitely-not-a-real-loop-tool", "--version"),
            )
            result = CommandRunner(Path(directory), 1000).run("frontend", check)
            self.assertEqual(result.status, CheckStatus.TOOL_ERROR)
            self.assertEqual(result.error_kind, "missing_executable")

    def test_configured_exit_code_is_tool_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            check = CommandCheck(
                id="structured-tool-error",
                title="Structured tool error",
                command=(sys.executable, "-c", "raise SystemExit(2)"),
                tool_error_exit_codes=(2,),
            )
            result = CommandRunner(Path(directory), 1000).run("frontend", check)
            self.assertEqual(result.status, CheckStatus.TOOL_ERROR)
            self.assertEqual(result.exit_code, 2)
            self.assertEqual(
                result.error_kind, "configured_tool_error_exit_code"
            )

    def test_redacts_common_secret_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = "print('api_key=do-not-store-this')"
            check = CommandCheck(
                id="redaction",
                title="Redaction",
                command=(sys.executable, "-c", script),
            )
            result = CommandRunner(Path(directory), 1000).run("backend", check)
            self.assertNotIn("do-not-store-this", result.evidence)
            self.assertIn("[REDACTED]", result.evidence)


if __name__ == "__main__":
    unittest.main()
