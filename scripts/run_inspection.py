#!/usr/bin/env python3
"""Bootstrap the stage-one CLI directly from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from loop_engineering.cli import main  # noqa: E402

raise SystemExit(main())

