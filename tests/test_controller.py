from __future__ import annotations

import unittest

from loop_engineering.controller import normalize_findings, select_one_target
from loop_engineering.models import (
    CheckResult,
    CheckStatus,
    InspectorResult,
    InspectorStatus,
    Severity,
)


def result(inspector: str, check_id: str, severity: Severity, priority: int):
    check = CheckResult(
        inspector=inspector,
        check_id=check_id,
        title=check_id,
        status=CheckStatus.FINDING,
        severity=severity,
        priority=priority,
        command=("tool",),
        working_directory=".",
        exit_code=1,
        duration_ms=1,
        evidence="failure",
    )
    return InspectorResult(
        inspector=inspector,
        status=InspectorStatus.FINDINGS,
        checks=(check,),
    )


class ControllerTests(unittest.TestCase):
    def test_selection_is_severity_first_and_stable(self) -> None:
        inputs = [
            result("frontend", "low-check", Severity.LOW, 999),
            result("database", "critical-check", Severity.CRITICAL, -100),
            result("backend", "high-check", Severity.HIGH, 50),
        ]
        first = normalize_findings("product", inputs)
        second = normalize_findings("product", list(reversed(inputs)))
        self.assertEqual(
            [finding.fingerprint for finding in first],
            [finding.fingerprint for finding in second],
        )
        selected = select_one_target(first)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.check_id, "critical-check")


if __name__ == "__main__":
    unittest.main()

