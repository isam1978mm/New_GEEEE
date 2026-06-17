# C07 sample manifest generator dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/c07_generate_private_sample_manifest.py`.

No private sample manifest was written.

No private sample lineage was written.

No private sample rows are included.

No private identifiers are included.

No coordinates or private polygon geometries are included.

No I1 rows were created.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Dry-run command

```text
python scripts/c07_generate_private_sample_manifest.py --source-file C:\Dev\New_GEE_PRIVATE\C07_RAW\maus_mining_polygons.gpkg
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_only |
| Source id | C07 |
| Source file name | maus_mining_polygons.gpkg |
| Source reader | geopandas |
| Requested count | 217 |
| Raw record count | 44929 |
| Eligible count | 44929 |
| Selected count | 217 |
| Held back count | 0 |
| Manifest written | false |
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

## Decision

Decision:

```text
c07_sample_manifest_generator_dry_run_passed
```

## Next possible phase

The next possible phase is to write the private C07 sample manifest outside Git using `--write`.

This will create only the private sample manifest and private lineage files.

It will not create C07 I1 rows.

It will not assemble I2.

It will not run the validator.

## Current final status

C07 sample manifest generator dry-run passed.

C07 sample manifest is not written yet.

C07 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
