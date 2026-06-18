# H3 real feature matrix plan

Status: plan ready for real feature source inventory

This document opens the H3 real feature matrix path after the private I2 pack passed readiness and the H3 smoke-test training pipeline completed.

No private rows are included.

No private identifiers are included.

No feature matrix is written by this document.

No model is trained by this document.

No inference is started by this document.

## Current status

```text
Private I2 readiness: complete
H3 smoke-test pipeline: complete
H3 local artifacts: outside Git
H4 inference: not started
Git: clean before this plan
```

## Why this phase is needed

The completed H3 baseline used:

```text
training_type: metadata_smoke_test_baseline
scientific_training_ready: false
```

That model only proved the local training pipeline works.

It should not be used for scientific claims or H4 inference.

The next H3 phase must build a real predictive feature matrix from remote-sensing and context inputs.

## Current item checklist

```text
H3 real feature matrix path

[x] I2 private rows ready
[x] smoke-test feature matrix built
[x] smoke-test training pipeline proven
[x] CI repaired / green
[x] H3 real feature matrix plan
[ ] H3 real feature source inventory       <- NEXT
[ ] H3 real feature builder script
[ ] H3 real feature dry-run
[ ] H3 real feature matrix written outside Git
[ ] H3 scientific training design
[ ] H3 scientific training dry-run
[ ] H3 scientific training run
[ ] H3 holdout evaluation
[ ] H4 gate reopen decision
```

## Goal

Create a private real feature matrix with one row per private I2 example.

Expected row count:

```text
868
```

The matrix must join one-to-one by sample_id and preserve the existing split labels.

Private output must stay outside Git.

Recommended output folder:

```text
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES
```

Recommended output files:

```text
real_feature_matrix.private.csv
real_feature_matrix.private.summary.json
real_feature_matrix_lineage.private.json
real_feature_source_inventory.private.json
```

## Candidate real feature families

The initial real feature matrix should prefer simple, explainable, aggregate features.

Recommended families:

```text
Sentinel-2 spectral band summary statistics
NDVI / NDBI / NDWI style index summaries
Dynamic World class probabilities or class context
bare / built / vegetation / water / crop context fractions
local texture or contrast summaries
neighbor-cell context summaries
source-specific quality flags
missing-data / cloud / nodata indicators
```

## Required matrix columns

Identity and split columns:

```text
sample_id
split
label
source_id
```

Required numeric features:

```text
at least 1 real numeric feature
all numeric features finite
no NaN
no Infinity
```

Recommended minimum real feature groups:

```text
spectral_mean_* 
spectral_std_*
index_mean_ndvi
index_mean_ndbi
index_mean_ndwi
dynamic_world_fraction_*
quality_cloud_or_missing_fraction
```

## Data boundary

The builder must read private data only from local private folders outside Git.

Allowed private folders:

```text
C:\Dev\New_GEE_PRIVATE\I2_PRIVATE
C:\Dev\New_GEE_PRIVATE\C06_RAW
C:\Dev\New_GEE_PRIVATE\C07_RAW
C:\Dev\New_GEE_PRIVATE\FEATURES
C:\Dev\New_GEE_PRIVATE\H3_REAL_FEATURES
```

The builder must not commit:

```text
private rows
feature matrices
model artifacts
prediction outputs
spatial payloads
raw rasters
GeoPackages
GeoJSON source files
```

## First implementation step

Before building features, create an inventory script that checks which local inputs exist.

Future script:

```text
scripts/h3_inventory_real_feature_sources.py
```

Default behavior:

```text
dry-run only
read file existence and aggregate metadata only
write nothing unless --write is explicit
print aggregate-only JSON
```

The inventory should report:

```text
private I2 pack present
private I2 row count
Dynamic World raster present
C07 mining polygons present
optional feature source folder present
candidate raster/vector source count
missing required source count
training_started: false
inference_started: false
```

## Stop conditions

Stop before any step that would:

```text
run H4 inference
create prediction files
serve model output through API/frontend
create overlays
commit private data
commit feature matrices
commit model artifacts
commit private source files
```

## Decision

```text
h3_real_feature_matrix_plan_ready
```

## Next step

```text
Create H3 real feature source inventory
```
