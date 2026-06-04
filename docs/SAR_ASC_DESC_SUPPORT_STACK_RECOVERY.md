# SAR ASC/DESC Support Stack Recovery

## 1. Purpose

Phase 4E locks source-recovery and verification requirements for the notebook's separate ascending/descending Sentinel-1 support outputs:

```text
S1_ASC_VV_Filtered_640.tif
S1_ASC_VH_Filtered_640.tif
S1_DESC_VV_Filtered_640.tif
S1_DESC_VH_Filtered_640.tif
S1_ASC_VV_Filtered_640.npy
S1_ASC_VH_Filtered_640.npy
S1_DESC_VV_Filtered_640.npy
S1_DESC_VH_Filtered_640.npy
```

This phase determines what evidence is still required before implementation. It is investigation and contract only.

## 2. Scope

Phase 4E covers:

- current SAR stage source inspection;
- notebook source inspection;
- output-by-output status;
- source status classification;
- required inputs;
- frozen reference and metadata requirements;
- a machine-readable checklist/report helper.

Files inspected:

```text
notebook_gaps_coverage.md
gaps.md
docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md
docs/parity_expected_outputs.json
docs/PARITY_MODE_CONTRACT.md
docs/MISSING_RASTER_FAMILIES_CONTRACT.md
docs/SAR_SOURCE_SELECTION_PARITY.md
docs/SAR_PROCESSING_PARITY.md
app/pipeline/parity/missing_rasters.py
app/pipeline/stages/sar_rtc.py
app/pipeline/stages/feature_stacks.py
notebooks/new.ipynb
tests/notebook_parity/test_sar_parity.py
tests/unit/test_sar_rtc.py
```

## 3. Non-Goals

Phase 4E does not:

- implement ASC/DESC stack generation;
- change SAR math;
- change SAR RTC math;
- change SAR filtering logic;
- change selected image IDs;
- change pair selection;
- change orbit selection;
- change GRID behavior;
- generate SAR rasters;
- generate NPY arrays;
- alias final SAR outputs as ASC/DESC support stacks;
- call Earth Engine;
- integrate with the live pipeline;
- change API, frontend, database, migrations, classifier logic, or artifact serving.

No SAR math changed in Phase 4E.

## 4. Current App SAR Stage Findings

`app/pipeline/stages/sar_rtc.py` implements the app's SAR RTC path:

- builds a `COPERNICUS/S1_GRD` collection;
- filters to IW, 10 m, VV, VH, and angle;
- selects ASCENDING and DESCENDING collections;
- picks best tracks;
- applies orbit-window and pair-cap selection;
- applies dB-domain border mask, sigma Lee, Lee filtering, and dB-linear-dB transforms per image;
- aggregates ASC/DESC pairs and final pair median;
- samples to the locked grid;
- applies local DEM RTC in local NumPy;
- writes final app-native root outputs:

```text
VV_dB.tif
VH_dB.tif
logRatio_dB.tif
incidence.tif
```

It also writes notebook-compatible final radar aliases:

```text
GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif
GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif
GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif
GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif
NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy
NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy
NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy
NPY_RADAR_BANDS/RADAR_angle_640_app.npy
```

Those outputs are final RTC/fused products. They are not separate ASC/DESC filtered support stacks.

`app/pipeline/stages/feature_stacks.py` consumes final SAR outputs and writes support stacks such as `radar_db_support_stack.*`, `radar_linear_support_stack.*`, and `NPY_STACKS/RADAR_STACK_HWC_640_app.npy`. It does not write the separate `S1_ASC_*` or `S1_DESC_*` notebook support outputs.

## 5. Notebook Source Findings

`notebooks/new.ipynb` contains a distinct Sentinel-1 filtered-layer export block around lines 26199-26308. The source block:

- builds `ee.ImageCollection('COPERNICUS/S1_GRD')`;
- filters by grid region and date range `2022-01-01` to `2026-03-01`;
- filters for IW mode and VV/VH polarizations;
- selects the newest ASCENDING image:

```text
s1_collection.filter(orbitProperties_pass == ASCENDING).sort(system:time_start, False).first()
```

- selects the newest DESCENDING image:

```text
s1_collection.filter(orbitProperties_pass == DESCENDING).sort(system:time_start, False).first()
```

- applies a simple speckle filter:

```text
image.focal_mean(radius=1.5, kernelType='circle', units='pixels')
```

- grid-aligns each selected VV/VH band;
- samples a 640 x 640 cube in 2 x 2 tiles;
- writes one GeoTIFF and one NPY per processed band;
- writes `NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy`.

This is exact notebook source evidence for the separate support-stack family. It is not the same processing path as the app's final RTC products.

## 6. Output-By-Output Status Table

| Output | Current app status | Source status | Implementation status | Runtime verified | Notebook-value parity verified |
| --- | --- | --- | --- | --- | --- |
| `S1_ASC_VV_Filtered_640.tif` | Missing; final RTC VV is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_ASC_VH_Filtered_640.tif` | Missing; final RTC VH is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_DESC_VV_Filtered_640.tif` | Missing; final RTC VV is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_DESC_VH_Filtered_640.tif` | Missing; final RTC VH is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_ASC_VV_Filtered_640.npy` | Missing; final RTC VV NPY is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_ASC_VH_Filtered_640.npy` | Missing; final RTC VH NPY is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_DESC_VV_Filtered_640.npy` | Missing; final RTC VV NPY is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |
| `S1_DESC_VH_Filtered_640.npy` | Missing; final RTC VH NPY is not equivalent. | `exact_source_found` | `requires_reference_output` | false | false |

## 7. Formula/Source Status

Allowed source statuses:

```text
exact_source_found
partial_source_found
no_source_found
existing_app_equivalent_found
unknown_needs_reference
```

All eight required outputs are classified as:

```text
exact_source_found
```

The source is exact because the notebook block explicitly names the collection, orbit-pass filters, VV/VH selections, speckle filter, grid alignment, per-band GeoTIFF/NPY writes, and stack write.

The current app does not have an existing equivalent. The app's final SAR RTC products must not be treated as equivalent because they are fused, paired, median-composited, locally RTC-corrected products, while the notebook support block exports separate newest-pass filtered layers.

## 8. Required Inputs

Known required inputs:

- Sentinel-1 collection: `COPERNICUS/S1_GRD`;
- orbit pass: `ASCENDING` or `DESCENDING`;
- bands: `VV` and `VH`;
- filtering/masking: notebook block uses `focal_mean(radius=1.5, kernelType='circle', units='pixels')`;
- median/composite logic: no median in the support block; newest image per pass is selected with descending time sort and `first()`;
- RTC or pre-RTC status: appears pre-local-RTC; not equivalent to app final RTC outputs;
- scaling/unit convention: native Sentinel-1 GRD band values after focal mean, final units must be verified from frozen reference outputs;
- GRID alignment: `to_grid_aligned(...)` and 640 x 640 tiled sampling;
- nodata policy: notebook `NODATA` and rasterio profile nodata.

## 9. Implementation Risk

Implementation risk is medium-high:

- source text exists, but frozen outputs are not yet available;
- Earth Engine image availability may change unless exact image IDs are captured;
- newest-image selection is date-window dependent and less stable than explicit pair IDs;
- support layers are not local DEM RTC outputs;
- final app SAR products cannot be used as aliases;
- NPY/TIF parity requires metadata and value comparison.

The safest next step is a verifier/reference-capture task, not implementation.

## 10. Required Tests For Later Implementation

A later implementation slice must test:

- all eight per-band files are produced under notebook-compatible folders;
- `S1_FILTERED_LAYERS_STACK_640.npy` shape and band order when that stack family is implemented;
- original notebook filenames are preserved;
- ASC and DESC pass outputs are not swapped;
- VV and VH outputs are not swapped;
- CRS, transform, width, height, dtype, nodata, and band count match frozen references;
- numeric values match frozen references within locked tolerances;
- outputs remain private/notebook parity and do not default to public/shared exposure;
- final RTC outputs are not aliased as separate ASC/DESC support stacks.

## 11. Required Frozen Notebook Outputs

Required frozen references:

```text
GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif
NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy
```

The related stack output should be captured for a later tensor task:

```text
NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy
```

## 12. Required Reference Metadata/Tolerance Expectations

Reference metadata must lock:

- CRS;
- transform;
- pixel size;
- width and height;
- dtype;
- nodata;
- band count;
- unit convention;
- filtering status;
- RTC or pre-RTC status;
- date window;
- selected ASC/DESC image IDs;
- selected acquisition timestamps.

Numeric verification must record:

- max absolute difference;
- mean absolute difference;
- compared pixel count;
- nodata or NaN pixel count;
- within-tolerance status;
- exact TIF-vs-NPY consistency for each band where applicable.

## 13. Recommended Phase 4E2 Plan

Recommended Phase 4E2 target:

```text
ASC/DESC support-stack reference capture and verifier
```

The next slice should:

1. accept an app or notebook reference directory;
2. verify presence of all eight per-band references;
3. parse TIF metadata and NPY shapes/dtypes when dependencies are available;
4. compare TIF and NPY values within each notebook reference pair;
5. record selected image IDs and timestamps if available;
6. avoid Earth Engine unless an explicit later reference-capture task is approved;
7. keep implementation blocked until frozen references and tolerance expectations are locked.

Only after the verifier/reference contract passes should a later task implement the notebook source path.

## 14. Confirmation

Phase 4E added only a recovery contract, checklist/report helper, and tests. It did not change SAR math, SAR RTC math, source selection, orbit selection, pair selection, GRID behavior, raster math, API/frontend/database code, artifact serving, existing output names, or Earth Engine behavior. It did not generate rasters or NPY arrays.
