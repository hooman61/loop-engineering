"""Read-only Git snapshots used to prove product repository immutability."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from .models import ConfigurationError, RepositorySnapshot


def _git(project_root: Path, *arguments: str, text: bool = True) -> str | bytes:
    executable = shutil.which("git")
    if executable is None:
        raise OSError("git executable was not found")
    completed = subprocess.run(
        (executable, "-C", str(project_root), *arguments),
        capture_output=True,
        text=text,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        stderr = (
            completed.stderr
            if text
            else completed.stderr.decode("utf-8", "replace")
        )
        raise OSError(stderr.strip() or f"git exited with {completed.returncode}")
    return completed.stdout


def capture_repository_snapshot(
    project_root: Path, *, require_git_repository: bool
) -> RepositorySnapshot:
    """Capture commit, status, tracked diff, and untracked content fingerprints."""

    try:
        repository_root = str(
            _git(project_root, "rev-parse", "--show-toplevel")
        ).strip()
        commit = str(_git(project_root, "rev-parse", "HEAD")).strip()
        status_text = str(
            _git(project_root, "status", "--porcelain=v1", "--untracked-files=all")
        )
        status_lines = tuple(sorted(line for line in status_text.splitlines() if line))
        diff = bytes(
            _git(
                project_root,
                "diff",
                "--no-ext-diff",
                "--binary",
                "HEAD",
                "--",
                text=False,
            )
        )
        untracked_raw = bytes(
            _git(
                project_root,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                text=False,
            )
        )
    except OSError as exc:
        if require_git_repository:
            raise ConfigurationError(
                f"project root must be an accessible Git repository: {exc}"
            ) from exc
        return RepositorySnapshot(
            available=False,
            repository_root=None,
            commit=None,
            status_lines=(),
            content_fingerprint=None,
            warning=f"Git guard unavailable: {exc}",
        )

    digest = hashlib.sha256()
    digest.update(commit.encode("utf-8"))
    digest.update(b"\0")
    digest.update(diff)
    repository_path = Path(repository_root)
    for raw_name in sorted(name for name in untracked_raw.split(b"\0") if name):
        relative = Path(raw_name.decode("utf-8", "surrogateescape"))
        digest.update(raw_name)
        digest.update(b"\0")
        candidate = repository_path / relative
        try:
            if candidate.is_file():
                with candidate.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)
        except OSError as exc:
            digest.update(f"UNREADABLE:{exc}".encode("utf-8", "replace"))

    return RepositorySnapshot(
        available=True,
        repository_root=repository_root,
        commit=commit,
        status_lines=status_lines,
        content_fingerprint=digest.hexdigest(),
    )


def repository_changed(
    before: RepositorySnapshot, after: RepositorySnapshot
) -> bool:
    """Return true when an inspected Git repository changed during a run."""

    if not before.available or not after.available:
        return False
    return before.content_fingerprint != after.content_fingerprint
