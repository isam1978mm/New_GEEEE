# C07 sample manifest write result

Status: private sample manifest written outside Git

This document records aggregate-only output from the C07 private sample manifest generator.

No private sample rows are included.

No private lineage rows are included.

No private identifiers are included.

No coordinates or private polygon geometries are included.

No I1 rows were created by this step.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Command

```text
python scripts/c07_generate_private_sample_manifest.py --source-file C:\Dev\New_GEE_PRIVATE\C07_RAW\maus_mining_polygons.gpkg --write
```

## Aggregate result

| Metric | Value |
| --- | ---: |
| Status | private_sample_manifest_written |
| Source id | C07 |
| Source file name | maus_mining_polygons.gpkg |
| Source reader | geopandas |
| Requested count | 217 |
| Raw record count | 44929 |
| Eligible count | 44929 |
| Selected count | 217 |
| Held back count | 0 |
| Manifest written | true |
| I1 rows created | 0 |
| I2 pack assembled | false |
| Validator run on real data | false |
| Training started | false |
| Inference started | false |

## Selected class aggregate counts

| Class | Count |
| --- | ---: |
| mining_disturbance_non_target | 44929 |

## Filtering summary

```text
class_field: null
class_filter_applied: false
reject_counts: {}
```

Because no class field was supplied, all records with valid geometry were treated as operator-selected mining/disturbance non-target candidates.

## Private files created

Aggregate file inventory only:

| File | Extension | Size bytes |
| --- | --- | ---: |
| c07_sample_lineage.private.jsonl | .jsonl | 52231 |
| c07_sample_manifest.private.jsonl | .jsonl | 24087 |
| c07_sample_manifest.private.summary.json | .json | 992 |
| maus_mining_polygons.gpkg | .gpkg | 24657920 |

## Decision

Decision:

```text
c07_private_sample_manifest_written_outside_git
```

## Current final status

C07 private sample manifest exists outside Git.

C07 real I1 rows are not created yet.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
