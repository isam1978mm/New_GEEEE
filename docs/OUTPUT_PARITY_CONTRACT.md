# Output Parity Contract

## Purpose

Given the same ROI and input settings, the app must reproduce the notebook's operational and calculation outputs, except for explicitly documented `PARITY_CORRECTS` cases.

This contract is about operation and calculation parity. It is not a claim of real-world detection accuracy, archaeological validity, or generalization beyond the accepted notebook workflow.

## Scope

This contract applies to accepted v1 core-pipeline artifacts and their parity tests. It covers:

- grid manifest
- DEM
- SAR RTC
- DEM derivatives
- thermal LST
- Sentinel-2 indices
- hypercube outputs
- PCA outputs
- object extraction outputs
- alignment QA outputs

It does not weaken any existing safety or redaction rule.

## Artifact Parity Set

The following artifacts are in the required production parity set.

### GRID

- `grid_manifest.json`

Required parity:

- same UTM/GRID identity for the same ROI/input settings
- same CRS family, EPSG, UTM zone, hemisphere, scale, size, transform, and bounds semantics

### DEM

- `dem.tif`
- `dem.npy`

Required parity:

- notebook-equivalent DEM ingest and GRID lock
- same spatial shape and GRID identity

### SAR RTC

- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`

Required parity:

- notebook-equivalent SAR selection, pairing, dB handling, RTC path, and GRID alignment

### DEM derivatives

- `slope.tif`
- `aspect.tif`
- `curvature.tif`
- `TPI.tif`
- `TRI.tif`
- `roughness.tif`
- `TWI.tif`

Required parity:

- notebook-equivalent DEM derivative calculations and output ordering

### Thermal LST

- `lst.tif`

Required parity:

- notebook-equivalent Landsat thermal masking, scaling, compositing, and GRID alignment

### Sentinel-2 indices

- `NDVI.tif`
- `NDWI.tif`
- `NDMI.tif`
- `NBR.tif`
- `IRONOX.tif`
- `IRON_SWIR.tif`
- `BSI.tif`

Required parity:

- notebook-equivalent collection/filter/composite rules and index formulas, except documented `PARITY_CORRECTS`

### Hypercube

- `hypercube.tif`
- `hypercube.npy`
- `hypercube_band_order.csv`
- `hypercube_band_stats.csv`
- `hypercube_norm_params.csv`

Required parity:

- same persisted hypercube representation used for downstream PCA
- same channel ordering
- same normalized-plus-mask behavior
- same support-file semantics for band order, per-band statistics, and normalization parameters
- `hypercube_band_order.csv`, `hypercube_band_stats.csv`, and `hypercube_norm_params.csv` must be band-order-aligned
- row order in those CSVs is semantic and must match the persisted hypercube channel order

### PCA

- `pca_anomaly.tif`
- `pca_eigenvalues.json`

Required parity:

- notebook-equivalent PCA input preparation, seeded fit behavior, anomaly magnitude logic, and report contents

### Object extraction

- `objects_index.csv`
- `clusters_summary.csv`

Required parity:

- same thresholding behavior
- same connected-component and object ordering behavior
- same clustering parameters
- same cluster labeling and output ordering behavior
- if H4 finds randomized clustering in the notebook, the production path must persist the seed and support deterministic replay

### Alignment QA

- `alignment_qa.json`

Required parity:

- notebook-equivalent alignment and drift checks for the accepted GRID contract

## Comparison Rules

### Rasters

Applies to GeoTIFF outputs such as DEM, SAR RTC, DEM derivatives, thermal, S2 indices, hypercube, and PCA.

Required comparisons:

- same raster count for the artifact set under comparison
- same spatial shape
- same CRS
- same transform
- same nodata semantics
- same band order
- same dtype policy
- same valid-mask behavior where a mask band or nodata policy is part of the stage contract

Numeric rules:

- values must match within stage-appropriate numeric tolerance
- tolerance must be explicit in the parity test or fixture protocol
- if a stage is intended to be exact, non-exact output is a parity failure
- if a stage uses floating-point normalization or decomposition, the tolerance must be documented and stable

### NPY

Applies to `dem.npy`, `hypercube.npy`, and any other parity-controlled array export.

Required comparisons:

- same shape
- same channel order
- same dtype policy
- same value tolerance rules
- same valid-mask behavior
- same nodata or fill semantics where the notebook-defined representation depends on them

### CSV

Applies to `hypercube_band_order.csv`, `hypercube_band_stats.csv`, `hypercube_norm_params.csv`, `objects_index.csv`, and `clusters_summary.csv`.

Required comparisons:

- same columns
- same row ordering
- same row count
- same deterministic values within any documented numeric tolerance

Public-output rule:

- public-facing CSV outputs must not include forbidden coordinate-bearing columns
- parity does not override redaction constraints

### JSON

Applies to `alignment_qa.json`, `pca_eigenvalues.json`, manifests, and sidecars as appropriate.

Required comparisons:

- same required keys
- same deterministic values where applicable
- same parity metadata where applicable

Forbidden content rule:

- no coordinates
- no geometry
- no bounds
- no CRS transforms in public outputs
- no filesystem paths
- no hashes
- no raw errors or traceback content

### Manifests and sidecars

Applies to internal manifests and raster sidecars that anchor GRID identity.

Required comparisons:

- exact GRID identity where required
- same CRS and transform contract
- same size, nodata, and dtype policy fields where the sidecar defines them

## Allowed Exceptions

### IRON_SWIR

`IRON_SWIR` is `PARITY_CORRECTS`.

The app intentionally uses:

`(B11 - B12) / (B11 + B12)`

H4 found that the checked-in notebook evidence is not yet fully reconciled with the older parity notes. See [IRON_SWIR_PROVENANCE.md](IRON_SWIR_PROVENANCE.md).

The accepted H4.5 production interpretation is Option A from [IRON_SWIR_PROVENANCE.md](IRON_SWIR_PROVENANCE.md).

H5 comparison rule for `IRON_SWIR`:

- compare against the corrected analytical/app reference using `(B11 - B12) / (B11 + B12)`
- do not compare pixel-for-pixel against the checked-in notebook sign-flipped `IRON_SWIR` raster

This exception is allowed because the PRD and current parity metadata already accept an `IRON_SWIR` denominator correction in the app.

### Future exceptions

Any future parity exception must include all of the following:

- `parity_category`
- `parity_reason`
- test coverage
- documentation

Undocumented output drift is not an allowed exception.

## Rollback and Recovery Rule

If a parity test fails, the offending stage must be rolled back to its accepted M-phase implementation pending PRD and parity-contract review.

No band-aid fix may bypass the parity contract.

This rollback rule applies to:

- SAR RTC
- Sentinel-2
- hypercube
- PCA
- object extraction
- all other parity stages

## Production Acceptance Gate

Production parity is not accepted until all of the following are true:

- v1 tests pass
- CI passes
- notebook safety scanner passes
- canonical notebook reference outputs are captured
- app outputs are compared against frozen notebook outputs
- all differences are either zero or documented as `PARITY_CORRECTS`
- live Earth Engine service-account run completes
- public API leaks no coordinates, geometry, bounds, CRS transforms, hashes, filesystem paths, or raw errors
- experimental classifier remains CLI-only and `FILESYSTEM_ONLY`

## Failure Policy

Any difference outside documented tolerance or outside an approved `PARITY_CORRECTS` record is a parity failure.

Parity failures block production hardening until resolved or formally documented through the accepted parity process.
