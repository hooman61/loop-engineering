"""Shared test fixtures built only with the Python standard library."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from loop_engineering.models import (
    INSPECTOR_NAMES,
    CommandCheck,
    InspectionProfile,
    InspectorConfig,
    ReadOnlyPolicy,
    Severity,
)


def run_git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        capture_output=True,
        text=True,
    )


def initialize_git_repository(root: Path) -> None:
    """Create one clean Git commit without relying on global user settings."""

    run_git(root, "init")
    (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    run_git(
        root,
        "-c",
        "user.name=Loop Tests",
        "-c",
        "user.email=loop-tests@example.invalid",
        "commit",
        "-m",
        "baseline",
    )


def make_profile(
    root: Path,
    *,
    inspector: str = "backend",
    script: str = "raise SystemExit(0)",
    severity: Severity = Severity.MEDIUM,
) -> InspectionProfile:
    inspectors = {
        name: InspectorConfig(name=name, enabled=False, checks=())
        for name in INSPECTOR_NAMES
    }
    inspectors[inspector] = InspectorConfig(
        name=inspector,
        enabled=True,
        checks=(
            CommandCheck(
                id=f"{inspector}-check",
                title=f"{inspector.title()} check",
                command=(sys.executable, "-c", script),
                severity_on_failure=severity,
                priority=10,
            ),
        ),
    )
    return InspectionProfile(
        schema_version="1.0",
        project_id="test-product",
        project_root=root,
        inspectors=inspectors,
        read_only=ReadOnlyPolicy(
            require_git_repository=True,
            require_clean_start=True,
            fail_on_change=True,
        ),
    )

