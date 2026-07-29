# React Doctor sensor runtime

This directory owns the pinned Node.js runtime used by the read-only frontend
sensor. It is separate from every inspected product, so observing a repository
does not add or update that product's dependencies.

## Version policy

`package.json` pins React Doctor to an exact version. `package-lock.json` records
the complete dependency graph and registry integrity values. Version upgrades
are separate loop-design changes and must be followed by baseline and
repeatability review.

## Privacy and network policy

Product scans use these flags:

```text
--no-score
--no-telemetry
--no-supply-chain
```

They prevent score sharing, telemetry, crash reporting, and Socket.dev
dependency requests during a scan. Dependency vulnerability analysis belongs
to a separate security sensor with its own evidence and network policy.

## Install

```powershell
npm.cmd ci `
  --prefix tools\react-doctor `
  --cache .npm-cache `
  --no-audit `
  --no-fund
```

## Verify

```powershell
.\tools\react-doctor\node_modules\.bin\react-doctor.cmd --version
npm.cmd ls --depth=0 --prefix tools\react-doctor
```

## Adapter contract

The inspection profile calls `scan.mjs`, not the interactive installer. The
adapter excludes generated, backend, dependency, and legacy-server paths; emits
stable compact JSON; and selects one deterministic leading diagnostic.

```text
exit 0  complete scan, no diagnostics
exit 1  complete scan, one or more diagnostics
exit 2  scanner or configuration failure
```

Within the same severity, target order is Security, Bugs, Performance,
Accessibility, then Maintainability. File, line, column, rule, and diagnostic ID
provide a stable total-order tie-breaker.
