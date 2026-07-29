from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from loop_engineering.engine import InspectionEngine
from loop_engineering.graph_runtime import RuntimeUnavailableError

from tests.helpers import initialize_git_repository, make_profile


class InspectionEngineTests(unittest.TestCase):
    def test_failed_check_yields_one_human_target_without_product_change(self) -> None:
        with tempfile.TemporaryDirectory() as target_directory:
            with tempfile.TemporaryDirectory() as output_directory:
                target = Path(target_directory)
                initialize_git_repository(target)
                profile = make_profile(target, script="raise SystemExit(3)")

                outcome, report_directory = InspectionEngine(profile).run_and_write(
                    Path(output_directory), runtime="stdlib"
                )

                self.assertEqual(outcome.status, "needs_human_input")
                self.assertEqual(len(outcome.findings), 1)
                self.assertIsNotNone(outcome.selected_target)
                self.assertEqual(outcome.runtime, "stdlib-fallback")
                self.assertTrue((report_directory / "report.json").is_file())
                self.assertTrue((report_directory / "findings.json").is_file())
                self.assertTrue((report_directory / "report.md").is_file())
                self.assertTrue((report_directory / "report.html").is_file())
                self.assertTrue((report_directory / "manifest.json").is_file())

                if importlib.util.find_spec("jsonschema") is not None:
                    from jsonschema import Draft202012Validator

                    schema_path = (
                        Path(__file__).resolve().parents[1]
                        / "schemas"
                        / "inspection-report.schema.json"
                    )
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                    report = json.loads(
                        (report_directory / "report.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    Draft202012Validator(schema).validate(report)

    def test_repository_mutation_aborts_safely(self) -> None:
        with tempfile.TemporaryDirectory() as target_directory:
            target = Path(target_directory)
            initialize_git_repository(target)
            script = "from pathlib import Path; Path('generated.txt').write_text('x')"
            profile = make_profile(target, script=script)

            outcome = InspectionEngine(profile).run(runtime="stdlib")

            self.assertEqual(outcome.status, "aborted_safely")
            self.assertTrue(outcome.stop_reasons)
            self.assertTrue((target / "generated.txt").exists())

    def test_langgraph_runtime_is_real_or_fails_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as target_directory:
            target = Path(target_directory)
            initialize_git_repository(target)
            profile = make_profile(target)
            if importlib.util.find_spec("langgraph") is None:
                with self.assertRaises(RuntimeUnavailableError):
                    InspectionEngine(profile).run(runtime="langgraph")
            else:
                outcome = InspectionEngine(profile).run(runtime="langgraph")
                self.assertEqual(outcome.runtime, "langgraph")
                self.assertEqual(outcome.status, "accepted")


if __name__ == "__main__":
    unittest.main()
