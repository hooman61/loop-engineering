#!/usr/bin/env python3
"""Validate one or more loop definitions against the repository contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - exercised before dev setup
    missing = getattr(exc, "name", "a required package")
    print(
        f"Missing dependency: {missing}. "
        "Install requirements-dev.txt in an isolated environment.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = REPOSITORY_ROOT / "schemas" / "loop-definition.schema.json"
DEFAULT_PORTFOLIO_SCHEMA = REPOSITORY_ROOT / "schemas" / "portfolio.schema.json"
DEFAULT_PORTFOLIO = REPOSITORY_ROOT / "config" / "portfolio.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate loop.yaml files against the Loop Engineering schema."
    )
    parser.add_argument("definitions", nargs="*", type=Path)
    parser.add_argument(
        "--all",
        action="store_true",
        help="validate the base template and every loops/**/loop.yaml file",
    )
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument(
        "--portfolio-schema", type=Path, default=DEFAULT_PORTFOLIO_SCHEMA
    )
    args = parser.parse_args()
    if not args.all and not args.definitions:
        parser.error("provide at least one definition or use --all")
    return args


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("the YAML document root must be a mapping")
    return value


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    Draft202012Validator.check_schema(value)
    return value


def format_error_path(parts: Any) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def validate_references(
    definition_path: Path,
    definition: dict[str, Any],
    portfolio: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    directory = definition_path.parent

    if directory.parent.name == "loops" and directory.name != definition.get("id"):
        errors.append(
            f"$.id: '{definition.get('id')}' must match directory '{directory.name}'"
        )

    references = {
        "$.actuator.skill_file": definition.get("actuator", {}).get("skill_file"),
        "$.human_gate.feedback_file": definition.get("human_gate", {}).get(
            "feedback_file"
        ),
    }
    for label, relative in references.items():
        if isinstance(relative, str) and not (directory / relative).is_file():
            errors.append(f"{label}: referenced file does not exist: {relative}")

    golden_patterns = definition.get("actuator", {}).get("golden_patterns", [])
    for index, relative in enumerate(golden_patterns):
        if isinstance(relative, str) and not (directory / relative).is_file():
            errors.append(
                f"$.actuator.golden_patterns[{index}]: file does not exist: {relative}"
            )

    source_docs = definition.get("metadata", {}).get("source_docs", [])
    for index, relative in enumerate(source_docs):
        if isinstance(relative, str) and not (directory / relative).is_file():
            errors.append(
                f"$.metadata.source_docs[{index}]: file does not exist: {relative}"
            )

    baseline = definition.get("sensor", {}).get("baseline_file")
    status = definition.get("status")
    if status in {"shadow", "active"}:
        if not isinstance(baseline, str) or not baseline:
            errors.append(
                "$.sensor.baseline_file: shadow and active loops require a baseline"
            )
        elif not (directory / baseline).is_file():
            errors.append(
                f"$.sensor.baseline_file: file does not exist: {baseline}"
            )

    capacity_key = definition.get("flow_control", {}).get("portfolio_capacity_key")
    review_queues = portfolio.get("review_queues", {})
    if capacity_key not in review_queues:
        errors.append(
            "$.flow_control.portfolio_capacity_key: "
            f"undefined review queue: {capacity_key}"
        )

    if status == "active" and portfolio.get("status") != "active":
        errors.append(
            "$.status: an active loop requires config/portfolio.yaml to be active"
        )

    required_siblings = ["runbook.md", "iteration-report.md"]
    for sibling in required_siblings:
        if not (directory / sibling).is_file():
            errors.append(f"required loop artifact does not exist: {sibling}")

    return errors


def validate_definition(
    definition_path: Path,
    schema: dict[str, Any],
    portfolio: dict[str, Any],
) -> list[str]:
    definition = load_yaml(definition_path)
    validator = Draft202012Validator(schema)
    errors = [
        f"{format_error_path(error.absolute_path)}: {error.message}"
        for error in sorted(
            validator.iter_errors(definition), key=lambda item: list(item.absolute_path)
        )
    ]
    errors.extend(validate_references(definition_path, definition, portfolio))
    return errors


def main() -> int:
    args = parse_args()
    schema_path = args.schema.resolve()
    portfolio_schema_path = args.portfolio_schema.resolve()
    portfolio_path = args.portfolio.resolve()

    try:
        schema = load_schema(schema_path)
        portfolio_schema = load_schema(portfolio_schema_path)
        portfolio = load_yaml(portfolio_path)
        portfolio_errors = list(
            Draft202012Validator(portfolio_schema).iter_errors(portfolio)
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Schema error: {exc}", file=sys.stderr)
        return 2

    if portfolio_errors:
        print(f"INVALID {portfolio_path}")
        for error in sorted(
            portfolio_errors, key=lambda item: list(item.absolute_path)
        ):
            print(f"  - {format_error_path(error.absolute_path)}: {error.message}")
        return 1

    print(f"VALID   {portfolio_path}")

    supplied_paths = list(args.definitions)
    if args.all:
        supplied_paths.append(REPOSITORY_ROOT / "templates" / "loop" / "loop.yaml")
        supplied_paths.extend(
            sorted((REPOSITORY_ROOT / "loops").glob("**/loop.yaml"))
        )

    definitions = list(dict.fromkeys(path.resolve() for path in supplied_paths))

    failed = False
    for path in definitions:
        try:
            errors = validate_definition(path, schema, portfolio)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors = [str(exc)]

        if errors:
            failed = True
            print(f"INVALID {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"VALID   {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
