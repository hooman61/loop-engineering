"""Workflow runtimes for the stage-one inspection graph.

LangGraph is the production graph runtime.  A standard-library runtime with the
same domain contract exists for unit tests and bootstrap diagnostics before
dependencies are installed.  Reports disclose which runtime executed a run;
the fallback is never presented as a LangGraph execution.
"""

from __future__ import annotations

import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Any, TypedDict

from .controller import normalize_findings, select_one_target
from .inspectors import SpecialistInspector
from .models import (
    CheckResult,
    CheckStatus,
    Finding,
    InspectorResult,
    InspectorStatus,
    Severity,
)


class RuntimeUnavailableError(RuntimeError):
    """Raised when the requested graph runtime is not installed."""


class InspectionGraphState(TypedDict, total=False):
    """Serializable state contract shared by graph nodes."""

    inspector_results: Annotated[list[dict[str, Any]], operator.add]
    findings: list[dict[str, Any]]
    selected_target: dict[str, Any] | None


def _check_from_dict(value: dict[str, Any]) -> CheckResult:
    return CheckResult(
        inspector=value["inspector"],
        check_id=value["check_id"],
        title=value["title"],
        status=CheckStatus(value["status"]),
        severity=Severity(value["severity"]),
        priority=value["priority"],
        command=tuple(value["command"]),
        working_directory=value["working_directory"],
        exit_code=value["exit_code"],
        duration_ms=value["duration_ms"],
        evidence=value["evidence"],
        error_kind=value.get("error_kind"),
    )


def inspector_result_from_dict(value: dict[str, Any]) -> InspectorResult:
    """Rehydrate domain output from graph-safe state."""

    return InspectorResult(
        inspector=value["inspector"],
        status=InspectorStatus(value["status"]),
        checks=tuple(_check_from_dict(check) for check in value["checks"]),
    )


def finding_from_dict(value: dict[str, Any]) -> Finding:
    """Rehydrate a finding from a graph-safe dictionary."""

    return Finding(
        fingerprint=value["fingerprint"],
        project_id=value["project_id"],
        inspector=value["inspector"],
        check_id=value["check_id"],
        title=value["title"],
        severity=Severity(value["severity"]),
        priority=value["priority"],
        score=value["score"],
        evidence=value["evidence"],
        command=tuple(value["command"]),
        working_directory=value["working_directory"],
    )


def _control_state(
    project_id: str, result_values: list[dict[str, Any]]
) -> dict[str, Any]:
    results = sorted(
        (inspector_result_from_dict(value) for value in result_values),
        key=lambda result: result.inspector,
    )
    findings = normalize_findings(project_id, results)
    selected = select_one_target(findings)
    return {
        "findings": [finding.to_dict() for finding in findings],
        "selected_target": selected.to_dict() if selected else None,
    }


def run_standard_graph(
    project_id: str, inspectors: dict[str, SpecialistInspector]
) -> tuple[list[InspectorResult], list[Finding], Finding | None, str]:
    """Run the graph contract with standard-library parallelism."""

    with ThreadPoolExecutor(max_workers=max(1, len(inspectors))) as executor:
        futures = {
            name: executor.submit(inspector.inspect)
            for name, inspector in inspectors.items()
        }
        results = [futures[name].result() for name in sorted(futures)]
    findings = normalize_findings(project_id, results)
    return results, findings, select_one_target(findings), "stdlib-fallback"


def run_langgraph(
    project_id: str, inspectors: dict[str, SpecialistInspector]
) -> tuple[list[InspectorResult], list[Finding], Finding | None, str]:
    """Build and invoke the parallel LangGraph inspection workflow."""

    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeUnavailableError(
            "LangGraph is not installed. Install project dependencies or use "
            "the explicit stdlib bootstrap runtime."
        ) from exc

    graph = StateGraph(InspectionGraphState)
    inspector_nodes: list[str] = []
    for name, inspector in inspectors.items():
        node_name = f"inspect_{name}"
        inspector_nodes.append(node_name)

        def run_node(
            _state: InspectionGraphState,
            selected: SpecialistInspector = inspector,
        ) -> dict[str, Any]:
            return {"inspector_results": [selected.inspect().to_dict()]}

        graph.add_node(node_name, run_node)
        graph.add_edge(START, node_name)

    def control_node(state: InspectionGraphState) -> dict[str, Any]:
        return _control_state(project_id, state.get("inspector_results", []))

    graph.add_node("deterministic_control", control_node)
    graph.add_edge(inspector_nodes, "deterministic_control")
    graph.add_edge("deterministic_control", END)
    final_state = graph.compile().invoke({"inspector_results": []})

    results = sorted(
        (
            inspector_result_from_dict(value)
            for value in final_state.get("inspector_results", [])
        ),
        key=lambda result: result.inspector,
    )
    findings = [
        finding_from_dict(value) for value in final_state.get("findings", [])
    ]
    selected_value = final_state.get("selected_target")
    selected = finding_from_dict(selected_value) if selected_value else None
    return results, findings, selected, "langgraph"


def run_inspection_graph(
    project_id: str,
    inspectors: dict[str, SpecialistInspector],
    runtime: str,
) -> tuple[list[InspectorResult], list[Finding], Finding | None, str]:
    """Select an explicit runtime without disguising fallback behavior."""

    if runtime == "langgraph":
        return run_langgraph(project_id, inspectors)
    if runtime == "stdlib":
        return run_standard_graph(project_id, inspectors)
    if runtime != "auto":
        raise ValueError(f"unsupported runtime: {runtime}")
    try:
        return run_langgraph(project_id, inspectors)
    except RuntimeUnavailableError:
        return run_standard_graph(project_id, inspectors)

