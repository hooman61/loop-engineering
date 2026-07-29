# Golden patterns

## Metadata

```text
loop_id: sana-github-quality-gates
patterns_version: 0.1.0
last_reviewed: 2026-07-29
reviewed_by: workspace-human-owner
```

## Pattern: independent specialists with a single final gate

```text
frontend ─┐
backend  ─┼─> integration ─> required quality gate
database ─┘
```

### Invariants

- Specialist evidence remains separate.
- Integration cannot hide a failed specialist.
- The final gate fails when any required job is failed, cancelled, or skipped.
- No job can modify GitHub or production state.
- Artifacts carry evidence, not credentials.

## Pattern: report warnings, block errors

React Doctor warnings remain visible in JSON and the job summary. Scanner
failure or error-severity diagnostics block CI. Changing this threshold requires
a separate baseline decision and human review.
