# Sana GitHub quality-gate delivery skill

## Mission

Create one reviewable GitHub Actions workflow in the versioned Sana test copy.
The workflow measures frontend, backend, database, integration, and React
quality without modifying the repository or contacting production systems.

## Required behavior

1. Preserve the existing PostgreSQL backup workflow and its secret boundary.
2. Use pull-request, protected-branch push, and manual triggers only.
3. Grant `contents: read` and no write permission.
4. Pin every external action to a reviewed full commit SHA.
5. Use locked product and React Doctor installations.
6. Run frontend, backend, and database specialists independently.
7. Make integration depend on all three specialists.
8. Use ephemeral PostgreSQL 16 for backend, database, and integration checks.
9. Upload React Doctor evidence even when its gate fails.
10. Provide one final required-check job for branch protection.
11. Stop at human review; do not copy, commit, push, merge, or deploy.

## Warning policy

The current warning backlog is evidence, not a reason to make CI permanently
red. React Doctor scanner failures and error-severity diagnostics fail CI.
Warnings are summarized and uploaded for bounded future iterations.

## Forbidden behavior

- Do not use `pull_request_target`.
- Do not grant write permissions.
- Do not use production credentials, database URLs, or backup secrets.
- Do not suppress React Doctor rules or weaken product checks.
- Do not alter application code, migrations, tests, or the backup workflow.
- Do not write to the original Sana repository.

## Output

Complete `iteration-report.md` with scope, before/after evidence, changed files,
verification, unproven GitHub-only behavior, stop conditions, and the human
activation steps.
