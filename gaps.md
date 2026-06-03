# Notebook-to-App Gaps for Faithful Parity

**Project:** GEE Screening  
**Source review:** `Notebook cells.md`, repository docs, and current app code  
**Primary goal:** Convert the notebook to a Python app as faithfully as possible, while keeping execution modes clear.

---

## 1. Correct framing

The challenge is not to remove notebook behavior.

The challenge is to convert the notebook into a Python app and preserve what the notebook does, including its output families, file names, folder structure, and experimental/classifier outputs where technically feasible.

Notebook outputs should be tracked as notebook-parity requirements. They should not be lost merely because the core app or public UI does not expose them.

This document separates:

1. outputs that must be reproduced for notebook parity;
2. outputs already covered by the app, renamed, corrected, or partially covered;
3. outputs that require private/parity-mode handling rather than clean/core exposure;
4. outputs that may require staged implementation because they depend on Earth Engine, model weights, Colab-only behavior, or unavailable source data;
5. outputs whose stage-file existence is known but whose runtime output/parity status is not yet proven.

---

## 2. Important correction: file existence is not parity proof

A Python stage file existing in the repo is not enough to mark a notebook output as implemented.

Before an output can be treated as implemented or authoritative, the relevant stage file must be opened and confirmed for:

- stage class name;
- `stage.name`;
- artifact names written;
- relative paths written;
- artifact class;
- `http_servable` setting;
- formulas or source inputs if visible;
- whether the output is app-native, notebook-compatible alias, semantic/report raster, QA/provenance, coordinate-bearing, or experimental/private;
- whether runtime output presence has been proven;
- whether notebook-value parity has been proven.

If a file exists but runtime output presence or value parity has not been verified, use:

```text
unknown_needs_verification
```

Do not mark an output as implemented from filename existence alone.

---

## 3. Classification correction: `secret_layers.py` and `report_640.py`

`app/pipeline/stages/secret_layers.py` and `app/pipeline/stages/report_640.py` must not be classified as clean defensible core by default.

Correct classification:

```text
secret_layers.py  -> notebook-parity semantic raster stage
report_640.py     -> notebook-parity report/semantic raster stage
```

They can be preserved for faithful notebook conversion, but they should not be grouped with neutral core science stages unless the document clearly qualifies them as notebook-parity semantic/report outputs.

Clean/core examples are closer to:

- GRID;
- DEM;
- SAR RTC;
- Sentinel-2 indices;
- DEM derivatives;
- thermal;
- hypercube assembly;
- PCA anomaly;
- object extraction;
- QA/alignment.

Notebook-parity semantic/report examples are:

- `AI_READY_640_Secret_*` layers;
- `AI_BEH_*` layers;
- `REPORT_640_Pottery_Report.tif`;
- `REPORT_640_Mass_Report.tif`;
- `REPORT_640_FINAL_Zero_Point_Targets.tif`.

These outputs may be valuable parity targets, but they need explicit verification of code path, runtime presence, formulas, metadata, and notebook parity.

---

## 4. Scope decision

Excluded from this gap register by project-owner decision:

- Interactive Colab point picker / map workflow.

That feature is not required as a parity gap at this time.

Everything else from the notebook should be evaluated as a parity target unless explicitly rejected later.

---

## 5. Required mode separation

To preserve the notebook as-is without mixing conversion fidelity with the clean app workflow, the app should support clear output modes.

### 5.1 Core app mode

Purpose:

- controlled pipeline execution;
- stable backend workflow;
- run status;
- artifact tracking;
- current clean app behavior.

This mode may use app-native names and controlled outputs.

### 5.2 Notebook parity mode

Purpose:

- reproduce notebook output families;
- preserve original notebook names where needed;
- preserve original folder conventions where needed;
- preserve original report/classifier/KMZ/GeoJSON/CSV outputs where technically feasible;
- produce an auditable output tree for comparison against notebook reference output.

This mode may include original notebook names such as:

```text
AI_BEH_*
AI_READY_*
REPORT_640_*
FINAL_TESLA_V7_2_*
RADAR_*_640_*
```

### 5.3 Experimental/private mode

Purpose:

- run classifier or model-derived outputs that are not part of the clean core pipeline;
- preserve notebook logic for audit and experimentation;
- keep original notebook labels when required for conversion fidelity;
- optionally write neutral aliases beside original names.

### 5.4 Public/shared mode

Purpose:

- future controlled sharing;
- redacted summaries;
- no accidental exposure of internal/private artifacts.

Public/shared mode is separate from notebook parity mode. A parity artifact can exist privately without becoming public UI functionality.

---

## 6. Highest-priority true parity gaps

### 6.1 Full v6 paid-archive package outputs

Notebook outputs:

```text
lawful_gee_candidate_scout_top_25_<timestamp>.csv
lawful_gee_candidate_scout_top_25_<timestamp>.geojson
top25_enhanced_v6.csv
top25_enhanced_v6.geojson
quality_diagnostics_all_cells_v6.csv
stable_candidate_priority_list_v6.csv
request_zones_v6.csv
request_zones_v6.geojson
paid_imagery_quote_template_v6.csv
paid_imagery_quote_comparison_v6.csv
paid_archive_request_summary.txt
visual_inspection_map.html
paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip
```

Current app gap:

The app does not yet provide a complete v6 package import/export parity path that validates these files, stores provenance, and exposes them as structured run outputs.

Required parity goal:

Implement `gee-import-v6` or equivalent so the app can accept or reproduce the v6 package and keep every expected package file available under the run output tree.

Priority: Critical.

---

### 6.2 Candidate tables and ranking outputs

Notebook ranking fields include:

```text
candidate_score
quality_adjusted_score
review_priority_score
confidence_score_all
stability_score
top10_count
top25_count
avg_rank
season_top10_count
season_top25_count
season_avg_rank
season_score_mean
season_score_std
score_gap_from_median
score_gap_to_next_rank
balanced_rank
visibility_heavy_rank
contrast_heavy_rank
terrain_heavy_rank
false_positive_warning_count
```

Current app gap:

The app can produce PCA anomaly and object extraction outputs, but those are not a full replacement for the notebook’s v6 candidate ranking tables.

Required parity goal:

Reproduce or import:

```text
top25_enhanced_v6.csv
top25_enhanced_v6.geojson
stable_candidate_priority_list_v6.csv
quality_diagnostics_all_cells_v6.csv
```

Priority: Critical.

---

### 6.3 Request-zone outputs

Notebook outputs:

```text
request_zones_v6.csv
request_zones_v6.geojson
```

Required parity goal:

Add request-zone import/export support preserving notebook fields such as:

```text
zone_id
geometry
centroid
area estimate
included candidate IDs
candidate count
max candidate score
mean review priority score
max confidence score
minimum false-positive warning count
reason summary
recommended imagery specs
```

Priority: Critical.

---

### 6.4 Paid imagery quote outputs

Notebook outputs:

```text
paid_imagery_quote_template_v6.csv
paid_imagery_quote_comparison_v6.csv
```

Required parity goal:

Add quote-row persistence and parity exports preserving fields such as provider, zone, candidate coverage, acquisition date, sensor, resolution, cloud cover, off-nadir angle, license, price, delivery time, coverage score, metadata completeness, and notes.

Priority: High.

---

## 7. Notebook raster and tensor parity gaps

### 7.1 DEM / terrain output family

Notebook outputs:

```text
DEM_640.tif
slope_deg_640.tif
aspect_deg_640.tif
roughness_100m_640.tif
tpi_100m_640.tif
curv_laplacian_640.tif
curv_plan_640.tif
curv_profile_640.tif
hillshade_0to1_640.tif
```

Required parity goal:

Produce notebook-compatible DEM output names and folder structure in parity mode, even if the core app also writes cleaner internal names.

Priority: Medium-high.

---

### 7.2 SAR / radar output family

Notebook outputs:

```text
RADAR_VV_dB_640_*.tif
RADAR_VH_dB_640_*.tif
RADAR_logRatio_dB_640_*.tif
RADAR_angle_640_*.tif
RADAR_VV_dB_640_*.npy
RADAR_VH_dB_640_*.npy
RADAR_logRatio_dB_640_*.npy
RADAR_angle_640_*.npy
S1_ASC_VV_Filtered_640.tif
S1_ASC_VH_Filtered_640.tif
S1_DESC_VV_Filtered_640.tif
S1_DESC_VH_Filtered_640.tif
S1_ASC_VV_Filtered_640.npy
S1_ASC_VH_Filtered_640.npy
S1_DESC_VV_Filtered_640.npy
S1_DESC_VH_Filtered_640.npy
```

Required parity goal:

Reproduce the full notebook SAR output family in parity mode, including ASC/DESC support outputs if technically feasible.

Priority: High.

---

### 7.3 Pre-RTC SAR intermediate arrays

Notebook outputs:

```text
QA/sar/intermediates/per_image_products_db/*
QA/sar/intermediates/pair_median/*
QA/sar/intermediates/final_median_pre_rtc/*
QA/sar/intermediates/post_sample_pre_rtc/*
QA/sar/intermediates/post_rtc/*
QA/sar/intermediates/sar_intermediate_manifest.json
```

Required parity goal:

For notebook parity mode, either write the missing intermediate arrays or write a manifest explaining why a source-equivalent intermediate cannot be recovered. For faithful conversion, writing the arrays is preferred where technically possible.

Priority: Medium-high.

---

### 7.4 Optical / panchromatic output family

Notebook outputs:

```text
PAN_LS_Panchromatic_640.tif
PAN_S2_Panchromatic_10m_640.tif
PAN_LS_Panchromatic_640.npy
PAN_S2_Panchromatic_10m_640.npy
PAN_LAYERS_STACK_640.npy
```

Required parity goal:

Add parity-mode generation for panchromatic support outputs if they are required to match the notebook reference output.

Priority: Medium.

---

### 7.5 Hypercube / stacked tensor output family

Notebook outputs:

```text
FINAL_TESLA_V7_2_HYPERCUBE.tif
FINAL_TESLA_V7_2_HYPERCUBE.npy
FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
RADAR_STACK_HWC_640_*.npy
S1_FILTERED_LAYERS_STACK_640.npy
```

Required parity goal:

Preserve notebook names and stack shapes in parity mode. Add a stack manifest containing source layer list, band order, shape, dtype, nodata policy, source file mapping, and intentional differences.

Priority: High.

---

## 8. Notebook semantic/report raster parity gaps

These outputs should be preserved for parity if the goal is notebook conversion fidelity. They should not be silently renamed away unless parity aliases are also written.

### 8.1 `REPORT_640_*` rasters

Notebook outputs:

```text
REPORT_640_Pottery_Report.tif
REPORT_640_Mass_Report.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
```

Current code existence:

`report_640.py` exists and is intended to write these outputs, but Phase 0 must verify the stage source and mark runtime parity as unknown unless a real run proves it.

Required verification:

- exact filename;
- exact folder;
- artifact names;
- artifact class;
- formulas;
- source inputs;
- shape;
- transform;
- CRS;
- nodata policy;
- runtime output presence;
- notebook-value parity or accepted tolerance.

Required classification:

```text
notebook-parity report/semantic raster stage
```

Do not classify as clean defensible core by default.

Priority: High.

---

### 8.2 `AI_BEH_*` and `AI_READY_*` series

Notebook outputs:

```text
AI_BEH_* series
AI_READY_* series
AI_READY_640_Secret_* series
```

Examples:

```text
AI_READY_640_Secret_Gold_Halo
AI_READY_640_Secret_Silver_Oxide
AI_READY_640_Secret_Tunnel_Ceiling
AI_READY_640_Secret_Thermal_Inertia
AI_READY_640_Secret_Chemical_Protector
AI_READY_640_Secret_Hidden_Doors
```

Current code existence:

`secret_layers.py` exists and is intended to write `AI_READY_640_Secret_*` rasters, but Phase 0 must verify the stage source and mark runtime parity as unknown unless a real run proves it.

Required verification:

- layer names;
- formulas;
- source inputs;
- output folder;
- artifact class;
- manifest behavior;
- missing-source behavior;
- runtime output presence;
- notebook-value parity or accepted tolerance.

Required classification:

```text
notebook-parity semantic raster stage
```

Do not classify as clean defensible core by default.

Priority: High.

---

## 9. Classifier / model output parity gaps

### 9.1 Original classifier labels

Notebook labels include:

```text
Gold_Metal_Jar
Sarcophagus_Naos
Red_Mercury_Trace
Black_Mercury_Trace
Buried_Entrance
Weapons_Shield_Cache
Ancient_Well
```

Current app status:

The current app experimental module uses neutral `Class_A` through `Class_N` identifiers. That is good for clean app mode, but it is not full notebook parity if original labels are required.

Required parity goal:

Notebook parity mode should be able to preserve original classifier output labels when the goal is exact conversion fidelity.

Recommended output strategy:

```text
experimental/classifications_original.csv
experimental/classifications_neutral.csv
experimental/class_mapping.json
experimental/summary.json
```

Priority: Medium-high.

---

### 9.2 Deep learning model build/inference cells

Notebook behavior:

The notebook contains Swin, UnetPlusPlus, ResNet50, SegFormer, YOLO-style, and CNN inference/build attempts.

Required parity goal:

Track these cells separately because feasibility depends on package availability, runtime, model weights, training data, whether the cell was runnable, and whether source files exist.

Use explicit statuses such as:

```text
not_implemented_missing_weights
not_implemented_missing_training_data
not_implemented_broken_notebook_cell
not_implemented_dependency_unavailable
```

Priority: Medium.

---

## 10. Coordinate-bearing output parity

Notebook outputs:

```text
GeoJSON
KMZ
KML
CSV with lat/lon
Google Earth overlays
visual_inspection_map.html
field/navigation-style outputs
```

Correct framing:

These are notebook-parity outputs, not automatically public app features.

Required parity goal:

Preserve them in notebook parity/private output mode when the goal is to match the notebook.

Recommended output strategy:

```text
parity/location/*.geojson
parity/kmz/*.kmz
parity/maps/visual_inspection_map.html
parity/navigation/*.kml
parity/navigation/*.csv
```

Priority: High for parity, separate from public UI decisions.

---

## 11. QA / diagnostics / provenance parity gaps

Notebook outputs:

```text
QA_GRID_dx_m_640.tif
QA_GRID_dy_m_640.tif
QA_GRID_validmask_640.tif
QA_RADAR_CELL25_PAIR_IDS_*.json
QA_S1_MASTER_UNITS.json
QA_RADAR_META_*.json
SUMMARY_RADAR_*.csv
RUN_MANIFEST.json
sar_intermediate_manifest.json
```

Required parity goal:

Write notebook-compatible QA outputs in parity mode, even if the app also keeps its own cleaner manifests.

Required approach:

```text
app-native QA files remain
notebook-compatible QA aliases are also written
parity manifest maps native files to notebook files
```

Priority: High.

---

## 12. Colab / Drive behavior

The app does not need to reproduce Colab UI mechanics exactly.

The conversion target is:

```text
output-equivalent behavior, not Colab-mechanic-equivalent behavior
```

Examples:

- Do not need Drive mount if server storage writes the same files.
- Do not need Drive refresh if app output tree is complete.
- Do not need pip install cells if requirements are pinned.
- Do not need JS auto-scroll if app orchestration runs stages directly.

Not a direct parity output gap unless a Colab-only step produces a file that is missing from the app.

---

## 13. Known notebook bugs and parity policy

### 13.1 `IRON_SWIR` formula

Notebook note identified this bug:

```text
IRON_SWIR = (B11 - B12) / (B11 - B12)
```

The app currently uses the corrected form:

```text
(B11 - B12) / (B11 + B12)
```

Parity policy:

Document this as a corrected notebook bug. If strict bug-for-bug parity is ever needed, support it only behind an explicit compatibility flag.

Default should remain corrected behavior.

### 13.2 Broken constructor typo

Notebook cell 233 uses:

```python
def init(self)
```

instead of:

```python
def __init__(self)
```

Parity policy:

Do not reproduce broken code unless preserving it as a non-runnable source reference. Mark as:

```text
not_implemented_broken_notebook_cell
```

---

## 14. Current app strengths to preserve while adding parity

Preserve these strengths:

- service-account Earth Engine backend flow;
- run status lifecycle;
- stage manifests;
- artifact records;
- deterministic run directories;
- fixed GRID discipline;
- alignment QA;
- app-native artifact classes;
- app-native redaction/public-response controls;
- app-native API/frontend separation;
- app-native clean/core pipeline mode.

Adding notebook parity mode must not break the current core app pipeline.

---

## 15. Recommended implementation phases

### Phase 1 — Output inventory lock

Create an authoritative notebook-output inventory from `Notebook cells.md` and/or a frozen notebook output bundle.

Deliverables:

```text
docs/NOTEBOOK_OUTPUT_INVENTORY_LOCKED.md
parity_expected_outputs.json
```

Important Phase 1 rule:

Every status must be backed by source-file inspection or marked `unknown_needs_verification`. `secret_layers.py` and `report_640.py` must be classified as notebook-parity semantic/report raster stages, not clean defensible core.

### Phase 2 — Parity output tree design

Define where notebook-parity outputs live in the app run directory.

### Phase 3 — v6 package import/export parity

Implement candidate, request-zone, quote, summary, map, and zip package parity.

### Phase 4 — Raster/tensor parity

Implement or alias DEM, SAR, S2, thermal, report rasters, AI_READY/AI_BEH, hypercube, panchromatic, and stack outputs.

### Phase 5 — QA/intermediate parity

Implement notebook-compatible QA files, grid QA files, SAR pair diagnostics, and SAR intermediate arrays.

### Phase 6 — Classifier/model parity

Implement original-label classifier outputs in private parity mode, alongside optional neutral aliases.

### Phase 7 — End-to-end parity test

Run app vs frozen notebook output comparison.

Compare file presence, row counts, required columns, raster shapes, CRS/transform, nodata, band order, checksums where deterministic, and numeric tolerance where Earth Engine variability exists.

---

## 16. Final rule

The objective is faithful notebook-to-Python-app conversion.

Do not delete notebook outputs from the plan just because they are experimental, oddly named, duplicate, or not part of the clean UI.

Instead:

```text
preserve them in notebook parity/private mode;
map them clearly;
validate them;
then decide separately what, if anything, belongs in clean core app mode or public/shared mode.
```
