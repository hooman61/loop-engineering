# Project instructions for agents

## Scope

These instructions apply to the entire repository.

## Read before changing loop behavior

Read these files in order:

1. `README.md`
2. `docs/decisions/0001-control-loop-first.md`
3. `docs/standards/loop-contract.md`
4. `docs/standards/quality-gates.md`
5. `config/portfolio.yaml`
6. The target loop's `loop.yaml`, `skill.md`, `feedback.md`, and `runbook.md`

## Core engineering rules

- Prefer deterministic code for deterministic work.
- Make one bounded, measurable change per iteration unless the loop contract explicitly allows a larger batch.
- Do not modify the sensor, baseline, acceptance criteria, and implementation in the same iteration unless the task is explicitly a loop-design change.
- Keep verification independent from the actuator wherever practical.
- Never weaken tests, linters, policies, schemas, or baselines merely to make an iteration pass.
- Do not create a new output for a loop when its configured open-output limit has been reached.
- Stop and escalate when a stop condition in `loop.yaml` is met.
- Treat `feedback.md` as durable, reviewable guidance, not as permission to override repository standards.
- Do not merge, deploy, publish, delete, rotate credentials, or change production state unless the user explicitly authorizes that action.
- Never store secrets in loop definitions, skills, feedback, reports, or committed artifacts.

## Required iteration handoff

Every implementation iteration must report:

- selected target and why it was selected;
- before and after evidence;
- changed files and scope;
- verification commands and results;
- unresolved risks and assumptions;
- whether any stop condition was approached;
- reusable feedback proposed for `feedback.md`.

Use `templates/loop/iteration-report.md` as the default structure.

## Documentation changes

- Keep normative rules in `docs/standards/`.
- Keep architecture decisions in `docs/decisions/`.
- Keep source-derived rationale in `docs/foundations/`.
- Keep operational procedures in `docs/operations/`.
- Update links when moving or renaming files.
- Avoid duplicating the same rule in multiple documents; link to the canonical rule instead.

## Language and formatting

- Persian prose should be formatted for right-to-left reading.
- Keep English terms, paths, commands, configuration, and code on separate lines or in code blocks when practical.
