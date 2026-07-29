"""Specialist read-only inspectors built on deterministic command sensors."""

from __future__ import annotations

from .command_runner import CommandRunner
from .models import (
    CheckStatus,
    InspectionProfile,
    InspectorConfig,
    InspectorResult,
    InspectorStatus,
)


class SpecialistInspector:
    """Run all configured checks for exactly one engineering domain.

    Domain specialization resides in the versioned check configuration.  The
    execution policy remains shared so frontend, backend, database, and
    integration evidence receive identical safety and classification rules.
    """

    def __init__(
        self,
        profile: InspectionProfile,
        config: InspectorConfig,
        runner: CommandRunner | None = None,
    ) -> None:
        self.profile = profile
        self.config = config
        self.runner = runner or CommandRunner(
            profile.project_root, profile.max_evidence_chars
        )

    def inspect(self) -> InspectorResult:
        """Execute the inspector and return stable, structured evidence."""

        if not self.config.enabled:
            return InspectorResult(
                inspector=self.config.name,
                status=InspectorStatus.SKIPPED,
                checks=(),
            )

        results = []
        for check in self.config.checks:
            result = self.runner.run(self.config.name, check)
            results.append(result)
            if (
                result.status is CheckStatus.TOOL_ERROR
                and self.profile.stop_on_inspector_error
            ):
                break

        statuses = {result.status for result in results}
        if CheckStatus.TOOL_ERROR in statuses:
            status = InspectorStatus.ERROR
        elif CheckStatus.FINDING in statuses:
            status = InspectorStatus.FINDINGS
        else:
            status = InspectorStatus.PASSED

        return InspectorResult(
            inspector=self.config.name,
            status=status,
            checks=tuple(results),
        )


def build_inspectors(profile: InspectionProfile) -> dict[str, SpecialistInspector]:
    """Create the four named stage-one inspectors in deterministic order."""

    return {
        name: SpecialistInspector(profile, profile.inspectors[name])
        for name in profile.inspectors
    }

