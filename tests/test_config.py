from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_engineering.config import parse_profile
from loop_engineering.models import ConfigurationError


class ProfileValidationTests(unittest.TestCase):
    def base_document(self, root: Path) -> dict:
        disabled = {"enabled": False, "checks": []}
        return {
            "schema_version": "1.0",
            "project": {"id": "test-product", "root": str(root)},
            "read_only": {
                "require_git_repository": True,
                "require_clean_start": False,
                "fail_on_change": True,
            },
            "stop_on_inspector_error": True,
            "max_evidence_chars": 4000,
            "inspectors": {
                "frontend": dict(disabled),
                "backend": dict(disabled),
                "database": dict(disabled),
                "integration": dict(disabled),
            },
        }

    def test_rejects_shell_command_string(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = self.base_document(Path(directory))
            document["inspectors"]["backend"] = {
                "enabled": True,
                "checks": [
                    {
                        "id": "django-check",
                        "title": "Django check",
                        "command": "python manage.py check && echo unsafe",
                    }
                ],
            }
            with self.assertRaisesRegex(ConfigurationError, "array of arguments"):
                parse_profile(document, base_directory=Path(directory))

    def test_rejects_working_directory_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = self.base_document(Path(directory))
            document["inspectors"]["backend"] = {
                "enabled": True,
                "checks": [
                    {
                        "id": "django-check",
                        "title": "Django check",
                        "command": ["python", "manage.py", "check"],
                        "working_directory": "../outside",
                    }
                ],
            }
            with self.assertRaisesRegex(ConfigurationError, "project root"):
                parse_profile(document, base_directory=Path(directory))

    def test_stage_one_guard_cannot_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = self.base_document(Path(directory))
            document["read_only"]["fail_on_change"] = False
            with self.assertRaisesRegex(ConfigurationError, "fail_on_change=true"):
                parse_profile(document, base_directory=Path(directory))

    def test_rejects_overlapping_exit_code_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = self.base_document(Path(directory))
            document["inspectors"]["frontend"] = {
                "enabled": True,
                "checks": [
                    {
                        "id": "structured-scan",
                        "title": "Structured scan",
                        "command": ["scanner"],
                        "success_exit_codes": [0, 2],
                        "tool_error_exit_codes": [2],
                    }
                ],
            }
            with self.assertRaisesRegex(ConfigurationError, "must be disjoint"):
                parse_profile(document, base_directory=Path(directory))


if __name__ == "__main__":
    unittest.main()
