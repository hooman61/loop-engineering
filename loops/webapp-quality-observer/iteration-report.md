# Iteration report

## Latest-revision observation and independent triage — 2026-07-29

### Run metadata

```text
loop_id: webapp-quality-observer
run_id: inspection-20260729T154531Z-e3837d27
definition_sha256: 9e3e40f75678a08046a5736d0a175c8996d4a664d58558939cf1b305ea318481
skill_sha256: 4cf5979f49632152dc29264e1286ea9df94f16f3ea149b3465a04fdf49f24916
started_at: 2026-07-29T15:45:31.428708+00:00
finished_at: 2026-07-29T15:45:57.866019+00:00
status: needs_human_input
```

### Selected target

- Target: `src/App.tsx:974`, rule
  `react-doctor/no-impure-state-updater`.
- Sensor evidence: React Doctor `0.9.2` found one error and 365 warnings in 24
  affected source files. The selected diagnostic fingerprint is
  `e1c943c393025ff54f7c`.
- Selection reason: the only error precedes all warnings under the controller's
  deterministic severity-first ordering.
- Independent review: true positive. The `setCurrentUser` updater calls
  `setUserRole` and writes `localStorage`; both are observable side effects in a
  function React expects to be pure and may invoke more than once.
- Applicable limits: read-only observation, one selected target, no product
  edit, and mandatory human approval before a separate repair iteration.

### Change summary

Created a new versioned test copy for source revision `a082b77c`, verified its
included files against the source by relative path and SHA-256, installed
dependencies only in ignored paths, updated the local inspection profile, ran
the complete LangGraph observation, repeated the React Doctor sensor directly,
and independently reviewed the selected code. The previous test copy and all
product source files were preserved.

### Files changed

| File | Reason | Scope |
|---|---|---|
| `config/inspection.local.yaml` | Point local observation commands at the versioned copy | Local sensor configuration |
| `loops/webapp-quality-observer/iteration-report.md` | Preserve evidence and handoff | Loop documentation |
| `loops/webapp-quality-observer/runbook.md` | Correct current-state and copy-path guidance | Loop operations |

No tracked or untracked file in the source product or its test copy was added,
removed, or modified by the observation.

### Before and after evidence

| Measure | Before | After | Expected direction |
|---|---:|---:|---|
| Inspected revision | `6b339125...` | `a082b77c...` | match current source |
| Included source/copy files | not compared for new revision | 172 / 172 | exact |
| Relative-path differences | not measured | 0 | zero |
| SHA-256 content differences | not measured | 0 | zero |
| Verified included bytes | not measured | 1,263,726 | complete |
| React Doctor diagnostics | 361 | 366 | observed, not optimized |
| React Doctor errors | 1 | 1 | selected for review |
| Selected diagnostic fingerprint | `90d06f56eec05fa0af9e` | `e1c943c393025ff54f7c` | revision-specific |
| Target repository fingerprint | `06f7330f...` before | `06f7330f...` after | unchanged |
| Target revision | `a082b77c...` before | `a082b77c...` after | unchanged |

### Verification results

| Check or command | Result | Evidence location |
|---|---|---|
| Relative-path and SHA-256 copy comparison | 172 files equal; zero differences | terminal evidence |
| Backend `pip check` | no broken requirements | terminal evidence |
| Frontend `npm ls --depth=0` | dependency tree valid | terminal evidence |
| Full LangGraph observation | six checks passed; React Doctor finding trustworthy | `artifacts/runs/inspection-20260729T154531Z-e3837d27/` |
| Direct React Doctor repeat | 366 diagnostics; same selected fingerprint | terminal evidence |
| Django system check | passed | run `report.json` |
| Django application tests | passed | run `report.json` |
| Migration drift check | passed | run `report.json` |
| TypeScript static analysis | passed | run `report.json` |
| Production frontend build | passed | run `report.json` |
| Django/React route contract | passed | run `report.json` |
| Repository guard | identical commit, status, and content fingerprint | run `report.json` |
| Source inspection of updater | nested state update at line 980 and storage write at line 981 | copied `src/App.tsx` |

### Risks and assumptions

- This report applies only to revision
  `a082b77c25d6fd850ce40ef57f842276d4af6e4f`.
- React Doctor's remaining 365 warnings are an untriaged backlog; they are not
  accepted as defects merely because the sensor reported them.
- A repair must preserve current-user refresh behavior and avoid introducing an
  effect dependency loop. A likely bounded design derives the refreshed user
  outside the updater and performs the three updates sequentially in the effect,
  but that design has not yet been implemented or browser-tested.
- The loop still has placeholder owner and approver identities and therefore
  cannot actuate, schedule itself, or approve its own finding.
- Frontend unit coverage for the session/user refresh transition has not been
  demonstrated. A repair needs a focused regression test or explicit browser
  verification in addition to the existing static and production-build gates.

### Stop-condition status

The human gate and denied product path were approached and respected: the
finding was reviewed but not changed. No inspector error, repository mutation,
credential exposure, command escape, schema failure, or inconsistent repeated
fingerprint occurred.

### Durable-feedback proposal

Proposed for human review, not yet written to `feedback.md`:

```text
When the source HEAD advances, preserve earlier evidence and create a versioned
test copy whose included relative paths and SHA-256 hashes are proven equal
before running or comparing quality observations.
```

### Suggested next target

Define and approve one bounded repair iteration for
`src/App.tsx:974-986`: move `setUserRole` and `localStorage.setItem` out of the
`setCurrentUser` updater, add focused regression evidence for user-role refresh,
then rerun all seven configured checks. Do not batch any of the 365 warnings
into that repair.

## React Doctor sensor onboarding — 2026-07-29

### Run metadata

```text
loop_id: webapp-quality-observer
run_id: inspection-20260729T152919Z-71d00eee
definition_sha256: 9e3e40f75678a08046a5736d0a175c8996d4a664d58558939cf1b305ea318481
skill_sha256: 4cf5979f49632152dc29264e1286ea9df94f16f3ea149b3465a04fdf49f24916
started_at: 2026-07-29T15:29:19.534199+00:00
finished_at: 2026-07-29T15:29:55.754208+00:00
status: needs_human_input
```

### Selected target

- Loop-design target: add a source-only React Doctor sensor, explicitly
  requested by the human owner.
- Observation target: `src/App.tsx:900`, rule
  `react-doctor/no-impure-state-updater`.
- Sensor evidence: one error and 360 warnings across 23 source files; selected
  diagnostic fingerprint `90d06f56eec05fa0af9e`.
- Selection reason: error severity precedes warnings; the adapter then applies
  category, file, line, column, rule, and fingerprint tie-breakers.
- Applicable limits: one sensor integration, zero product changes, no automatic
  fix, no schedule, and mandatory human review.

### Change summary

React Doctor `0.9.2` is pinned in a loop-owned Node.js toolchain. A documented
adapter excludes backend, generated, dependency, and legacy-server paths;
disables score sharing, telemetry, and supply-chain network requests; emits
compact deterministic JSON; and reserves exit code `2` for untrustworthy tool
failure. The generic Python runner now supports configured tool-error exit codes.

### Files changed

| File or group | Reason | Scope |
|---|---|---|
| `.gitignore` | Ignore the tool runtime dependency tree | Loop design |
| `tools/react-doctor/*` | Pin, document, and adapt React Doctor | Loop design |
| `src/loop_engineering/{models,config,command_runner}.py` | Separate scanner failure from findings | Control plane |
| `schemas/inspection-profile.schema.json` | Declare optional tool-error exit codes | Contract |
| `config/inspection.example.yaml` | Document the new profile option | Example |
| `config/inspection.local.yaml` | Enable the target-specific React Doctor check | Local sensor |
| `tests/test_command_runner.py` | Verify configured tool-error classification | Verification |
| `tests/test_config.py` | Reject overlapping exit-code classes | Verification |
| `docs/architecture/stage-1-read-only-inspection.md` | Explain the exit-code contract | Architecture |
| `docs/api/python-control-plane.md` | Document control-plane behavior | API docs |
| `README.md` | Correct current project state | Repository docs |
| `loops/webapp-quality-observer/{loop.yaml,runbook.md,iteration-report.md}` | Register and operate the sensor | Loop package |

No file in the inspected product was changed.

### Before and after evidence

| Measure | Before | After | Expected direction |
|---|---:|---:|---|
| React Doctor runtime | absent | `0.9.2` pinned | reproducible |
| Raw diagnostics | 398, including out-of-scope files | 361 source-only | remove false positives |
| Out-of-scope diagnostics accepted | possible | zero; adapter aborts if any escape | zero |
| Stable selected fingerprint | absent | `90d06f56eec05fa0af9e` twice | stable |
| Python tests | 15 passed | 17 passed | no regression |
| Target commit | `6b339125...` | `6b339125...` | unchanged |
| Target Git status | six pre-existing QA reports | same six reports | unchanged |
| Original source HEAD | not part of the inspected snapshot | `a082b77c...` | record drift |

### Verification results

| Check or command | Result | Evidence location |
|---|---|---|
| `react-doctor.cmd --version` | `0.9.2` | terminal evidence |
| `node --check tools/react-doctor/scan.mjs` | passed | terminal evidence |
| `python -m unittest discover -s tests -t . -v` | 17 passed | terminal evidence |
| `python scripts/validate_loop.py --all` | all definitions valid | terminal evidence |
| `loop-inspect validate config/inspection.local.yaml` | valid | terminal evidence |
| Two source-only adapter scans | identical count and target fingerprint | terminal evidence |
| Full LangGraph observation | one finding, `needs_human_input` | `artifacts/runs/inspection-20260729T152919Z-71d00eee/` |
| Repository guard | before/after fingerprints identical | run `report.json` |

### Risks and assumptions

- The 361-diagnostic backlog requires human triage; tool output is evidence, not
  proof that every diagnostic is a defect.
- The adapter contract is coupled to React Doctor `0.9.2`; upgrades require a
  separate loop-design iteration and repeatability review.
- Supply-chain network checks are intentionally disabled. Dependency
  vulnerability analysis remains outside this iteration.
- Product ownership and approver placeholders remain unresolved, so the loop
  stays in `draft` and cannot actuate or schedule itself.
- The original source repository is now at `a082b77c25d6fd850ce40ef57f842276d4af6e4f`
  (`feat: add separate tank and product permissions`), while the inspected copy
  remains at `6b339125ea2a5e645da4a11e27e2e141b34673a7`. This report applies only
  to the copied revision; no synchronization was attempted.

### Stop-condition status

Two conditions were approached but not triggered in the final run:

1. The first npm installation attempt ended with `ECONNRESET`; the incomplete
   runtime was not used, and installation resumed from the pinned lock/cache.
2. The first raw scan crossed the frontend boundary into generated and backend
   files; integration stopped until explicit exclusions and an escape assertion
   were added.

The final run had no tool error, no repository mutation, no credential access,
no schema failure, and no inconsistent fingerprint.

### Durable-feedback proposal

Proposed for human review, not yet written to `feedback.md`:

```text
Before connecting a repository-wide scanner to a controller, exclude generated,
dependency, and other-domain paths and make any out-of-scope diagnostic a tool
error rather than a product finding.
```

### Suggested next target

Independently review the selected diagnostic at `src/App.tsx:900` and confirm
whether the nested `setUserRole()` call is a true defect. Do not modify the
product until that review is accepted as a separate iteration.

## Previous accepted baseline

- Loop: `webapp-quality-observer`
- Stage: `draft`
- Product profile: `config/inspection.local.yaml`
- Product: `sana-tank-monitor-django-test`
- Revision: `6b339125ea2a5e645da4a11e27e2e141b34673a7`
- Observation runs:
  - `inspection-20260729T110554Z-befe8d89`
  - `inspection-20260729T110946Z-849501af`
- Selected target: none
- Product changes: none

## Before evidence

The engine had passed its own tests, but the target-specific commands and their
cross-layer prerequisites had not yet been proven against a real product copy.

## After evidence

The stage-one control-plane now includes:

- an immutable Python domain model;
- safe shell-free command execution;
- four specialist read-only inspectors;
- a deterministic one-target controller;
- a real parallel LangGraph runtime;
- an explicitly labelled standard-library bootstrap runtime;
- before/after Git repository fingerprints;
- atomic JSON, Markdown, findings, and checksum reports;
- JSON Schemas for profiles and reports;
- a documented CLI and operational runbook.

Verification completed:

```text
14 unit and integration tests passed
real LangGraph YAML-to-report execution passed
loop and portfolio schema validation passed
example inspection profile schema validation passed
Python dependency consistency check passed
local Markdown link and code-fence validation passed
public Python API docstring validation passed
```

Two real target observations completed on the same revision with the actual
LangGraph runtime and status `accepted`:

```text
Django system check: passed
Django domain tests: 17 passed
Django migration drift: no changes detected
Frontend TypeScript analysis: passed
Vite production build: 2,576 modules transformed
Django/React route contract: 2 passed
Deterministic findings: 0
Repository fingerprint before/after: identical
Repository revision before/after: identical
Ordered findings in both runs: identical and empty
Check status sequence in both runs: identical
```

The authoritative machine-readable evidence is stored outside the inspected
repository under:

```text
artifacts/runs/inspection-20260729T110554Z-befe8d89/
artifacts/runs/inspection-20260729T110946Z-849501af/
```

## Risks and assumptions

- The loop remains `draft` because the owner and human approver placeholders
  have not been replaced with approved identities.
- Repeatability was proven for two consecutive runs on this revision. Human
  review is still required to assess possible false negatives before promotion.
- The PostgreSQL schema is checked through Django migration consistency. This
  stage does not connect to a production PostgreSQL instance and stores no
  database credentials.
- Frontend dependencies and the integration bundle are generated in ignored
  target paths; the Git fingerprint guard proves that tracked product content
  and the pre-existing worktree status did not change.

## Stop conditions approached

No mandatory stop condition was reached in the accepted run. An earlier
diagnostic run exposed two environment/setup findings: the deliberately omitted
frontend bundle and sandbox-restricted Vite config loading. They were resolved
by modelling the bundle as an integration prerequisite and running the final
observation with the required filesystem access. Neither was classified as a
product defect.

## Durable feedback proposal

Proposed, not yet approved: keep domain tests separate from cross-layer route
tests when the latter require a generated frontend artifact.
