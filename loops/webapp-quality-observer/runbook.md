# Web application quality observer runbook

## Current state

The loop is in `draft`. Two baseline observations on revision `6b339125`
completed with status `accepted`. A later source-only React Doctor observation
on revision `a082b77c` completed with status `needs_human_input` and selected one
independently confirmed impure state updater in `src/App.tsx`. The source and
versioned test copy were unchanged by that run. The loop must remain
non-scheduled and non-actuating until the owner and approver are assigned and
the selected finding is approved for a separate bounded repair iteration.

## Configure

1. Copy `config/inspection.example.yaml` to `config/inspection.local.yaml`.
2. Set the absolute target repository path.
3. Replace example working directories and commands with commands proven in the
   target repository.
4. Keep credentials and production connection strings out of the profile.
5. Ensure report output is outside the target repository.

## Prepare an isolated product copy

The Sana target profile expects dependency environments inside the disposable
copy. These paths are ignored by the target repository and must never be copied
back to the source repository.

```powershell
$targetRoot = "C:\Users\huoman\OneDrive\Documents\loop-engineering\targets\sana-tank-monitor-django-test-<short-commit>"

python -m venv "$targetRoot\backend\.venv"
& "$targetRoot\backend\.venv\Scripts\python.exe" `
  -m pip install --disable-pip-version-check `
  -r "$targetRoot\backend\requirements.txt"

npm.cmd ci `
  --prefix "$targetRoot" `
  --cache .npm-cache `
  --no-audit `
  --no-fund
```

Confirm the environments before inspection:

```powershell
& "$targetRoot\backend\.venv\Scripts\python.exe" -m pip check
npm.cmd ls --depth=0 --prefix "$targetRoot"
git -C "$targetRoot" status --short
```

The integration inspector creates `backend/frontend_dist/` before running the
Django/React route contract. That directory is generated, ignored, and may be
replaced on every run.

Create a new versioned copy when the source revision changes. Preserve older
copies as evidence, and compare the included relative paths and SHA-256 hashes
before treating the new copy as equivalent to the source.

## Prepare the React Doctor sensor

React Doctor belongs to the loop toolchain, not to the inspected product. Its
exact version and dependency graph are pinned under `tools/react-doctor/`.

```powershell
npm.cmd ci `
  --prefix tools\react-doctor `
  --cache .npm-cache `
  --no-audit `
  --no-fund

.\tools\react-doctor\node_modules\.bin\react-doctor.cmd --version
```

The profile invokes the non-interactive adapter in `tools/react-doctor/scan.mjs`.
The adapter excludes backend, generated, dependency, and legacy-server paths;
disables score sharing, telemetry, and network supply-chain requests; and emits
one stable leading diagnostic for deterministic controller selection. See the
[toolchain contract](../../tools/react-doctor/README.md).

## Validate

```powershell
.\.venv\Scripts\python.exe scripts\run_inspection.py validate `
  config\inspection.local.yaml
```

## Run with LangGraph

```powershell
.\.venv\Scripts\python.exe scripts\run_inspection.py run `
  config/inspection.local.yaml `
  --runtime langgraph `
  --output artifacts/runs
```

## Bootstrap diagnostics without dependencies

The standard-library runtime exists only to test deterministic control logic
before LangGraph is installed. A report identifies this runtime explicitly.

```powershell
python scripts/run_inspection.py run `
  config/inspection.local.json `
  --runtime stdlib `
  --output artifacts/runs
```

## Interpret status

```text
accepted            all enabled checks passed
needs_human_input   trustworthy findings exist
aborted_safely      tool failure or read-only policy violation
```

An `accepted` observation is not authorization to change the loop lifecycle
status. Promotion from `draft` still requires the lifecycle criteria and human
approval.

## Repeatability gate

Before proposing `shadow` status:

1. rerun the profile on the same Git revision;
2. compare the ordered finding fingerprints;
3. confirm the before/after repository fingerprints remain identical;
4. record false-positive and false-negative review results;
5. assign the loop owner and human approver.

## Incident response

If the target repository changes during inspection:

1. Do not run another iteration.
2. Preserve the report and target worktree state.
3. Identify the command that wrote to the repository.
4. Remove or reconfigure that command in a separately reviewed loop-design change.
5. Let the repository owner decide how to handle generated files; the observer
   must not clean them automatically.
