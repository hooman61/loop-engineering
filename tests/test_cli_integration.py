from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from loop_engineering.cli import main

from tests.helpers import initialize_git_repository


@unittest.skipUnless(
    importlib.util.find_spec("yaml")
    and importlib.util.find_spec("jsonschema")
    and importlib.util.find_spec("langgraph"),
    "full integration dependencies are not installed",
)
class CliIntegrationTests(unittest.TestCase):
    def test_yaml_profile_runs_through_real_langgraph(self) -> None:
        import yaml

        with tempfile.TemporaryDirectory() as target_directory:
            with tempfile.TemporaryDirectory() as control_directory:
                target = Path(target_directory)
                control = Path(control_directory)
                initialize_git_repository(target)
                disabled = {"enabled": False, "checks": []}
                profile = {
                    "schema_version": "1.0",
                    "project": {"id": "cli-product", "root": str(target)},
                    "read_only": {
                        "require_git_repository": True,
                        "require_clean_start": True,
                        "fail_on_change": True,
                    },
                    "stop_on_inspector_error": True,
                    "max_evidence_chars": 4000,
                    "inspectors": {
                        "frontend": dict(disabled),
                        "backend": {
                            "enabled": True,
                            "checks": [
                                {
                                    "id": "python-smoke",
                                    "title": "Python smoke check",
                                    "command": [
                                        sys.executable,
                                        "-c",
                                        "raise SystemExit(0)",
                                    ],
                                    "working_directory": ".",
                                    "timeout_seconds": 30,
                                    "success_exit_codes": [0],
                                    "severity_on_failure": "high",
                                    "priority": 50,
                                }
                            ],
                        },
                        "database": dict(disabled),
                        "integration": dict(disabled),
                    },
                }
                profile_path = control / "inspection.yaml"
                profile_path.write_text(
                    yaml.safe_dump(profile, sort_keys=False), encoding="utf-8"
                )
                output_root = control / "reports"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "run",
                            str(profile_path),
                            "--output",
                            str(output_root),
                            "--runtime",
                            "langgraph",
                        ]
                    )

                self.assertEqual(exit_code, 0, stdout.getvalue())
                report_paths = list(output_root.glob("*/report.json"))
                self.assertEqual(len(report_paths), 1)
                report = json.loads(report_paths[0].read_text(encoding="utf-8"))
                self.assertEqual(report["runtime"], "langgraph")
                self.assertEqual(report["status"], "accepted")


if __name__ == "__main__":
    unittest.main()

