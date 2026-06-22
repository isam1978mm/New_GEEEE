# Current parity checklist

Status: active checklist snapshot for the current parity/recovery workflow.

No private payloads, raster data, NPY data, CSV rows, SAR JSON bodies, image identifiers, coordinates, or per-pixel values are included.

## Legend

```text
[x] closed / passed / documented
[~] diagnostic-only or partially closed
[ ] open
```

## Reference bundle and safety gates

```text
[x] D1C reference bundle validation
    [x] reference bundle valid
    [x] expected S1/SAR/PAN/stack files located where needed
    [x] manifest mentions verified for located targets

[x] local-only boundary
    [x] no public downloads
    [x] no HTTP table/array serving
    [x] no map overlays
    [x] safe aggregate reporting only
```

## INT1 / internal raster work

```text
[x] INT1 internal raster generation/diagnostic support
    [x] unit/integration/notebook parity tests recovered after loader signature fix
    [x] diagnostic payload remains local-safe
    [x] internal raster verifier result documented
```

## S1/SAR reference and component parity

```text
[x] S1-1 core-band real app-vs-reference parity
    [x] D2-valid S1-1 reference files located
    [x] app outputs located
    [x] VV/VH ASC/DESC TIF values passed
    [x] VV/VH ASC/DESC NPY values passed
    [x] raw file hashes may differ for TIF containers, but value parity passed

[x] S1 filtered layers stack parity
    [x] S1_FILTERED_LAYERS_STACK_640.npy located
    [x] app/reference shape and dtype matched
    [x] hash_match true
    [x] max_abs_diff 0.0
    [x] mean_abs_diff 0.0
```

## PAN / optical panchromatic parity

```text
[x] PAN canonical reference selection
    [x] duplicate PAN files detected in radar-like and OPT directories
    [x] OPT/PAN_* selected as canonical because PAN_LAYERS_STACK_640.npy matches OPT/PAN_NPY_640 components exactly

[x] PAN component parity
    [x] PAN_LS_Panchromatic_640.tif passed
    [x] PAN_S2_Panchromatic_10m_640.tif passed
    [x] PAN_LS_Panchromatic_640.npy passed
    [x] PAN_S2_Panchromatic_10m_640.npy passed

[x] PAN stack parity
    [x] PAN_LAYERS_STACK_640.npy passed within numeric tolerance
```

## AI-ready / object CSV support

```text
[x] AI-ready support stack reference handling
    [x] clarified that named AI_READY_* target rasters were not present in the searched D1C/app roots
    [x] ai_ready_support_stack.npy located and compared against app runs
    [x] a11309bf app run matched the located reference exactly
    [x] e11d3280 app run differed and was not used as the matching reference

[x] object/cluster CSV parity
    [x] objects_index.csv reference located
    [x] clusters_summary.csv reference located
    [x] app/reference hash_match true for objects_index.csv
    [x] app/reference hash_match true for clusters_summary.csv
    [x] schemas and row counts matched
```

## SAR source-selection and processing

```text
[x] SAR app-native QA/report parity
    [x] SAR QA JSON/CSV app/reference hash checks passed for inspected QA artifacts

[x] SAR source-selection identity
    [x] Cell 25 source identity matched
    [x] image identity matched
    [x] orbit pairing matched
    [x] pair count matched
    [x] source parameters matched
    [x] collection_id and orbit/track fields recoverable from Cell 25 sidecar

[x] SAR processing-path metadata classification
    [x] D1C metadata proves LOCAL_DEM_RTC / DBONLY / RTC
    [x] notebook source supports border/noise, dB-linear-dB, Lee, sigma-Lee, sampleRectangle, local DEM RTC terms
    [x] processing_path mismatch classified as metadata-detail/documentation gap, not source-image mismatch

[x] SAR core band processing parity
    [x] VV_dB raster passed
    [x] VV_dB NPY passed
    [x] VH_dB raster passed
    [x] VH_dB NPY passed
    [x] logRatio_dB raster passed
    [x] logRatio_dB NPY passed
    [x] incidence raster passed
    [x] incidence NPY passed

[x] SAR full app intermediate capture
    [x] app full Cell 25 intermediates exported locally
    [x] full-intermediate processing parity rerun
    [x] first divergence candidate identified at per_image_products_db

[~] SAR per_image_products_db row-shift diagnostic
    [x] label/order mismatch ruled out
    [x] dB-vs-linear domain mismatch ruled out
    [x] formula-parameter mismatch mostly ruled out
    [x] nodata/mask disagreement as main cause ruled out
    [x] flip/transpose mismatch ruled out
    [x] systematic VV/VH one-row offset identified
    [x] global vs per-tile shift tested; not isolated to tile-boundary placement
    [~] retained as diagnostic-only against frozen intermediates because final outputs pass

[x] SAR intermediate generator search
    [x] searched New_GEE, New_GEE_REFERENCE, and data/private_references
    [x] existing manifests located
    [x] app exporter/services/tests/docs located
    [x] notebook-side full intermediate generator not located
    [x] visible notebook final Cell 24 sampling matches app sampling pattern

[x] radar DB support stack / notebook alias parity
    [x] app radar_db_support_stack vs D1C raw RADAR_STACK_HWC reference passed within tolerance
    [x] NPY_STACKS/RADAR_STACK_HWC_640_app.npy vs D1C raw RADAR_STACK_HWC reference passed within tolerance

[x] radar linear support stack parity
    [x] direct linear-vs-raw dB 25 percent diagnostic explained as expected unit-contract mismatch
    [x] notebook raw dB reference converted to linear contract
    [x] app radar_linear_support_stack passed converted-reference contract within tolerance

[x] SAR summary-stat reconciliation
    [x] exact notebook summary CSV selected by the report was located
    [x] schema mismatch identified: app nodata_count vs notebook nodata_px
    [x] band-name mapping identified: incidence maps to notebook angle
    [x] numeric min/max/mean differences classified as rounded summary-format deltas
    [x] app final NPY stats recomputed and aligned with app summary at expected precision
    [x] closed as report-summary schema/formatting issue, not underlying SAR raster/NPY failure
```

## Current opening item

```text
[ ] Final clean working tree check
```

Main subitems for the current opening item:

```text
[x] targeted closeout tests passed: 22 passed, 1 warning
[x] full pytest suite passed: 1656 passed, 40 skipped, 2 warnings
[ ] confirm git status is clean after docs/code updates
```

## Final closeout still needed

```text
[x] Run final targeted tests for touched parity/SAR docs and scripts: 22 passed, 1 warning
[x] Run full pytest suite: 1656 passed, 40 skipped, 2 warnings
[ ] Confirm git status is clean after docs/code updates
```
