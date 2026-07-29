# Sana React state-updater repair runbook

## Scope

This shadow loop creates one reviewable change in the versioned test copy:

```text
targets/sana-tank-monitor-django-test-a082b77/src/App.tsx
```

It never writes to the original source repository.

## Preflight

```powershell
python scripts/validate_loop.py loops/sana-react-state-repair/loop.yaml
git -C targets/sana-tank-monitor-django-test-a082b77 status --short
git -C targets/sana-tank-monitor-django-test-a082b77 diff -- src/App.tsx
node tools/react-doctor/scan.mjs `
  targets/sana-tank-monitor-django-test-a082b77 `
  --no-score --no-telemetry --no-supply-chain
```

Proceed only when the approved fingerprint exists and `src/App.tsx` has no
pre-existing diff.

## Verify

Run the target commands declared in `loop.yaml`, then execute the complete
observer:

```powershell
.\.venv\Scripts\python.exe scripts\run_inspection.py run `
  config\inspection.local.yaml `
  --runtime langgraph `
  --output artifacts/runs
```

The observer may select the next warning after the only error disappears. That
does not fail this repair if the approved fingerprint is absent, error count is
zero, and all other deterministic checks pass.

## Rollback

Do not clean or reset the test repository automatically. If a gate fails,
preserve the diff and evidence, mark the iteration `verification_failed`, and
let the human owner decide whether to revert or iterate.

## Human gate

The final output is a shadow-stage review artifact. Human acceptance is required
before any equivalent change is applied to the original source or merged.
