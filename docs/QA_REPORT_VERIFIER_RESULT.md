# QA report verifier result

Status: passed for the inspected private report slice.

Checked file count:

```text
comparison group A: 5 of 5 passed
comparison group B: 5 of 5 passed
```

Safe checks completed:

```text
file hash match: true for all checked files
CSV schema match: true for checked CSV files
CSV row count match: true for checked CSV files
JSON top-level-key match: true for checked JSON files
```

Safe row counts:

```text
summary CSV rows: 4
nodata audit CSV rows: 4
```

Boundary:

```text
No report bodies were committed.
No CSV rows were committed.
No array payloads were committed.
No public serving was enabled.
```

Decision:

```text
QA report parity slice: closed / passed
related provenance slice: still open / separate gate
```
