# Golden patterns for observation

## Safe command declaration

Commands are arrays, not shell strings:

```yaml
command: [python, manage.py, check]
```

This is intentionally invalid:

```yaml
command: "python manage.py check && python manage.py test"
```

## Trustworthy result distinction

```text
exit code outside the accepted set -> finding
missing executable                 -> tool_error
timeout                            -> tool_error
no findings with healthy tools     -> passed
```

## Stable selection

```text
severity score descending
configured priority descending
inspector ascending
check id ascending
fingerprint ascending
```

## Read-only proof

Capture a Git content fingerprint before sensing, repeat it afterward, and stop
safely when the values differ. Never hide the difference by cleaning the target.

