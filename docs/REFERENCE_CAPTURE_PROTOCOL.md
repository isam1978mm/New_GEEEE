# Reference Capture Protocol

## Purpose

This document defines how to capture the frozen notebook reference outputs for production parity.

The goal is operational and calculation parity only. It is not a validation of real-world detection accuracy, archaeological validity, or deployment readiness by itself.

## Scope

This protocol applies to the core parity artifacts listed in [OUTPUT_PARITY_CONTRACT.md](OUTPUT_PARITY_CONTRACT.md):

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

## Preconditions

Before a reference capture is accepted:

1. The accepted v1 baseline must be frozen per `H0`.
1. The full local suite must pass:
   - `pytest tests/unit/ tests/integration/ tests/notebook_parity/`
1. The notebook safety scanner must pass:
   - `python scripts/check_notebook_safety.py`
1. The notebook revision used for capture must be the committed `notebooks/new.ipynb` or an explicitly recorded alternate hash.
1. The canonical ROI must be deliberately uninteresting and must be recorded by label, not by public coordinates.

## Canonical ROI

Use a stable internal label such as `canonical_roi_v1`.

Record:

- ROI label
- whether it is the accepted canonical ROI
- the internal grid manifest generated from the ROI

Do not publish raw ROI coordinates in the committed fixture notes. If coordinates are needed operationally, keep them in private operator notes outside the repo.

## Notebook Run Procedure

1. Start from a clean checkout of the accepted baseline.
1. Verify the notebook safety scan passes.
1. Open `notebooks/new.ipynb`.
1. Use the canonical ROI label and the accepted input settings used for parity capture.
1. Run the notebook in order from a fresh kernel.
1. Export only the parity artifacts required by the contract.
1. Normalize unstable metadata before comparing or committing any derived reference material.
1. Store the frozen capture under `tests/notebook_parity/fixtures/reference_run_v1/`.

## Required Capture Metadata

Every reference capture must include a metadata note or manifest containing at least:

- notebook path
- notebook git commit SHA
- notebook file hash
- capture date in ISO 8601
- operator environment summary
  - Python version
  - key package versions used for notebook execution
  - OS/runtime
- Earth Engine datasets referenced during the run
- ROI label
- grid manifest identity summary
  - CRS
  - EPSG
  - UTM zone
  - hemisphere
  - scale
  - output size
- parity exception notes, if any

## Stage and Artifact Tolerances

These values are the default H4 capture tolerances. H5 comparison tests must use these values unless a later contract update explicitly changes them.

| Stage / artifact set | Comparison mode | Numeric tolerance |
|---|---|---|
| GRID manifest and internal GRID sidecars | exact identity | exact |
| `dem.tif`, `dem.npy` | float comparison after shape/CRS/transform checks | abs <= `1e-5` |
| SAR RTC rasters | float comparison after shape/CRS/transform checks | abs <= `1e-4` |
| DEM derivative rasters | float comparison after shape/CRS/transform checks | abs <= `1e-4` |
| `lst.tif` | float comparison after shape/CRS/transform checks | abs <= `1e-3` |
| S2 index rasters other than `IRON_SWIR` | float comparison after shape/CRS/transform checks | abs <= `1e-4` |
| `IRON_SWIR.tif` | `PARITY_CORRECTS`; compare against corrected analytical/app reference, not notebook output | abs <= `1e-6` |
| `hypercube.tif`, `hypercube.npy` | float comparison with channel-order and `valid_mask` checks | abs <= `1e-5` |
| `hypercube_band_order.csv` | exact rows and ordering | exact |
| `hypercube_band_stats.csv`, `hypercube_norm_params.csv` | exact row order; float field comparison | abs <= `1e-6` |
| `pca_anomaly.tif` | float comparison after shape/CRS/transform checks | abs <= `1e-5` |
| `pca_eigenvalues.json` | exact keys; float field comparison | abs <= `1e-6` |
| `objects_index.csv` | exact columns and row ordering; float field comparison only where documented | abs <= `1e-6` |
| `clusters_summary.csv` | exact columns and row ordering; float field comparison only where documented | abs <= `1e-6` |
| `alignment_qa.json` | exact keys; float field comparison | abs <= `1e-6` |

If a future capture shows that a tolerance must change, update this document and the parity contract together before re-baselining.

## Comparison Procedure

1. Capture notebook outputs for the canonical ROI.
1. Run the app for the same ROI and input settings.
1. Compare outputs according to [OUTPUT_PARITY_CONTRACT.md](OUTPUT_PARITY_CONTRACT.md).
1. Treat any difference outside the documented tolerance as a parity failure unless it is an approved `PARITY_CORRECTS` exception.
1. Record the comparison result in the fixture notes.

## Storage Layout

Store the H4 reference capture under:

- `tests/notebook_parity/fixtures/reference_run_v1/README.md`
- optional small metadata files in the same directory
- optional small derived text summaries in the same directory

Do not add large binary fixtures unless they already exist and are explicitly accepted for storage.

## Bundle Storage and Portability

The frozen notebook reference bundle is operator-local and never committed. The repo commits only the portable manifest:

- `tests/notebook_parity/fixtures/reference_run_v1/MANIFEST.json`

Binary notebook outputs such as GeoTIFF, NPY, CSV, and JSON bundle files remain outside git. Operators point parity tests at the local bundle with:

- `NOTEBOOK_REFERENCE_BUNDLE_DIR`

On a new machine or future VPS, copy the bundle out-of-band to the chosen local path and set `NOTEBOOK_REFERENCE_BUNDLE_DIR` there. The path is operator configuration, not repo state.

Before comparing reference outputs, parity tests verify each file against the committed manifest checksum and recorded size. Missing configured files skip with the relative file name. Checksum mismatches fail because the configured bundle no longer matches the committed reference contract.

The manifest and test output must not expose raw coordinates, raw bounds, raw CRS transforms, absolute paths, or local machine paths.

## Verified Notebook Findings

### IRON_SWIR provenance

The PRD and current app metadata treat `IRON_SWIR` as `PARITY_CORRECTS`.

Verified notebook inspection on `2026-05-20` found:

- checked-in source: `notebooks/new.ipynb`
- notebook cell: `206`
- visible formula: `image.select('B12').subtract(image.select('B11')).divide(image.select('B12').add(image.select('B11')))`

This checked-in notebook cell already shows the corrected add-denominator form, not the buggy denominator recorded in the PRD and parity notes.

Implication:

- H4 must record the exact notebook commit SHA and file hash used for reference capture.
- If the accepted production reference is meant to come from an older notebook revision that still contains the denominator bug, that older revision must be identified explicitly by commit or artifact hash.
- If the checked-in notebook is the accepted capture source, the repo’s `IRON_SWIR` exception record must be reconciled in a later milestone before re-baselining.

### Object clustering determinism

Verified notebook inspection on `2026-05-20` found:

- checked-in source: `notebooks/new.ipynb`
- notebook cell: `70`
- clustering algorithm: `DBSCAN`
- parameters: `eps=4.0`, `min_samples=2`
- seed usage: none

DBSCAN is deterministic for a fixed input ordering and parameter set, so current object clustering is treated as deterministic rather than seeded.

If a future notebook revision introduces randomized clustering, H4 must record the seed and H5 must require deterministic replay.

## Binary Fixture Discipline

- Prefer committed metadata, hashes, manifests, and small derived text artifacts.
- Prefer keeping large notebook exports outside the repo unless there is an explicit acceptance decision.
- If binary fixtures are added later, record why smaller reference material was insufficient.
