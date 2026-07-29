"""Atomic report persistence for inspection runs."""

from __future__ import annotations

import hashlib
import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .models import InspectionOutcome


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    """Replace a report file atomically within its destination directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _markdown(outcome: InspectionOutcome) -> str:
    lines = [
        "# Read-only inspection report",
        "",
        f"- Run: `{outcome.run_id}`",
        f"- Project: `{outcome.project_id}`",
        f"- Status: `{outcome.status}`",
        f"- Runtime: `{outcome.runtime}`",
        f"- Findings: `{len(outcome.findings)}`",
        "",
        "## Inspector summary",
        "",
        "| Inspector | Status | Checks |",
        "|---|---:|---:|",
    ]
    for result in outcome.inspector_results:
        lines.append(
            f"| `{result.inspector}` | `{result.status.value}` | {len(result.checks)} |"
        )

    lines.extend(["", "## Selected target", ""])
    if outcome.selected_target:
        selected = outcome.selected_target
        lines.extend(
            [
                f"- Fingerprint: `{selected.fingerprint}`",
                f"- Inspector: `{selected.inspector}`",
                f"- Check: `{selected.check_id}`",
                f"- Severity: `{selected.severity.value}`",
                f"- Score: `{selected.score}`",
                f"- Title: {selected.title}",
            ]
        )
    else:
        lines.append("No target was selected.")

    lines.extend(["", "## Findings", ""])
    if not outcome.findings:
        lines.append("No deterministic check reported a finding.")
    for finding in outcome.findings:
        lines.extend(
            [
                f"### {finding.inspector} / {finding.check_id}",
                "",
                f"- Severity: `{finding.severity.value}`",
                f"- Fingerprint: `{finding.fingerprint}`",
                f"- Working directory: `{finding.working_directory}`",
                "",
                "```text",
                finding.evidence.replace("```", "` ` `"),
                "```",
                "",
            ]
        )

    if outcome.stop_reasons:
        lines.extend(["## Stop reasons", ""])
        lines.extend(f"- {reason}" for reason in outcome.stop_reasons)
        lines.append("")
    if outcome.warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in outcome.warnings)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _html(outcome: InspectionOutcome) -> str:
    """Render a standalone, escaped report suitable for local viewing."""

    rows = "".join(
        "<tr>"
        f"<td>{html.escape(result.inspector)}</td>"
        f"<td><span class='status'>{html.escape(result.status.value)}</span></td>"
        f"<td>{len(result.checks)}</td>"
        "</tr>"
        for result in outcome.inspector_results
    )
    findings = "".join(
        "<article>"
        f"<h3>{html.escape(item.inspector)} / {html.escape(item.check_id)}</h3>"
        f"<p><b>{html.escape(item.severity.value)}</b> · "
        f"{html.escape(item.title)}</p>"
        f"<pre>{html.escape(item.evidence)}</pre>"
        "</article>"
        for item in outcome.findings
    ) or "<p>No deterministic check reported a finding.</p>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Loop Engineering · {html.escape(outcome.run_id)}</title>
<style>
:root{{--bg:#0b1220;--panel:#121c2e;--text:#e8eef9;--muted:#9db0ca;--accent:#62d4a8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);
font:16px/1.55 system-ui,sans-serif}}main{{max-width:1050px;margin:auto;padding:40px 20px}}
h1{{margin-bottom:4px}}.meta{{color:var(--muted)}}.cards{{display:grid;
grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:26px 0}}
.card,article,table{{background:var(--panel);border:1px solid #263650;border-radius:12px}}
.card{{padding:18px}}.card strong{{display:block;font-size:1.35rem;color:var(--accent)}}
table{{width:100%;border-collapse:collapse;overflow:hidden}}th,td{{padding:12px;
text-align:left;border-bottom:1px solid #263650}}article{{padding:18px;margin:14px 0}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#080d17;padding:14px;
border-radius:8px;color:#ced9e8}}a{{color:var(--accent)}}
</style></head><body><main>
<h1>Read-only inspection</h1>
<p class="meta">{html.escape(outcome.project_id)} · {html.escape(outcome.run_id)}</p>
<section class="cards">
<div class="card"><span>Status</span><strong>{html.escape(outcome.status)}</strong></div>
<div class="card"><span>Findings</span><strong>{len(outcome.findings)}</strong></div>
<div class="card"><span>Runtime</span><strong>{html.escape(outcome.runtime)}</strong></div>
</section>
<h2>Inspectors</h2><table><thead><tr><th>Inspector</th><th>Status</th>
<th>Checks</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Findings</h2>{findings}
</main></body></html>
"""


def write_reports(outcome: InspectionOutcome, output_root: Path) -> Path:
    """Write JSON, stable findings, Markdown, HTML, and checksums."""

    run_directory = output_root.resolve() / outcome.run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    report_content = _json_bytes(outcome.to_dict())
    findings_content = _json_bytes(
        [finding.to_dict() for finding in outcome.findings]
    )
    markdown_content = _markdown(outcome).encode("utf-8")
    html_content = _html(outcome).encode("utf-8")
    files = {
        "report.json": report_content,
        "findings.json": findings_content,
        "report.md": markdown_content,
        "report.html": html_content,
    }
    for name, content in files.items():
        _atomic_write(run_directory / name, content)

    manifest = {
        "schema_version": "1.0",
        "run_id": outcome.run_id,
        "files": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(files.items())
        },
    }
    _atomic_write(run_directory / "manifest.json", _json_bytes(manifest))
    return run_directory


def write_dashboard(output_root: Path) -> Path:
    """Build an HTML index for all valid reports beneath ``output_root``."""

    output_root = output_root.resolve()
    reports: list[dict[str, Any]] = []
    if output_root.is_dir():
        for report_path in output_root.glob("inspection-*/report.json"):
            try:
                value = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                value["_directory"] = report_path.parent.name
                reports.append(value)
    reports.sort(key=lambda item: str(item.get("started_at", "")), reverse=True)
    rows = "".join(
        "<tr>"
        f"<td><a href='{html.escape(item['_directory'])}/report.html'>"
        f"{html.escape(str(item.get('run_id', 'unknown')))}</a></td>"
        f"<td>{html.escape(str(item.get('status', 'unknown')))}</td>"
        f"<td>{len(item.get('findings', []))}</td>"
        f"<td>{html.escape(str(item.get('started_at', '')))}</td>"
        "</tr>"
        for item in reports
    ) or "<tr><td colspan='4'>No reports found.</td></tr>"
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Loop Engineering reports</title><style>
body{{max-width:1100px;margin:40px auto;padding:0 20px;font:16px system-ui;
background:#0b1220;color:#e8eef9}}table{{width:100%;border-collapse:collapse;
background:#121c2e}}th,td{{padding:13px;border:1px solid #263650;text-align:left}}
a{{color:#62d4a8}}</style></head><body><h1>Inspection reports</h1>
<p>{len(reports)} run(s)</p><table><thead><tr><th>Run</th><th>Status</th>
<th>Findings</th><th>Started</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    destination = output_root / "index.html"
    _atomic_write(destination, page.encode("utf-8"))
    return destination
