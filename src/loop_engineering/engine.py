"""Application service for one complete read-only inspection iteration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from .graph_runtime import run_inspection_graph
from .inspectors import build_inspectors
from .models import (
    ConfigurationError,
    InspectionOutcome,
    InspectionProfile,
    InspectorStatus,
)
from .reporting import write_reports
from .repository import capture_repository_snapshot, repository_changed


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _run_id(started: datetime) -> str:
    timestamp = started.strftime("%Y%m%dT%H%M%SZ")
    return f"inspection-{timestamp}-{uuid.uuid4().hex[:8]}"


class InspectionEngine:
    """Coordinate preflight, parallel sensing, control, and read-only proof."""

    def __init__(self, profile: InspectionProfile) -> None:
        self.profile = profile

    def run(self, *, runtime: str = "auto") -> InspectionOutcome:
        """Execute one bounded observation cycle without product actuation."""

        started = _utc_now()
        before = capture_repository_snapshot(
            self.profile.project_root,
            require_git_repository=self.profile.read_only.require_git_repository,
        )
        if self.profile.read_only.require_clean_start and before.status_lines:
            raise ConfigurationError(
                "read-only policy requires a clean target repository at start"
            )

        results, findings, selected, runtime_name = run_inspection_graph(
            self.profile.project_id,
            build_inspectors(self.profile),
            runtime,
        )
        after = capture_repository_snapshot(
            self.profile.project_root,
            require_git_repository=self.profile.read_only.require_git_repository,
        )

        stop_reasons: list[str] = []
        warnings: list[str] = []
        if before.warning:
            warnings.append(before.warning)
        if after.warning and after.warning != before.warning:
            warnings.append(after.warning)

        if self.profile.read_only.fail_on_change and repository_changed(before, after):
            stop_reasons.append(
                "The inspected repository changed during a read-only run. "
                "No automatic cleanup was attempted."
            )
        if self.profile.stop_on_inspector_error and any(
            result.status is InspectorStatus.ERROR for result in results
        ):
            stop_reasons.append(
                "At least one inspector failed to produce trustworthy evidence."
            )

        if stop_reasons:
            status = "aborted_safely"
        elif findings:
            status = "needs_human_input"
        else:
            status = "accepted"

        return InspectionOutcome(
            run_id=_run_id(started),
            project_id=self.profile.project_id,
            status=status,
            runtime=runtime_name,
            started_at=started.isoformat(),
            completed_at=_utc_now().isoformat(),
            inspector_results=results,
            findings=findings,
            selected_target=selected,
            repository_before=before,
            repository_after=after,
            stop_reasons=stop_reasons,
            warnings=warnings,
        )

    def run_and_write(
        self, output_root: Path, *, runtime: str = "auto"
    ) -> tuple[InspectionOutcome, Path]:
        """Run an inspection and persist its reports outside the target repo."""

        output = output_root.resolve()
        target = self.profile.project_root.resolve()
        if output == target or output.is_relative_to(target):
            raise ConfigurationError(
                "report output must be outside the inspected product repository"
            )
        outcome = self.run(runtime=runtime)
        return outcome, write_reports(outcome, output)

