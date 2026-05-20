# Reference Run v1

This directory holds the frozen notebook reference-capture notes for the production-parity phase.

## Required Contents

At minimum, record:

- notebook path
- notebook git commit SHA
- notebook file hash
- capture date
- operator environment summary
- Earth Engine datasets used
- canonical ROI label
- grid manifest identity summary
- exported artifact inventory
- parity comparison summary
- any approved `PARITY_CORRECTS` note used during interpretation

## Expected Artifact Inventory

The capture should describe or store references for:

- `grid_manifest.json`
- `dem.tif`
- `dem.npy`
- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`
- `slope.tif`
- `aspect.tif`
- `curvature.tif`
- `TPI.tif`
- `TRI.tif`
- `roughness.tif`
- `TWI.tif`
- `lst.tif`
- `NDVI.tif`
- `NDWI.tif`
- `NDMI.tif`
- `NBR.tif`
- `IRONOX.tif`
- `IRON_SWIR.tif`
- `BSI.tif`
- `hypercube.tif`
- `hypercube.npy`
- `hypercube_band_order.csv`
- `hypercube_band_stats.csv`
- `hypercube_norm_params.csv`
- `pca_anomaly.tif`
- `pca_eigenvalues.json`
- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`

## Tolerance Source

Use the stage and artifact tolerances defined in [REFERENCE_CAPTURE_PROTOCOL.md](../../../../docs/REFERENCE_CAPTURE_PROTOCOL.md).

## Current Verified Notebook Notes

- `IRON_SWIR` provenance must be recorded with an exact notebook commit SHA and file hash. The currently checked-in notebook inspection on `2026-05-20` found cell `206` using the corrected add-denominator form, so any older buggy source revision must be identified explicitly if it is still the accepted parity reference.
- Object clustering in the currently checked-in notebook inspection on `2026-05-20` is deterministic `DBSCAN` in cell `70` with `eps=4.0` and `min_samples=2`; no seed is used.

## Binary Fixture Policy

- Do not commit large binary notebook exports here unless explicitly accepted.
- Prefer metadata notes, hashes, and small derived summaries.
- If large binaries are added later, document why they are required.
