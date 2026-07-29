# GitHub quality-gate baseline

## Revision

```text
target: sana-tank-monitor-django-test-a082b77
commit: a082b77c25d6fd850ce40ef57f842276d4af6e4f
captured_at: 2026-07-29
```

## Before

- The product had only a scheduled/manual PostgreSQL backup workflow.
- Pull requests and protected-branch pushes had no frontend, backend, database,
  integration, or aggregate required quality gate.
- React Doctor evidence was produced only by the local loop toolchain.

## Proven local checks

```text
TypeScript: passed
React Doctor: 362 warnings, 0 errors
Vite production build: 2,576 modules transformed
Django system check: passed
Django domain tests: 22 passed
Migration drift: no changes detected
Django/React route tests: 2 passed
```

## GitHub-only evidence still required

- successful PostgreSQL 16 service-container startup;
- successful migration application to ephemeral PostgreSQL;
- frontend artifact transfer into the integration job;
- artifact upload and download;
- aggregate `Required quality gate` result;
- branch-protection configuration.

These items cannot be accepted until the reviewed workflow is committed, pushed,
and observed on GitHub.
