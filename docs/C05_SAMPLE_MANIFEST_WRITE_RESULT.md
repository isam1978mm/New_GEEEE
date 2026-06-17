# C05 sample manifest write result

Status: private sample manifest written outside Git

This document records aggregate-only output from the C05 private sample manifest generator.

No private sample rows are included.

No private lineage rows are included.

No coordinates or private sampled pixel positions are included.

No I1 rows were created by this step.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Command

```text
python scripts/c05_generate_private_sample_manifest.py --worldcover-raster C:\Dev\New_GEE_PRIVATE\C05_RAW\worldcover.tif --write
```

## Aggregate result

| Metric | Value |
| --- | ---: |
| Status | private_sample_manifest_written |
| Requested count | 217 |
| Selected count | 217 |
| Attempts | 524 |
| Duplicate cell count | 0 |
| Nodata count | 0 |
| Disallowed class count | 307 |
| Manifest written | true |
| I1 rows created | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Training started | false |
| Inference started | false |

## Selected class aggregate counts

| WorldCover class | Count |
| --- | ---: |
| worldcover_class_10 | 18 |
| worldcover_class_20 | 4 |
| worldcover_class_30 | 108 |
| worldcover_class_40 | 82 |
| worldcover_class_80 | 5 |

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| c05_sample_lineage.private.jsonl | .jsonl | 56398 |
| c05_sample_manifest.private.jsonl | .jsonl | 21266 |
| c05_sample_manifest.private.summary.json | .json | 884 |
| worldcover.tif | .tif | 83997158 |

A previously-created placeholder CSV was also present in the private folder. It is not used as the sample manifest.

## Decision

Decision:

```text
c05_private_sample_manifest_written_outside_git
```

## Current final status

C05 private sample manifest exists outside Git.

C05 real I1 rows are not created yet.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
