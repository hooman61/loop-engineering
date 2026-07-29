"""Deterministic normalization and target selection."""

from __future__ import annotations

import hashlib

from .models import CheckStatus, Finding, InspectorResult, Severity


SEVERITY_WEIGHT = {
    Severity.INFO: 1,
    Severity.LOW: 2,
    Severity.MEDIUM: 3,
    Severity.HIGH: 4,
    Severity.CRITICAL: 5,
}


def _fingerprint(project_id: str, inspector: str, check_id: str) -> str:
    """Return an identifier stable across repeated runs of the same check."""

    material = f"{project_id}\0{inspector}\0{check_id}".encode()
    return hashlib.sha256(material).hexdigest()[:20]


def normalize_findings(
    project_id: str, inspector_results: list[InspectorResult]
) -> list[Finding]:
    """Normalize failed checks and apply one stable total ordering."""

    findings: list[Finding] = []
    for result in inspector_results:
        for check in result.checks:
            if check.status is not CheckStatus.FINDING:
                continue
            score = SEVERITY_WEIGHT[check.severity] * 10_000 + check.priority
            findings.append(
                Finding(
                    fingerprint=_fingerprint(
                        project_id, result.inspector, check.check_id
                    ),
                    project_id=project_id,
                    inspector=result.inspector,
                    check_id=check.check_id,
                    title=check.title,
                    severity=check.severity,
                    priority=check.priority,
                    score=score,
                    evidence=check.evidence,
                    command=check.command,
                    working_directory=check.working_directory,
                )
            )

    return sorted(
        findings,
        key=lambda finding: (
            -finding.score,
            finding.inspector,
            finding.check_id,
            finding.fingerprint,
        ),
    )


def select_one_target(findings: list[Finding]) -> Finding | None:
    """Select one bounded target without model judgment."""

    return findings[0] if findings else None

