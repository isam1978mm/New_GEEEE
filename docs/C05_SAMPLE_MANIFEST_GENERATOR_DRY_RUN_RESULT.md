# C05 sample manifest generator dry-run result

Status: dry-run passed

This document records aggregate-only output from `scripts/c05_generate_private_sample_manifest.py`.

No private sample manifest was written.

No private sample lineage was written.

No I1 rows were created.

No I2 pack was assembled.

No validator was run on real data.

No training or inference was started.

## Dry-run command

```text
python scripts/c05_generate_private_sample_manifest.py --worldcover-raster C:\Dev\New_GEE_PRIVATE\C05_RAW\worldcover.tif
```

## Aggregate dry-run result

| Metric | Value |
| --- | ---: |
| Status | dry_run_only |
| Requested count | 217 |
| Selected count | 217 |
| Attempts | 524 |
| Duplicate cell count | 0 |
| Nodata count | 0 |
| Disallowed class count | 307 |
| Manifest written | false |
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

## Decision

Decision:

```text
c05_sample_manifest_generator_dry_run_passed
```

## Next possible phase

The next possible phase is to write the private C05 sample manifest outside Git using `--write`.

This will create only the private sample manifest and private lineage files.

It will not create C05 I1 rows.

It will not assemble I2.

## Current final status

C05 sample manifest generator dry-run passed.

C05 sample manifest is not written yet.

C05 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
