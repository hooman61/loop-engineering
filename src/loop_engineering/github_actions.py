"""Generate a conservative GitHub Actions quality workflow from a profile."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from .models import ConfigurationError, InspectionProfile


CHECKOUT_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
SETUP_NODE_SHA = "49933ea5288caeca8642d1e84afbd3f7d6820020"
SETUP_PYTHON_SHA = "42375524e23c412d93fb67b49958b491fce71c38"
UPLOAD_ARTIFACT_SHA = "ea165f8d65b6e75b540449e92b4886f43607fa02"


def _job_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", value.lower())


def _shell_command(command: tuple[str, ...]) -> str:
    tokens = {"{python}", "{project-python}"}
    return shlex.join("python" if part in tokens else part for part in command)


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _dependency_steps(profile: InspectionProfile, working_directory: str) -> list[str]:
    directory = profile.project_root / working_directory
    lines: list[str] = []
    if (directory / "package-lock.json").is_file():
        lines.extend(
            [
                f"      - uses: actions/setup-node@{SETUP_NODE_SHA}",
                "        with:",
                "          node-version: '20'",
                "          cache: npm",
                "          cache-dependency-path: "
                + _quote(f"{working_directory}/package-lock.json"),
                "      - name: Install Node dependencies",
                f"        working-directory: {_quote(working_directory)}",
                "        run: npm ci",
            ]
        )
    requirements = directory / "requirements.txt"
    pyproject = directory / "pyproject.toml"
    if requirements.is_file() or pyproject.is_file():
        lines.extend(
            [
                f"      - uses: actions/setup-python@{SETUP_PYTHON_SHA}",
                "        with:",
                "          python-version: '3.12'",
                "          cache: pip",
                "          cache-dependency-path: "
                + _quote(
                    f"{working_directory}/"
                    + (
                        "requirements.txt"
                        if requirements.is_file()
                        else "pyproject.toml"
                    )
                ),
            ]
        )
        if requirements.is_file():
            lines.extend(
                [
                    "      - name: Install Python dependencies",
                    f"        working-directory: {_quote(working_directory)}",
                    "        run: python -m pip install -r requirements.txt",
                ]
            )
        else:
            lines.extend(
                [
                    "      - name: Install Python project",
                    f"        working-directory: {_quote(working_directory)}",
                    "        run: python -m pip install .",
                ]
            )
    return lines


def render_workflow(profile: InspectionProfile) -> str:
    """Return a self-contained, least-privilege workflow."""

    jobs: list[str] = []
    job_ids: list[str] = []
    for inspector in profile.inspectors.values():
        if not inspector.enabled:
            continue
        for check in inspector.checks:
            job_id = _job_id(f"{inspector.name}_{check.id}")
            job_ids.append(job_id)
            command = _shell_command(check.command)
            allowed = " ".join(str(code) for code in check.success_exit_codes)
            lines = [
                f"  {job_id}:",
                f"    name: {_quote(f'{inspector.name} · {check.title}')}",
                "    runs-on: ubuntu-latest",
                "    timeout-minutes: 30",
                "    steps:",
                f"      - uses: actions/checkout@{CHECKOUT_SHA}",
            ]
            lines.extend(_dependency_steps(profile, check.working_directory))
            lines.extend(
                [
                    "      - name: Run deterministic check",
                    f"        working-directory: {_quote(check.working_directory)}",
                    "        shell: bash",
                    "        run: |",
                    "          set +e",
                    f"          {command} 2>&1 | tee \"$GITHUB_WORKSPACE/{job_id}.log\"",
                    "          status=${PIPESTATUS[0]}",
                    f"          case \" {allowed} \" in",
                    "            *\" $status \"*) exit 0 ;;",
                    "            *) exit \"$status\" ;;",
                    "          esac",
                    "      - name: Upload evidence",
                    "        if: always()",
                    f"        uses: actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}",
                    "        with:",
                    f"          name: {_quote(f'loop-engineering-{job_id}')}",
                    f"          path: {_quote(f'{job_id}.log')}",
                    "          if-no-files-found: warn",
                    "          retention-days: 14",
                ]
            )
            jobs.append("\n".join(lines))

    if not jobs:
        raise ConfigurationError("cannot generate workflow: no inspectors are enabled")
    needs = ", ".join(job_ids)
    aggregate = "\n".join(
        [
            "  quality_gate:",
            "    name: Quality gate",
            "    if: always()",
            f"    needs: [{needs}]",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Enforce specialist results",
            "        env:",
            "          NEEDS_JSON: ${{ toJson(needs) }}",
            "        shell: bash",
            "        run: |",
            "          python - <<'PY'",
            "          import json, os, sys",
            "          results = json.loads(os.environ['NEEDS_JSON'])",
            "          failed = {k: v['result'] for k, v in results.items()",
            "                    if v['result'] != 'success'}",
            "          print(json.dumps(results, indent=2))",
            "          sys.exit(1 if failed else 0)",
            "          PY",
        ]
    )
    return "\n".join(
        [
            "# Generated by Loop Engineering. Review before committing.",
            "name: Loop Engineering quality gates",
            "",
            "on:",
            "  pull_request:",
            "  workflow_dispatch:",
            "",
            "permissions:",
            "  contents: read",
            "",
            "concurrency:",
            "  group: loop-engineering-${{ github.workflow }}-${{ github.ref }}",
            "  cancel-in-progress: true",
            "",
            "jobs:",
            *jobs,
            aggregate,
            "",
        ]
    )


def write_workflow(
    profile: InspectionProfile, destination: Path, *, force: bool = False
) -> Path:
    """Write a generated workflow without silently replacing existing CI."""

    destination = destination.resolve()
    if destination.exists() and not force:
        raise ConfigurationError(
            f"workflow already exists: {destination}; use --force to replace it"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_workflow(profile), encoding="utf-8")
    return destination
