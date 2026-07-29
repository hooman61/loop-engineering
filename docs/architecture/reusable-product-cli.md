# Reusable Loop Engineering product

## Product boundary

Loop Engineering is an installable, configuration-driven command-line product
for deterministic read-only quality observation. It discovers common project
stacks, generates a portable profile, checks local readiness, runs the existing
LangGraph control plane, renders durable reports, and can generate a read-only
GitHub Actions workflow.

It does not automatically edit application code, merge, deploy, access
production data, or turn every scanner warning into an accepted defect.

## Primary workflow

```text
init -> doctor -> run -> reports
                 |
                 +-> github
```

```powershell
loop-engineering init C:\path\to\project
loop-engineering doctor C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering run C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering reports C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering github C:\path\to\project\.loop-engineering\inspection.yaml
```

## Portability contract

- Generated profiles live under `.loop-engineering/` in the inspected project.
- `project.root` is relative to the profile, normally `..`.
- Project commands use the `{project-python}` runtime token. It prefers a
  virtual environment beside the project command and otherwise uses the
  current interpreter, without storing an operating-system-specific path.
- Default run evidence is stored outside the inspected repository in the user
  state directory.
- Commands remain argument arrays and are executed without a local shell.
- Generated GitHub workflows use Bash only inside GitHub-hosted Linux jobs and
  quote every configured argument.

## Detection contract

Detection is conservative and evidence-based:

- `package.json` plus known scripts enables frontend checks;
- `manage.py` enables Django system, test, and migration checks;
- `pytest` configuration or test files enable generic Python tests;
- build scripts are not enabled automatically because they commonly write
  bundles inside the target tree;
- unknown stacks produce a valid disabled profile and actionable doctor output
  instead of invented commands.

Generated configuration is a reviewable starting point. Users can add or remove
checks without modifying the control-plane source.

## Report contract

Every run writes:

```text
report.json
findings.json
report.md
report.html
manifest.json
```

The reports command builds an HTML index over all available runs for one
project. Dynamic evidence is HTML-escaped and no remote script is loaded.

## GitHub Actions contract

The generator creates one job per enabled inspector and one aggregate quality
gate. It:

- grants only `contents: read`;
- uses no production secret;
- pins GitHub-maintained actions to full commit SHAs;
- installs detected locked dependencies;
- captures check logs as artifacts;
- treats only configured success exit codes as success;
- does not commit, merge, deploy, publish, or schedule itself.

The generated workflow is a proposal until reviewed, committed, pushed, and
observed on GitHub.

## Exit codes

```text
0  command completed and its contract passed
1  trustworthy product findings exist when --fail-on-findings is requested
2  invalid configuration, missing prerequisite, untrustworthy evidence, or I/O failure
```
