# Raster/Tensor Parity Alias Contract

## Purpose

Phase 3 adds notebook-compatible alias support for raster and tensor outputs the app already computes. It maps existing app-native files into the notebook parity tree with preserved notebook names and manifest entries.

Phase 3 is alias/copy only. It does not change raster math, SAR math, Sentinel-2 formulas, DEM formulas, thermal formulas, PCA logic, object extraction logic, classifier logic, Earth Engine calls, API routes, frontend behavior, database models, migrations, artifact serving policy, existing output names, or pipeline stage formulas.

## Alias Behavior

The helper creates a run-local alias plan from an app-native source path to a notebook parity path, verifies that the source file exists, copies the bytes into `data/runs/<run_id>/parity/`, and writes Phase 1 parity manifest entries.

Runtime output presence is marked as verified only after the source exists and the copy succeeds. Notebook-value parity remains `false` by default because it still requires later comparison against a frozen notebook reference.

Missing source files are reported honestly. The helper does not fabricate files, synthesize rasters, or compute replacement outputs.

## Default Manifest Metadata

Alias entries default to:

```text
target_mode: notebook_parity
classification: notebook-parity
http_servable: false
requires_coordinates: false
probability_only_required: false
runtime_output_verified: true after copy
notebook_value_parity_verified: false
```

No alias entry defaults to `public_shared`. No alias entry defaults to HTTP serving.

TIF aliases are recorded as `LOCAL_SENSITIVE`. NPY tensor aliases are recorded as `FILESYSTEM_ONLY`. These manifest classes do not register database artifacts and do not change existing artifact serving behavior.

## DEM / Terrain Aliases

| App-native source | Notebook parity path |
| --- | --- |
| `dem.tif` | `parity/DEM_GEO8_TIFS/DEM_640.tif` |
| `slope.tif` | `parity/DEM_GEO8_TIFS/slope_deg_640.tif` |
| `aspect.tif` | `parity/DEM_GEO8_TIFS/aspect_deg_640.tif` |
| `roughness.tif` | `parity/DEM_GEO8_TIFS/roughness_100m_640.tif` |
| `TPI.tif` | `parity/DEM_GEO8_TIFS/tpi_100m_640.tif` |
| `hillshade.tif` or `DEM_GEO8_TIFS/hillshade_0to1_640.tif` when present | `parity/DEM_GEO8_TIFS/hillshade_0to1_640.tif` |

The helper does not create missing curvature variants.

## SAR / Radar Aliases

| App-native source | Notebook parity path |
| --- | --- |
| `VV_dB.tif` | `parity/GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif` |
| `VH_dB.tif` | `parity/GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif` |
| `logRatio_dB.tif` | `parity/GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif` |
| `incidence.tif` | `parity/GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif` |
| `npy_radar_bands/VV_dB.npy` | `parity/NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy` |
| `npy_radar_bands/VH_dB.npy` | `parity/NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy` |
| `npy_radar_bands/logRatio_dB.npy` | `parity/NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy` |
| `npy_radar_bands/incidence.npy` | `parity/NPY_RADAR_BANDS/RADAR_angle_640_app.npy` |

The helper does not generate separate ASC/DESC filtered SAR products or pre-RTC intermediates.

## Hypercube / Tensor Aliases

| App-native source | Notebook parity path |
| --- | --- |
| `hypercube.tif` | `parity/NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` |
| `hypercube.npy` | `parity/NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` |
| `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` or `FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` when present | `parity/NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` |
| `NPY_STACKS/RADAR_STACK_HWC_640_app.npy` when present | `parity/NPY_STACKS/RADAR_STACK_HWC_640_app.npy` |

The helper does not generate a 2.5 m resampled hypercube, filtered S1 layer stack, panchromatic stack, AI behavior series, report rasters, secret layers, or new tensor products.

## Missing Source Handling

If no configured source candidate exists for an alias, the helper raises a clear missing-source error naming the alias and checked source paths. Later integration may choose to collect those statuses into a broader parity report, but Phase 3 does not silently skip or fabricate outputs.

Path traversal is blocked for both source paths and parity target paths. All resolved paths must stay under the run directory.

## Relationship To Later Phases

Phase 4 handles missing notebook raster families and any source-equivalent generation that requires formulas, Earth Engine calls, model logic, resampling, or additional scientific decisions.

Phase 3 only copies bytes that already exist in the run directory and records source-to-notebook alias mappings for later notebook-reference comparison.
