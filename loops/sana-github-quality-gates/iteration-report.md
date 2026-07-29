# Iteration report

## Run metadata

```text
loop_id: sana-github-quality-gates
loop_status: shadow
run_status: needs_human_input
target_revision: a082b77c25d6fd850ce40ef57f842276d4af6e4f
definition_sha256: 59f12ca6091eda7a984516a1e4a3681561eeddf73e2499952071846dc8fe7e3a
skill_sha256: dbf9fff626897b96777a8bb888459ccfe64f09ef2e62a3b9433e6cd110fec798
final_observer_run: inspection-20260729T162221Z-426e5e7e
```

The shadow implementation is complete and locally verified. It remains
`needs_human_input` because the workflow has not been copied to the original
repository, committed, pushed, or executed by GitHub.

## Selected target

- Target: add deterministic GitHub Actions quality gates to the versioned Sana
  test copy.
- Before evidence: the product had only
  `.github/workflows/postgres-backup.yml`; pull requests had no frontend,
  backend, PostgreSQL, integration, React Doctor, or aggregate required gate.
- Selection reason: the human owner selected GitHub Actions as the next project
  component after the local observer and bounded repair were proven.
- Limits: six CI-owned files, no application change, no backup-workflow change,
  no production secret, no write permission, no schedule, no push, and no
  original-source write.

## Change summary

Added a portable five-job GitHub Actions workflow:

```text
frontend ─┐
backend  ─┼─> integration ─> Required quality gate
database ─┘
```

The frontend job runs TypeScript, the exact locked React Doctor toolchain, and
the production build. Backend and database jobs use independent ephemeral
PostgreSQL 16 service containers. Integration downloads the verified frontend
bundle and runs the Django/React route contract. A final always-running job
provides one stable branch-protection check.

React Doctor JSON is retained for 14 days. The current 362-warning backlog is
reported but does not make every pull request permanently red; scanner failures
and error-severity diagnostics do fail CI.

## Files changed

| File | Purpose | In allowed paths |
|---|---|---|
| `.github/scripts/enforce-react-doctor.mjs` | Validate report shape, summarize, and fail on errors | yes |
| `.github/tools/react-doctor/package.json` | Exact tool declaration | yes |
| `.github/tools/react-doctor/package-lock.json` | Reproducible transitive dependency graph | yes |
| `.github/tools/react-doctor/scan.mjs` | Deterministic privacy-preserving sensor | yes |
| `.github/workflows/quality-gates.yml` | Five-job CI workflow | yes |
| `docs/operations/github-actions-quality-gates.md` | Operation, evidence, security, and activation guide | yes |

The copied toolchain lock is byte-identical to the proven loop-owned lock. An
initial attempt to add React Doctor to the product lock caused an unacceptably
large dependency re-resolution; those command-owned changes were discarded by
restoring `package.json` and `package-lock.json` byte-for-byte from the original
source before implementing the isolated toolchain. Both product package files
are now hash-identical to the original.

The previously approved `src/App.tsx` shadow repair remains a separate output
and is not part of this CI actuator scope.

## Before and after evidence

| Measure | Before | After | Expected direction |
|---|---:|---:|---|
| Pull-request quality jobs | 0 | 5 | complete specialist coverage |
| Stable aggregate gate | absent | `Required quality gate` | one branch-protection check |
| External actions pinned to full SHA | 0 | 11 uses | all pinned |
| Workflow repository permission | not applicable | `contents: read` | least privilege |
| Production secrets used | backup workflow only | 0 in quality workflow | isolated |
| PostgreSQL quality service | absent | PostgreSQL 16 ephemeral | production-engine coverage |
| React Doctor errors | 0 | 0 | no regression |
| React Doctor warnings | 362 | 362 | reported, not hidden |
| Original source tracked changes | none | none | preserved |

## Verification results

| Check | Result | Evidence |
|---|---|---|
| Workflow YAML parse | passed | PyYAML `BaseLoader` |
| Workflow policy assertions | 5 jobs, 11 SHA-pinned action uses, read-only, no secrets, no schedule, no `pull_request_target` | terminal evidence |
| React Doctor tool syntax | passed | `node --check` |
| React Doctor gate syntax | passed | `node --check` |
| Isolated tool installation | `react-doctor@0.9.2` installed from exact lock | terminal evidence |
| React Doctor report enforcement | 362 warnings, 0 errors, gate passed | terminal evidence |
| Product `npm ci` | passed | terminal evidence |
| TypeScript | passed | `npm run lint` |
| Vite production build | passed; 2,576 modules transformed | terminal evidence |
| Django system check | passed | terminal evidence |
| Django domain tests | 22 passed | terminal evidence |
| Migration drift | no changes detected | terminal evidence |
| Django/React route tests | 2 passed | terminal evidence |
| Loop definitions | all valid after adding required shadow baseline | terminal evidence |
| Control-plane tests | 17 passed | terminal evidence |
| Full LangGraph observer | all non-React-Doctor checks passed; one warning-class finding | `artifacts/runs/inspection-20260729T162221Z-426e5e7e/` |
| Observer repository guard | fingerprint `cb90d1dd...` identical before and after | final `report.json` |
| Original source check | HEAD and six known untracked reports unchanged; no tracked diff | terminal evidence |

The first local Vite attempt was blocked by the Windows sandbox filesystem.
The unchanged build was rerun with approved filesystem access and passed. No
check, threshold, workflow, or product code was weakened in response.

## Risks and assumptions

- GitHub-hosted execution remains unproven until the six reviewed files are
  applied to the original repository and pushed.
- Local Docker did not respond, so PostgreSQL service startup, migration
  application, and artifact transfer are structurally validated but require
  evidence from the first GitHub run.
- The workflow supports GitHub.com hosted runners. Its pinned artifact actions
  are not intended for older GitHub Enterprise Server installations.
- The 362 React Doctor warnings remain an untriaged backlog and are not
  automatically accepted as defects.
- Branch protection is external GitHub state and has not been changed.
- The original backup workflow and `DATABASE_URL` secret boundary remain
  untouched.

## Stop-condition status

- Write permission requested: not triggered.
- `pull_request_target` used: not triggered.
- Production secret or database required: not triggered.
- Unpinned external action: not triggered.
- Previously passing product gate failed: not triggered in final verification.
- Workflow edits, commits, merges, deploys, or publishes: not triggered.
- Original source changed before approval: not triggered.
- Human activation gate: reached; execution stops here.

## Durable-feedback proposal

Proposed for human review; not written to `feedback.md`:

```text
For a product with an existing warning backlog, preserve the complete diagnostic
artifact and next-target selection while blocking CI only on untrustworthy
scanner execution or explicitly baselined error severity. Tighten warning
thresholds only in separate evidence-backed iterations.
```

## Suggested next target

After human approval, copy only the six listed CI files to the original Sana
repository, commit them on a review branch, push, observe the first GitHub run,
and enable `Required quality gate` in branch protection only after PostgreSQL,
artifact transfer, and aggregate-gate evidence pass.
