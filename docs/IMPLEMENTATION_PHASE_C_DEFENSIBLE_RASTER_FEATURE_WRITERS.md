# Implementation Phase C Defensible Raster Feature Writers

Phase C adds one small, source-driven writer slice for private notebook-parity semantic features.

## Selected Writer Family

Selected family:

- AI_BEH relation semantic features

Implemented outputs:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`

The implementation module is:

`app/pipeline/parity/semantic_feature_writers.py`

This module is private/parity-only. It is not wired into the live pipeline, API, frontend, or artifact-serving surface.

## Formula Evidence

The source evidence is locked by:

- `docs/AI_BEH_RELATION_PARITY_CONTRACT.md`
- `app/pipeline/parity/ai_beh_relation_recovery.py`

Those Phase 4H5 sources record notebook evidence around `notebooks/new.ipynb` lines `23418-23424` and later stack/candidate table references.

Implemented formulas:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640 = normalizedDifference(B8, B4)`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640 = B4 / B3`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640 = B11 / B12`

## Required Inputs

The writer requires same-shaped 2D arrays for:

- `B3`
- `B4`
- `B8`
- `B11`
- `B12`

Inputs with missing bands, non-2D arrays, or mismatched shapes are rejected.

## Metadata And Grid Policy

The Phase 4H5 contract records that frozen notebook references are still required to lock final exported TIFF metadata, including:

- dtype
- nodata or NaN policy
- CRS
- transform
- width
- height
- band count
- value tolerance

Phase C therefore does not claim final TIFF metadata parity. The writer preserves caller-supplied reference profile metadata in its returned private report and writes optional local `.npy` feature arrays under the provided run directory only.

Current dtype and nodata policy:

- computed arrays are `float32`
- unsafe ratio or normalized-difference denominators become `NaN`
- `.npy` outputs preserve `NaN`
- frozen references are still required before notebook-value parity can pass

## Safety Boundary

Phase C does not:

- call Earth Engine
- use Colab
- use Google Drive
- use interactive `ee.Authenticate()`
- start backend runs
- change existing raster, SAR, optical, DEM, PCA, GRID, classifier, or model math
- expose outputs through API or frontend
- change artifact-serving policy
- generate KMZ, KML, GeoJSON, HTML map, image, CSV, coordinate, classifier, or model artifacts
- implement Phase D, E, F, G, H, I, or J behavior

The selected AI_BEH relation outputs remain private notebook-parity features. They are not clean public/core outputs by default.

## Parity Status

Runtime output presence and notebook-value parity remain separate.

`notebook_value_parity_verified` remains `false` until frozen notebook references are captured and a reference comparison passes.

Phase C implements a narrow writer slice only. It does not make notebook-value parity pass by itself.
