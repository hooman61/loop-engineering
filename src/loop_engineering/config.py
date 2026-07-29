"""Load and validate stage-one inspection profiles.

JSON is supported with the Python standard library.  YAML and full JSON Schema
validation are enabled when the declared runtime dependencies are installed.
Independent semantic validation is always applied so unsafe command strings or
paths are rejected even if schema validation is unavailable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from .models import (
    INSPECTOR_NAMES,
    CommandCheck,
    ConfigurationError,
    InspectionProfile,
    InspectorConfig,
    ReadOnlyPolicy,
    Severity,
)


IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPOSITORY_ROOT / "schemas" / "inspection-profile.schema.json"


def _installed_schema() -> Path:
    """Locate the schema in a source checkout or an installed wheel."""

    if DEFAULT_SCHEMA.is_file():
        return DEFAULT_SCHEMA
    candidate = Path(sys.prefix) / "schemas" / "inspection-profile.schema.json"
    if candidate.is_file():
        return candidate
    raise ConfigurationError(
        "inspection profile schema is missing; reinstall loop-engineering"
    )


def _load_document(path: Path) -> dict[str, Any]:
    """Load a JSON or YAML mapping from ``path``."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"cannot read profile: {path}: {exc}") from exc

    if path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"invalid profile syntax: {exc}") from exc
    else:
        try:
            import yaml
        except ImportError as exc:
            raise ConfigurationError(
                "PyYAML is required for YAML profiles; install project "
                "dependencies or provide an equivalent JSON profile"
            ) from exc
        try:
            value = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"invalid profile syntax: {exc}") from exc

    if not isinstance(value, dict):
        raise ConfigurationError("profile root must be an object")
    return value


def _validate_with_json_schema(document: dict[str, Any], schema_path: Path) -> None:
    """Validate with Draft 2020-12 when jsonschema is available."""

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"cannot load profile schema: {exc}") from exc

    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            location = "$" + "".join(f"[{part!r}]" for part in error.absolute_path)
            rendered.append(f"{location}: {error.message}")
        raise ConfigurationError("profile schema errors:\n- " + "\n- ".join(rendered))


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be an object")
    return value


def _parse_check(raw: dict[str, Any], inspector: str) -> CommandCheck:
    check_id = raw.get("id")
    if not isinstance(check_id, str) or not IDENTIFIER.fullmatch(check_id):
        raise ConfigurationError(
            f"inspectors.{inspector}.checks[].id must be a kebab-case identifier"
        )

    title = raw.get("title")
    if not isinstance(title, str) or len(title.strip()) < 3:
        raise ConfigurationError(f"check {check_id}: title must contain 3 characters")

    command = raw.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise ConfigurationError(
            f"check {check_id}: command must be a non-empty array of arguments"
        )

    working_directory = raw.get("working_directory", ".")
    if not isinstance(working_directory, str) or not working_directory:
        raise ConfigurationError(f"check {check_id}: invalid working_directory")
    path = Path(working_directory)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigurationError(
            f"check {check_id}: working_directory must remain inside project root"
        )

    try:
        severity = Severity(raw.get("severity_on_failure", "medium"))
    except ValueError as exc:
        raise ConfigurationError(f"check {check_id}: invalid severity") from exc

    timeout = raw.get("timeout_seconds", 300)
    priority = raw.get("priority", 0)
    success_codes = raw.get("success_exit_codes", [0])
    tool_error_codes = raw.get("tool_error_exit_codes", [])
    if not isinstance(timeout, int) or not 1 <= timeout <= 3_600:
        raise ConfigurationError(f"check {check_id}: timeout must be 1..3600")
    if not isinstance(priority, int) or not -1_000 <= priority <= 1_000:
        raise ConfigurationError(f"check {check_id}: priority must be -1000..1000")
    if (
        not isinstance(success_codes, list)
        or not success_codes
        or any(not isinstance(code, int) for code in success_codes)
    ):
        raise ConfigurationError(f"check {check_id}: invalid success_exit_codes")
    if not isinstance(tool_error_codes, list) or any(
        not isinstance(code, int) for code in tool_error_codes
    ):
        raise ConfigurationError(f"check {check_id}: invalid tool_error_exit_codes")
    if len(set(success_codes)) != len(success_codes):
        raise ConfigurationError(f"check {check_id}: duplicate success_exit_codes")
    if len(set(tool_error_codes)) != len(tool_error_codes):
        raise ConfigurationError(f"check {check_id}: duplicate tool_error_exit_codes")
    if set(success_codes) & set(tool_error_codes):
        raise ConfigurationError(
            f"check {check_id}: success and tool-error exit codes must be disjoint"
        )

    return CommandCheck(
        id=check_id,
        title=title.strip(),
        command=tuple(command),
        working_directory=working_directory,
        timeout_seconds=timeout,
        success_exit_codes=tuple(success_codes),
        tool_error_exit_codes=tuple(tool_error_codes),
        severity_on_failure=severity,
        priority=priority,
    )


def parse_profile(
    document: dict[str, Any], *, base_directory: Path
) -> InspectionProfile:
    """Convert a validated mapping into immutable domain models."""

    if document.get("schema_version") != "1.0":
        raise ConfigurationError("schema_version must equal '1.0'")

    project = _require_mapping(document.get("project"), "project")
    project_id = project.get("id")
    if not isinstance(project_id, str) or not IDENTIFIER.fullmatch(project_id):
        raise ConfigurationError("project.id must be a kebab-case identifier")

    root_value = project.get("root")
    if not isinstance(root_value, str) or not root_value:
        raise ConfigurationError("project.root must be a path string")
    root = Path(root_value).expanduser()
    if not root.is_absolute():
        root = base_directory / root
    root = root.resolve()
    if not root.is_dir():
        raise ConfigurationError(f"project.root is not a directory: {root}")

    raw_inspectors = _require_mapping(document.get("inspectors"), "inspectors")
    unknown = sorted(set(raw_inspectors) - set(INSPECTOR_NAMES))
    if unknown:
        raise ConfigurationError(f"unknown inspectors: {', '.join(unknown)}")

    inspectors: dict[str, InspectorConfig] = {}
    for name in INSPECTOR_NAMES:
        raw = _require_mapping(raw_inspectors.get(name, {}), f"inspectors.{name}")
        enabled = raw.get("enabled", False)
        if not isinstance(enabled, bool):
            raise ConfigurationError(f"inspectors.{name}.enabled must be boolean")
        checks_value = raw.get("checks", [])
        if not isinstance(checks_value, list):
            raise ConfigurationError(f"inspectors.{name}.checks must be an array")
        checks = tuple(
            _parse_check(_require_mapping(item, f"inspectors.{name}.check"), name)
            for item in checks_value
        )
        if enabled and not checks:
            raise ConfigurationError(
                f"inspectors.{name} is enabled but defines no checks"
            )
        if len({check.id for check in checks}) != len(checks):
            raise ConfigurationError(f"inspectors.{name} contains duplicate check ids")
        inspectors[name] = InspectorConfig(name=name, enabled=enabled, checks=checks)

    read_only_raw = _require_mapping(document.get("read_only", {}), "read_only")
    read_only = ReadOnlyPolicy(
        require_git_repository=read_only_raw.get("require_git_repository", True),
        require_clean_start=read_only_raw.get("require_clean_start", False),
        fail_on_change=read_only_raw.get("fail_on_change", True),
    )
    if any(
        not isinstance(value, bool)
        for value in (
            read_only.require_git_repository,
            read_only.require_clean_start,
            read_only.fail_on_change,
        )
    ):
        raise ConfigurationError("read_only policy values must be boolean")
    if not read_only.fail_on_change:
        raise ConfigurationError("stage one requires read_only.fail_on_change=true")

    stop_on_error = document.get("stop_on_inspector_error", True)
    max_evidence = document.get("max_evidence_chars", 4_000)
    if not isinstance(stop_on_error, bool):
        raise ConfigurationError("stop_on_inspector_error must be boolean")
    if not stop_on_error:
        raise ConfigurationError("stage one requires stop_on_inspector_error=true")
    if not isinstance(max_evidence, int) or not 256 <= max_evidence <= 100_000:
        raise ConfigurationError("max_evidence_chars must be 256..100000")

    return InspectionProfile(
        schema_version="1.0",
        project_id=project_id,
        project_root=root,
        inspectors=inspectors,
        read_only=read_only,
        stop_on_inspector_error=stop_on_error,
        max_evidence_chars=max_evidence,
    )


def load_profile(path: Path, schema_path: Path | None = None) -> InspectionProfile:
    """Load, schema-check, and semantically validate a profile file."""

    resolved = path.resolve()
    document = _load_document(resolved)
    _validate_with_json_schema(document, (schema_path or _installed_schema()).resolve())
    return parse_profile(document, base_directory=resolved.parent)
