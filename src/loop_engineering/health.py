"""Environment preflight for a configured inspection profile."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .command_runner import expand_runtime_tokens
from .models import InspectionProfile
from .paths import default_output_root


def diagnose(profile: InspectionProfile, output_root: Path | None = None) -> dict[str, Any]:
    """Return structured readiness evidence without executing project checks."""

    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    output = (output_root or default_output_root(profile.project_id)).resolve()
    target = profile.project_root.resolve()
    safe_output = output != target and not output.is_relative_to(target)
    add(
        "report-output",
        "ok" if safe_output else "error",
        str(output) if safe_output else "output must be outside the target repository",
    )
    enabled = [item for item in profile.inspectors.values() if item.enabled]
    add(
        "enabled-inspectors",
        "ok" if enabled else "error",
        f"{len(enabled)} inspector(s) enabled",
    )
    for inspector in enabled:
        for check in inspector.checks:
            working = (target / check.working_directory).resolve()
            add(
                f"{inspector.name}/{check.id}/working-directory",
                "ok" if working.is_dir() and working.is_relative_to(target) else "error",
                str(working),
            )
            executable = expand_runtime_tokens(check.command, working)[0]
            found = Path(executable).is_file() or shutil.which(executable) is not None
            add(
                f"{inspector.name}/{check.id}/executable",
                "ok" if found else "error",
                executable,
            )
    if profile.read_only.require_git_repository:
        add(
            "git",
            "ok" if shutil.which("git") else "error",
            "required by read-only policy",
        )
    errors = sum(item["status"] == "error" for item in checks)
    return {
        "status": "ready" if errors == 0 else "not_ready",
        "project_id": profile.project_id,
        "project_root": str(target),
        "output_root": str(output),
        "errors": errors,
        "checks": checks,
    }
