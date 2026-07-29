# Loop runbook

## Ownership

```text
loop_id: example-quality-loop
owning_team: replace-with-owning-team
primary_approver: replace-with-human-approver
escalation_contact: replace-with-contact-or-role
```

## Purpose and scope

Describe the product property controlled by this loop, its boundaries, and what it must never change.

## Dependencies

List required tools, repositories, services, permissions and named secret references. Never place secret values in this file.

## Schedule and triggers

- Scheduled trigger:
- Manual trigger:
- Feedback or iterate trigger:
- Events that must not trigger the loop:

## Preflight procedure

1. Validate `loop.yaml` against the schema.
2. Confirm lifecycle state permits the requested action.
3. Check per-loop open-output capacity.
4. Check portfolio review capacity.
5. Confirm no overlapping target lock exists.
6. Run the sensor without changing the product.
7. Confirm the baseline and working environment are healthy.

## Normal operation

Document how the sensor, controller, actuator and verifier are invoked, where evidence is stored, and how the review output is identified.

## Pause procedure

Document the reversible steps that stop scheduling and actuation while preserving evidence and open outputs.

## Resume procedure

Resume through `shadow` mode. Define the evidence required before returning to `active`.

## Rollback procedure

Document how to identify the affected run, revert its product change, re-run baseline checks, and verify recovery.

## Incident procedure

1. Pause the loop.
2. Prevent automatic retries.
3. Identify all open outputs and target locks.
4. Restore the last verified product state.
5. Preserve relevant non-sensitive evidence.
6. Record cause and corrective action.
7. Recalibrate in shadow mode.

## Escalation conditions

List loop-specific conditions that require human or specialist intervention in addition to the global stop conditions.

## Scale-up criteria

Define the minimum accepted-run count, maximum rework rate, maximum rollback rate, review capacity and observation window required before increasing schedule, batch size, parallelism or autonomy.

## Retirement procedure

Document how scheduling, permissions, locks and open outputs are closed while retaining necessary audit evidence.
