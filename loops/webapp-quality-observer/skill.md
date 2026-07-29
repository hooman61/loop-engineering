# Read-only observer instructions

## Purpose

This stage-one loop measures a configured product repository. It does not edit,
format, migrate, install into, or clean the target repository.

## Required behavior

1. Validate the inspection profile before running any sensor.
2. Execute commands as argument arrays with no command shell.
3. Keep frontend, backend, database, and integration evidence separate.
4. Classify a non-success exit code as a finding.
5. Classify missing tools, missing working directories, and timeouts as tool errors.
6. Stop safely when evidence is not trustworthy.
7. Select at most one target with deterministic ordering.
8. Store reports outside the inspected repository.
9. Compare Git fingerprints before and after inspection.
10. Never attempt to clean or revert an unexpected target-repository change.

## Forbidden behavior

- Do not invoke a coding agent.
- Do not alter a test, threshold, sensor, dependency, migration, or application file.
- Do not use production credentials or production database connections.
- Do not claim that a tool error means zero findings.
- Do not record secrets or complete sensitive logs.

## Output

Produce the four report artifacts documented in the stage-one architecture:

```text
report.json
findings.json
report.md
manifest.json
```

