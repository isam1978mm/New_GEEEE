# C06 sample manifest generator dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/c06_generate_private_sample_manifest.py`.

No private sample manifest was written.

No private sample lineage was written.

No private sample rows are included.

No private identifiers are included.

No coordinates or private sampled pixel positions are included.

No I1 rows were created.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Dry-run command

```text
python scripts/c06_generate_private_sample_manifest.py --dynamic-world-raster C:\Dev\New_GEE_PRIVATE\C06_RAW\dynamic_world.tif
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_only |
| Requested count | 217 |
| Selected count | 217 |
| Attempts | 616 |
| Duplicate cell count | 0 |
| Nodata count | 0 |
| Disallowed class count | 399 |
| Manifest written | false |
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

## Decision

Decision:

```text
c06_sample_manifest_generator_dry_run_passed
```

## Next possible phase

The next possible phase is to write the private C06 sample manifest outside Git using `--write`.

This will create only the private sample manifest and private lineage files.

It will not create C06 I1 rows.

It will not assemble I2.

## Current final status

C06 sample manifest generator dry-run passed.

C06 sample manifest is not written yet.

C06 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
