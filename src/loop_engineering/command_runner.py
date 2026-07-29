"""Safe deterministic command execution for inspection sensors."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .models import CheckResult, CheckStatus, CommandCheck


_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)"
            r"(\s*[:=]\s*)[^\s,;]+"
        ),
        r"\1\2[REDACTED]",
    ),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\b"),
        "[REDACTED_JWT]",
    ),
)


def redact(text: str) -> str:
    """Remove common credential shapes from captured command output.

    Redaction is defense in depth, not permission to print secrets.  Sensor
    commands must still be configured to avoid verbose credential output.
    """

    value = text
    for pattern, replacement in _REDACTIONS:
        value = pattern.sub(replacement, value)
    return value


def _bounded_evidence(stdout: str, stderr: str, limit: int) -> str:
    """Create a deterministic, redacted, size-bounded evidence string."""

    parts: list[str] = []
    if stdout.strip():
        parts.append("STDOUT:\n" + stdout.strip())
    if stderr.strip():
        parts.append("STDERR:\n" + stderr.strip())
    value = redact("\n\n".join(parts))
    if not value:
        value = "Command produced no output."
    if len(value) > limit:
        omitted = len(value) - limit
        value = value[:limit] + f"\n...[{omitted} characters omitted]"
    return value


def _resolve_executable(argument: str) -> str | None:
    """Resolve executables consistently, including ``.cmd`` files on Windows."""

    candidate = Path(argument)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return str(candidate) if candidate.is_file() else None
    return shutil.which(argument)


def expand_runtime_tokens(
    command: tuple[str, ...], working_directory: Path | None = None
) -> tuple[str, ...]:
    """Expand portable runtime tokens without invoking a command shell."""

    project_python = sys.executable
    if working_directory is not None:
        candidates = (
            working_directory / ".venv" / "Scripts" / "python.exe",
            working_directory / ".venv" / "bin" / "python",
            working_directory / "venv" / "Scripts" / "python.exe",
            working_directory / "venv" / "bin" / "python",
        )
        project_python = str(
            next((path for path in candidates if path.is_file()), sys.executable)
        )
    replacements = {
        "{python}": sys.executable,
        "{project-python}": project_python,
    }
    return tuple(replacements.get(argument, argument) for argument in command)


class CommandRunner:
    """Execute configured checks without a command shell."""

    def __init__(self, project_root: Path, max_evidence_chars: int) -> None:
        self.project_root = project_root.resolve()
        self.max_evidence_chars = max_evidence_chars

    def run(self, inspector: str, check: CommandCheck) -> CheckResult:
        """Run one check and classify process failure separately from findings."""

        working_directory = (self.project_root / check.working_directory).resolve()
        if not working_directory.is_relative_to(self.project_root):
            return self._tool_error(
                inspector,
                check,
                "unsafe_path",
                "Working directory escaped project root.",
            )
        if not working_directory.is_dir():
            return self._tool_error(
                inspector,
                check,
                "missing_working_directory",
                f"Working directory does not exist: {working_directory}",
            )

        expanded_command = expand_runtime_tokens(check.command, working_directory)
        executable = _resolve_executable(expanded_command[0])
        if executable is None:
            return self._tool_error(
                inspector,
                check,
                "missing_executable",
                f"Executable was not found: {expanded_command[0]}",
            )

        command = (executable, *expanded_command[1:])
        environment = os.environ.copy()
        environment.setdefault("CI", "true")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=working_directory,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=check.timeout_seconds,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = int((time.monotonic() - started) * 1_000)
            stdout = (
                exc.stdout.decode("utf-8", "replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            stderr = (
                exc.stderr.decode("utf-8", "replace")
                if isinstance(exc.stderr, bytes)
                else (exc.stderr or "")
            )
            evidence = _bounded_evidence(stdout, stderr, self.max_evidence_chars)
            evidence += f"\nTimed out after {check.timeout_seconds} seconds."
            return CheckResult(
                inspector=inspector,
                check_id=check.id,
                title=check.title,
                status=CheckStatus.TOOL_ERROR,
                severity=check.severity_on_failure,
                priority=check.priority,
                command=check.command,
                working_directory=check.working_directory,
                exit_code=None,
                duration_ms=duration,
                evidence=evidence,
                error_kind="timeout",
            )
        except OSError as exc:
            return self._tool_error(inspector, check, "process_error", str(exc))

        duration = int((time.monotonic() - started) * 1_000)
        if completed.returncode in check.success_exit_codes:
            status = CheckStatus.PASSED
            error_kind = None
        elif completed.returncode in check.tool_error_exit_codes:
            status = CheckStatus.TOOL_ERROR
            error_kind = "configured_tool_error_exit_code"
        else:
            status = CheckStatus.FINDING
            error_kind = None
        return CheckResult(
            inspector=inspector,
            check_id=check.id,
            title=check.title,
            status=status,
            severity=check.severity_on_failure,
            priority=check.priority,
            command=check.command,
            working_directory=check.working_directory,
            exit_code=completed.returncode,
            duration_ms=duration,
            evidence=_bounded_evidence(
                completed.stdout, completed.stderr, self.max_evidence_chars
            ),
            error_kind=error_kind,
        )

    def _tool_error(
        self,
        inspector: str,
        check: CommandCheck,
        error_kind: str,
        message: str,
    ) -> CheckResult:
        """Build a uniform result for failures to start or execute a tool."""

        return CheckResult(
            inspector=inspector,
            check_id=check.id,
            title=check.title,
            status=CheckStatus.TOOL_ERROR,
            severity=check.severity_on_failure,
            priority=check.priority,
            command=check.command,
            working_directory=check.working_directory,
            exit_code=None,
            duration_ms=0,
            evidence=redact(message)[: self.max_evidence_chars],
            error_kind=error_kind,
        )
