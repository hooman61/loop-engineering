from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loop_engineering.command_runner import expand_runtime_tokens
from loop_engineering.config import load_profile
from loop_engineering.github_actions import render_workflow
from loop_engineering.health import diagnose
from loop_engineering.onboarding import detect_project, write_profile
from loop_engineering.reporting import write_dashboard


class ProductCliTests(unittest.TestCase):
    def test_runtime_python_token_is_portable(self) -> None:
        expanded = expand_runtime_tokens(("{python}", "-V"))
        self.assertNotEqual(expanded[0], "{python}")
        self.assertEqual(expanded[1], "-V")

    def test_project_python_prefers_nearby_virtual_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            working = Path(directory)
            executable = working / ".venv" / "Scripts" / "python.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"placeholder")

            expanded = expand_runtime_tokens(
                ("{project-python}", "-V"), working
            )

            self.assertEqual(expanded[0], str(executable))

    def test_detects_django_and_react_without_running_project_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manage.py").write_text("", encoding="utf-8")
            frontend = root / "frontend"
            frontend.mkdir()
            (frontend / "package.json").write_text(
                json.dumps(
                    {"scripts": {"lint": "eslint .", "build": "vite build"}}
                ),
                encoding="utf-8",
            )

            detection = detect_project(root)

            self.assertEqual(detection.technologies, ("django", "node", "python"))
            self.assertTrue(detection.inspectors["frontend"]["enabled"])
            self.assertTrue(detection.inspectors["backend"]["enabled"])
            self.assertTrue(detection.inspectors["database"]["enabled"])
            self.assertFalse(detection.inspectors["integration"]["enabled"])

    def test_generated_profile_is_relative_and_ready(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML is not installed")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "portable-app"
            root.mkdir()
            (root / "pyproject.toml").write_text(
                "[project]\nname='portable-app'\nversion='1'\n",
                encoding="utf-8",
            )
            profile_path, _ = write_profile(root)
            text = profile_path.read_text(encoding="utf-8")

            self.assertIn("root: ..", text)
            profile = load_profile(profile_path)
            result = diagnose(profile, Path(directory) / "reports")
            self.assertEqual(result["project_id"], "portable-app")
            self.assertTrue(
                any(
                    item["name"].endswith("/executable")
                    for item in result["checks"]
                )
            )

    def test_generated_workflow_is_pinned_and_least_privilege(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            detection = detect_project(root)
            try:
                import yaml
            except ImportError:
                self.skipTest("PyYAML is not installed")
            profile_path, _ = write_profile(root)
            profile = load_profile(profile_path)
            workflow = render_workflow(profile)

            self.assertIn("permissions:\n  contents: read", workflow)
            self.assertNotIn("pull_request_target", workflow)
            self.assertNotIn("secrets.", workflow)
            self.assertIn("actions/checkout@11bd719", workflow)
            yaml.safe_load(workflow)
            self.assertTrue(detection.inspectors["backend"]["enabled"])

    def test_dashboard_indexes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "inspection-1"
            report.mkdir()
            (report / "report.json").write_text(
                json.dumps(
                    {
                        "run_id": "inspection-1",
                        "status": "accepted",
                        "started_at": "2026-01-01T00:00:00Z",
                        "findings": [],
                    }
                ),
                encoding="utf-8",
            )
            dashboard = write_dashboard(root)
            content = dashboard.read_text(encoding="utf-8")
            self.assertIn("inspection-1/report.html", content)
            self.assertIn("accepted", content)


if __name__ == "__main__":
    unittest.main()
