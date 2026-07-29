"""Conservative project detection and portable profile generation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ConfigurationError


@dataclass(frozen=True, slots=True)
class Detection:
    """Detected stack and generated inspector configuration."""

    project_id: str
    technologies: tuple[str, ...]
    inspectors: dict[str, dict[str, Any]]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug or not slug[0].isalpha():
        slug = f"project-{slug}" if slug else "project"
    return slug


def _check(
    check_id: str,
    title: str,
    command: list[str],
    *,
    working_directory: str = ".",
    timeout: int = 300,
    severity: str = "medium",
    priority: int = 0,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "command": command,
        "working_directory": working_directory,
        "timeout_seconds": timeout,
        "success_exit_codes": [0],
        "tool_error_exit_codes": [],
        "severity_on_failure": severity,
        "priority": priority,
    }


def _relative(directory: Path, root: Path) -> str:
    value = directory.relative_to(root).as_posix()
    return value if value else "."


def _package_candidates(root: Path) -> list[Path]:
    candidates = [root / "package.json"]
    candidates.extend(root / name / "package.json" for name in ("frontend", "client", "web"))
    return [path for path in candidates if path.is_file()]


def detect_project(root: Path) -> Detection:
    """Detect declared, deterministic checks without executing project code."""

    root = root.resolve()
    if not root.is_dir():
        raise ConfigurationError(f"project directory does not exist: {root}")

    grouped: dict[str, list[dict[str, Any]]] = {
        "frontend": [],
        "backend": [],
        "database": [],
        "integration": [],
    }
    technologies: set[str] = set()

    for package_path in _package_candidates(root):
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            scripts = {}
        directory = _relative(package_path.parent, root)
        technologies.add("node")
        if "lint" in scripts:
            grouped["frontend"].append(
                _check(
                    "frontend-lint",
                    "Frontend lint",
                    ["npm", "run", "lint"],
                    working_directory=directory,
                    severity="high",
                    priority=80,
                )
            )
        if "test" in scripts and "no test specified" not in str(scripts["test"]).lower():
            grouped["frontend"].append(
                _check(
                    "frontend-tests",
                    "Frontend tests",
                    ["npm", "test"],
                    working_directory=directory,
                    timeout=600,
                    severity="high",
                    priority=90,
                )
            )
        # Build scripts are intentionally not enabled automatically: unlike
        # lint and tests they commonly write bundles inside the target tree.
        break

    manage = root / "manage.py"
    if not manage.is_file():
        matches = [root / name / "manage.py" for name in ("backend", "server", "api")]
        manage = next((path for path in matches if path.is_file()), manage)
    if manage.is_file():
        technologies.update(("python", "django"))
        directory = _relative(manage.parent, root)
        grouped["backend"].extend(
            [
                _check(
                    "django-system-check",
                    "Django deployment checks",
                    ["{project-python}", "manage.py", "check", "--deploy"],
                    working_directory=directory,
                    severity="high",
                    priority=100,
                ),
                _check(
                    "django-tests",
                    "Django test suite",
                    ["{project-python}", "manage.py", "test"],
                    working_directory=directory,
                    timeout=1200,
                    severity="high",
                    priority=95,
                ),
            ]
        )
        grouped["database"].append(
            _check(
                "django-migration-drift",
                "Django migration drift",
                [
                    "{project-python}",
                    "manage.py",
                    "makemigrations",
                    "--check",
                    "--dry-run",
                ],
                working_directory=directory,
                severity="critical",
                priority=110,
            )
        )
    elif (root / "pyproject.toml").is_file() or (root / "pytest.ini").is_file():
        technologies.add("python")
        grouped["backend"].append(
            _check(
                "python-tests",
                "Python test suite",
                ["{project-python}", "-m", "pytest"],
                timeout=1200,
                severity="high",
                priority=90,
            )
        )

    inspectors = {
        name: {"enabled": bool(checks), "checks": checks}
        for name, checks in grouped.items()
    }
    return Detection(_slug(root.name), tuple(sorted(technologies)), inspectors)


def write_profile(
    root: Path,
    destination: Path | None = None,
    *,
    force: bool = False,
) -> tuple[Path, Detection]:
    """Generate a portable YAML profile rooted relative to its project."""

    try:
        import yaml
    except ImportError as exc:
        raise ConfigurationError(
            "PyYAML is required for profile generation; install the package dependencies"
        ) from exc
    root = root.resolve()
    detection = detect_project(root)
    destination = destination or root / ".loop-engineering" / "inspection.yaml"
    destination = destination.resolve()
    if destination.exists() and not force:
        raise ConfigurationError(
            f"profile already exists: {destination}; use --force to replace it"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    relative_root = Path(os.path.relpath(root, destination.parent)).as_posix()
    document = {
        "schema_version": "1.0",
        "project": {"id": detection.project_id, "root": relative_root or "."},
        "read_only": {
            "require_git_repository": (root / ".git").exists(),
            "require_clean_start": False,
            "fail_on_change": True,
        },
        "stop_on_inspector_error": True,
        "max_evidence_chars": 4000,
        "inspectors": detection.inspectors,
    }
    destination.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return destination, detection
