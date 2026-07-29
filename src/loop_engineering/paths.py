"""Portable filesystem locations for local Loop Engineering state."""

from __future__ import annotations

import os
from pathlib import Path


def state_root() -> Path:
    """Return the per-user state directory without touching the filesystem."""

    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "loop-engineering"
    if os.environ.get("XDG_STATE_HOME"):
        return Path(os.environ["XDG_STATE_HOME"]) / "loop-engineering"
    return Path.home() / ".local" / "state" / "loop-engineering"


def default_output_root(project_id: str) -> Path:
    """Return the default report root for a project."""

    return state_root() / "runs" / project_id
