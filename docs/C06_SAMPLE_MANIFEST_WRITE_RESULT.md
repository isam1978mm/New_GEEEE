# C06 sample manifest write result

Status: private sample manifest written outside Git

This document records aggregate-only output from the C06 private sample manifest generator.

No private sample rows are included.

No private lineage rows are included.

No private identifiers are included.

No coordinates or private sampled pixel positions are included.

No I1 rows were created by this step.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Command

```text
python scripts/c06_generate_private_sample_manifest.py --dynamic-world-raster C:\Dev\New_GEE_PRIVATE\C06_RAW\dynamic_world.tif --write
```

## Aggregate result

| Metric | Value |
| --- | ---: |
| Status | private_sample_manifest_written |
| Requested count | 217 |
| Selected count | 217 |
| Attempts | 616 |
| Duplicate cell count | 0 |
| Nodata count | 0 |
| Disallowed class count | 399 |
| Manifest written | true |
| I1 rows created | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Training started | false |
| Inference started | false |

## Selected class aggregate counts

| Dynamic World class | Count |
| --- | ---: |
| bare | 182 |
| built | 35 |

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| c06_sample_lineage.private.jsonl | .jsonl | 54335 |
| c06_sample_manifest.private.jsonl | .jsonl | 21700 |
| c06_sample_manifest.private.summary.json | .json | 704 |
| dynamic_world.tif | .tif | 13165994 |

## Decision

Decision:

```text
c06_private_sample_manifest_written_outside_git
```

## Current final status

C06 private sample manifest exists outside Git.

C06 real I1 rows are not created yet.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
