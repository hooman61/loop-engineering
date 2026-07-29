# Golden patterns

## Metadata

```text
loop_id: sana-react-state-repair
patterns_version: 0.1.0
last_reviewed: 2026-07-29
reviewed_by: workspace-human-owner
source: Sana src/App.tsx restoreSession success path
```

## Pattern: sequential synchronization outside a state updater

### Context

Use this pattern when an effect has already derived one coherent user value and
must synchronize related React state and browser storage.

### Avoid

```tsx
setCurrentUser(previous => {
  setUserRole(fresh.role);
  localStorage.setItem("currentUserRole", fresh.role);
  return fresh;
});
```

### Follow

```tsx
setCurrentUser(fresh);
setUserRole(fresh.role);
localStorage.setItem("currentUserRole", fresh.role);
```

### Invariants

- The refreshed user is selected by the current or persisted user ID.
- The users list is still refreshed from the query result.
- `currentUser`, `userRole`, and `currentUserRole` receive the same fresh user.
- No state setter or external write runs inside another state updater.
- The effect must not create an identity-based rerender loop.

### Non-applicable cases

Stop if the repair requires changing authentication, authorization, API shape,
query enablement, dependencies, or more than the approved file.
