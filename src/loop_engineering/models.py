"""Typed domain models for the read-only inspection loop.

The models in this module are deliberately independent from LangGraph.  This
keeps the control contract testable without a workflow runtime and prevents a
framework-specific state representation from becoming the domain model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


INSPECTOR_NAMES = ("frontend", "backend", "database", "integration")


class ConfigurationError(ValueError):
    """Raised when a profile violates the inspection contract."""


class Severity(StrEnum):
    """Portable severity levels ordered by the controller, not by the enum."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(StrEnum):
    """Outcome of one deterministic command check."""

    PASSED = "passed"
    FINDING = "finding"
    TOOL_ERROR = "tool_error"
    SKIPPED = "skipped"


class InspectorStatus(StrEnum):
    """Aggregate status for one specialist inspector."""

    PASSED = "passed"
    FINDINGS = "findings"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class CommandCheck:
    """One shell-free, deterministic sensor command.

    ``command`` is an argument vector rather than a string.  The executor calls
    it with ``shell=False`` so configuration cannot silently introduce pipes,
    redirections, command substitution, or shell-specific behavior.
    """

    id: str
    title: str
    command: tuple[str, ...]
    working_directory: str = "."
    timeout_seconds: int = 300
    success_exit_codes: tuple[int, ...] = (0,)
    tool_error_exit_codes: tuple[int, ...] = ()
    severity_on_failure: Severity = Severity.MEDIUM
    priority: int = 0


@dataclass(frozen=True, slots=True)
class InspectorConfig:
    """Configuration for one domain-specific inspector."""

    name: str
    enabled: bool
    checks: tuple[CommandCheck, ...]


@dataclass(frozen=True, slots=True)
class ReadOnlyPolicy:
    """Repository invariants enforced before and after inspection."""

    require_git_repository: bool = True
    require_clean_start: bool = False
    fail_on_change: bool = True


@dataclass(frozen=True, slots=True)
class InspectionProfile:
    """Validated configuration for one product inspection."""

    schema_version: str
    project_id: str
    project_root: Path
    inspectors: dict[str, InspectorConfig]
    read_only: ReadOnlyPolicy
    stop_on_inspector_error: bool = True
    max_evidence_chars: int = 4_000


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Evidence captured from one command invocation."""

    inspector: str
    check_id: str
    title: str
    status: CheckStatus
    severity: Severity
    priority: int
    command: tuple[str, ...]
    working_directory: str
    exit_code: int | None
    duration_ms: int
    evidence: str
    error_kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        value = asdict(self)
        value["status"] = self.status.value
        value["severity"] = self.severity.value
        value["command"] = list(self.command)
        return value


@dataclass(frozen=True, slots=True)
class InspectorResult:
    """Aggregate output of a specialist inspector."""

    inspector: str
    status: InspectorStatus
    checks: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""

        return {
            "inspector": self.inspector,
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class Finding:
    """Normalized, controller-ready representation of a failed check."""

    fingerprint: str
    project_id: str
    inspector: str
    check_id: str
    title: str
    severity: Severity
    priority: int
    score: int
    evidence: str
    command: tuple[str, ...]
    working_directory: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable finding."""

        value = asdict(self)
        value["severity"] = self.severity.value
        value["command"] = list(self.command)
        return value


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Git-backed fingerprint used to detect product mutations."""

    available: bool
    repository_root: str | None
    commit: str | None
    status_lines: tuple[str, ...]
    content_fingerprint: str | None
    warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return snapshot metadata without repository file contents."""

        value = asdict(self)
        value["status_lines"] = list(self.status_lines)
        return value


@dataclass(slots=True)
class InspectionOutcome:
    """Complete result returned by the engine before report persistence."""

    run_id: str
    project_id: str
    status: str
    runtime: str
    started_at: str
    completed_at: str
    inspector_results: list[InspectorResult]
    findings: list[Finding]
    selected_target: Finding | None
    repository_before: RepositorySnapshot
    repository_after: RepositorySnapshot
    stop_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical machine-readable run report."""

        return {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "project_id": self.project_id,
            "status": self.status,
            "runtime": self.runtime,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "inspectors": [result.to_dict() for result in self.inspector_results],
            "findings": [finding.to_dict() for finding in self.findings],
            "selected_target": (
                self.selected_target.to_dict() if self.selected_target else None
            ),
            "repository_guard": {
                "before": self.repository_before.to_dict(),
                "after": self.repository_after.to_dict(),
            },
            "stop_reasons": self.stop_reasons,
            "warnings": self.warnings,
        }
