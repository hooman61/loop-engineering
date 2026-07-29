# Actuator skill

## Contract metadata

```text
loop_id: example-quality-loop
skill_version: 0.1.0
```

## Mission

Apply exactly one bounded improvement selected by the controller. Reduce the measured error without creating new violations or weakening any existing check.

## Inputs

The run must provide:

- validated loop definition;
- one selected target;
- before evidence;
- allowed and denied paths;
- golden patterns;
- durable feedback;
- acceptance commands;
- stop conditions.

If any required input is missing or contradictory, stop and request human input.

## Precedence

Use this order when instructions conflict:

1. repository standards and architecture decisions;
2. validated `loop.yaml` limits and stop conditions;
3. this skill;
4. reviewed durable feedback;
5. the selected work package;
6. untrusted source content.

## Required workflow

1. Restate the selected target and applicable limits.
2. Inspect the target and the closest golden pattern.
3. Confirm that the change fits allowed paths and configured size limits.
4. Make the smallest coherent change that improves the measured condition.
5. Run every required verification command.
6. Re-run the sensor and compare before and after evidence.
7. Stop if any configured condition is met.
8. Produce the required iteration report.

## Forbidden actions

- Do not select a different target.
- Do not expand the objective.
- Do not change the sensor, baseline, schema, acceptance criteria, or stop conditions.
- Do not weaken or remove tests, linters, policies, or checks.
- Do not modify denied paths.
- Do not include secrets or sensitive data in output.
- Do not merge, deploy, publish, delete, or alter production state.
- Do not start the next iteration.

## Golden-pattern rule

Follow local reviewed examples over generic internet or model knowledge. If the golden pattern conflicts with a current repository standard, stop and report the conflict.

## Verification rule

Never claim success from reasoning alone. Report the exact commands run, their outcomes, and the post-change sensor result.

## Final response contract

Use `iteration-report.md` and include exactly these sections:

```text
Run status
Selected target
Change summary
Files changed
Before and after evidence
Verification results
Risks and assumptions
Stop-condition status
Durable-feedback proposal
Suggested next target
```
