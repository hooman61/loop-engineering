"""Command-line product for reusable, read-only quality inspection."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .config import load_profile
from .engine import InspectionEngine
from .github_actions import write_workflow
from .graph_runtime import RuntimeUnavailableError
from .health import diagnose
from .models import ConfigurationError
from .onboarding import write_profile
from .paths import default_output_root
from .reporting import write_dashboard


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loop-engineering",
        description="Portable, deterministic quality loops for software projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="detect a project and create a profile")
    init.add_argument("project", type=Path, nargs="?", default=Path("."))
    init.add_argument("--profile", type=Path, help="custom profile destination")
    init.add_argument("--force", action="store_true", help="replace an existing profile")

    validate = subparsers.add_parser("validate", help="validate a profile")
    validate.add_argument("profile", type=Path)

    doctor = subparsers.add_parser("doctor", help="check runtime readiness")
    doctor.add_argument("profile", type=Path)
    doctor.add_argument("--output", type=Path)

    inspect = subparsers.add_parser("run", help="run one observation iteration")
    inspect.add_argument("profile", type=Path)
    inspect.add_argument(
        "--output",
        type=Path,
        help="report root; defaults to the per-user application state directory",
    )
    inspect.add_argument(
        "--runtime",
        choices=("auto", "langgraph", "stdlib"),
        default="auto",
        help="workflow runtime",
    )
    inspect.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="return exit code 1 when trustworthy findings exist",
    )

    reports = subparsers.add_parser("reports", help="build a report dashboard")
    reports.add_argument("profile", type=Path)
    reports.add_argument("--output", type=Path)
    reports.add_argument("--open", action="store_true", help="open in the default browser")

    github = subparsers.add_parser("github", help="generate GitHub Actions quality gates")
    github.add_argument("profile", type=Path)
    github.add_argument("--path", type=Path, help="custom workflow destination")
    github.add_argument("--force", action="store_true", help="replace an existing workflow")
    return parser


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    """Run a command with stable automation-friendly exit codes."""

    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            destination, detection = write_profile(
                args.project, args.profile, force=args.force
            )
            _print(
                {
                    "status": "created",
                    "profile": str(destination),
                    "project_id": detection.project_id,
                    "technologies": detection.technologies,
                    "enabled_inspectors": [
                        name
                        for name, config in detection.inspectors.items()
                        if config["enabled"]
                    ],
                }
            )
            return 0

        profile = load_profile(args.profile)
        if args.command == "validate":
            _print(
                {
                    "status": "valid",
                    "project_id": profile.project_id,
                    "project_root": str(profile.project_root),
                }
            )
            return 0

        if args.command == "doctor":
            output = args.output or default_output_root(profile.project_id)
            result = diagnose(profile, output)
            _print(result)
            return 0 if result["status"] == "ready" else 2

        if args.command == "reports":
            output = args.output or default_output_root(profile.project_id)
            dashboard = write_dashboard(output)
            if args.open:
                webbrowser.open(dashboard.as_uri())
            _print({"status": "created", "dashboard": str(dashboard)})
            return 0

        if args.command == "github":
            destination = args.path or (
                profile.project_root / ".github" / "workflows" / "quality-gates.yml"
            )
            workflow = write_workflow(profile, destination, force=args.force)
            _print({"status": "created", "workflow": str(workflow)})
            return 0

        output = args.output or default_output_root(profile.project_id)
        outcome, report_directory = InspectionEngine(profile).run_and_write(
            output, runtime=args.runtime
        )
    except (ConfigurationError, RuntimeUnavailableError, OSError) as exc:
        print(f"loop-engineering error: {exc}", file=sys.stderr)
        return 2

    _print(
        {
            "run_id": outcome.run_id,
            "status": outcome.status,
            "runtime": outcome.runtime,
            "findings": len(outcome.findings),
            "report_directory": str(report_directory),
            "html_report": str(report_directory / "report.html"),
        }
    )
    if outcome.status == "aborted_safely":
        return 2
    if args.fail_on_findings and outcome.findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
