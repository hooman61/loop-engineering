# Sana GitHub quality-gate runbook

## Current stage

The workflow is a validated shadow artifact in the versioned Sana test copy.
It has not been copied to the original repository, committed, pushed, or run by
GitHub.

## Local verification

Run the commands declared in `loop.yaml`, validate the YAML job graph, and
confirm the target diff contains only:

```text
.github/scripts/enforce-react-doctor.mjs
.github/tools/react-doctor/package.json
.github/tools/react-doctor/package-lock.json
.github/tools/react-doctor/scan.mjs
.github/workflows/quality-gates.yml
docs/operations/github-actions-quality-gates.md
```

The earlier approved `src/App.tsx` shadow diff is a separate output and must not
be counted as part of this CI work package.

## Activation

After human review:

1. copy only the six CI work-package files to the original Sana repository;
2. verify the original repository diff;
3. commit on a review branch;
4. push and open a pull request;
5. inspect the first GitHub-hosted run;
6. require `Required quality gate` in branch protection only after it passes.

Do not activate the workflow by copying the test repository wholesale.

## Failure handling

Preserve logs and artifacts. Classify dependency, runner, scanner, product, and
PostgreSQL failures separately. Fix only one selected target per later
iteration; never weaken the gate to hide a failure.
