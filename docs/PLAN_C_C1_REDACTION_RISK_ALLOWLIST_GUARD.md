# Plan C C1 ??? Redaction Risk Allowlist Guard

## Date

2026-07-03

## Status

Implemented as a static safety guard.

## Scope

C1 freezes the current approved redaction-risk baseline for:

```text
docs/
app/
scripts/
```

The guard excludes tests because tests intentionally contain coordinate-like and redaction fixtures.

## What the guard blocks

The C1 test fails if future changes introduce:

```text id="q4j7zc"
1. A new unapproved docs/app/scripts file with private-path or coordinate-like risk.
2. A new risk type in an already-approved file.
3. An increased risk count in an already-approved file.
```

Decreases or removals are allowed.

## Files

```text id="pli16y"
tests/fixtures/plan_c_c1_redaction_risk_allowlist.json
tests/unit/test_plan_c_redaction_risk_allowlist.py
```

## Non-goals

```text id="fs41ch"
No app behavior change.
No private artifact movement.
No raw array inspection.
No exact coordinate exposure.
No notebook parity claim.
```

## Future update rule

Only update the allowlist when the added risk is intentional and documented. Prefer removing or redacting risky content instead of expanding the allowlist.
