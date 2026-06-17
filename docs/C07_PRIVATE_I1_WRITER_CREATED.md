# C07 private I1 writer created

Status: script created

Script:

```text
scripts/c07_write_private_i1_rows.py
```

## Current item checklist

```text
C07 hard-negative source path

[x] plan
[x] actual review kickoff
[x] Phase A source/version confirmation
[x] Phase B sampling policy
[x] Phase C writer design
[x] private sample manifest generator
[x] C07 sample manifest generator dry-run passed
[x] private sample manifest write
[x] private I1 writer
[ ] private I1 rows written outside Git       ← NEXT
```

## Boundary

The script defaults to dry-run.

It writes zero private rows unless `--write` is explicitly provided.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Next local command

```text
python scripts/c07_write_private_i1_rows.py
```
