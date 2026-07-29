# Sana React state-updater repair skill

## Contract metadata

```text
loop_id: sana-react-state-repair
skill_version: 0.1.0
```

## Mission

Remove only the approved `react-doctor/no-impure-state-updater` finding from
the versioned Sana test copy while preserving the current-user and role refresh
behavior.

## Approved work package

```text
target: src/App.tsx:974-986
fingerprint: e1c943c393025ff54f7c
allowed product files: 1
maximum changed lines: 25
actuation attempts: 1
```

The human owner approved this bounded test-copy repair in the Codex task on
2026-07-29. That approval does not authorize changing the source repository,
merging, deploying, publishing, or starting another target.

## Required workflow

1. Confirm the approved fingerprint still exists in the before evidence.
2. Confirm the test copy has only the six known untracked QA reports and no
   pre-existing `src/App.tsx` diff.
3. Follow the reviewed sequential state-synchronization pattern in
   `golden-patterns.md`.
4. Change only the selected effect in `src/App.tsx`.
5. Keep `setCurrentUser` updater callbacks pure.
6. Run TypeScript, React Doctor, production build, Django checks and tests,
   migration drift, and the route contract.
7. Run the full read-only LangGraph observer after the focused checks.
8. Confirm the original source repository is unchanged.
9. Produce the complete iteration report and stop at the human review gate.

## Forbidden actions

- Do not change the observer, sensor, baseline, acceptance criteria, tests, or
  dependencies during actuation.
- Do not change any second product file.
- Do not weaken or suppress a React Doctor rule.
- Do not edit the original Sana source repository.
- Do not merge, deploy, publish, delete, clean, or handle credentials.
- Do not address any warning reported after the selected error disappears.

## Required output

Use `iteration-report.md` and report the selected target, before/after evidence,
focused diff, every verification result, remaining risks, stop conditions,
feedback proposal, and suggested next target.
