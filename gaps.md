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
4. outputs that may require staged implementation because they depend on Earth Engine, model weights, Colab-only behavior, unavailable source data, or labeled training data;
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
- whether the output is app-native, notebook-compatible alias, semantic/report raster, QA/provenance, coordinate-bearing, experimental/private, or probability-classifier output;
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

## 4. Probability-only classifier rule

Future ML/classifier outputs must be probability-based, not confirmation-based.

Allowed wording patterns:

```text
probability
class probability
model-estimated probability
likelihood score
probability band
candidate resembles training examples
```

Allowed example output shape:

```text
object_id: 17
top_class: tomb_like
class_probability: 0.36
probability_band: 30-40%
model_version: tomb_classifier_v0.1
calibration_status: uncalibrated_or_calibrated
```

Forbidden output meaning:

```text
confirmed
found
proven
dig target
definitely
```

The app may support labels such as `tomb_like_probability` or `Buried_Entrance_probability` in private/parity/experimental mode, but the value must be documented as a model probability or score, never as confirmation.

If there is no labeled/calibrated dataset, the output must be called a heuristic score or uncalibrated model score, not a calibrated probability.

---

## 5. Scope decision

Excluded from this gap register by project-owner decision:

- Interactive Colab point picker / map workflow.

That feature is not required as a parity gap at this time.

Everything else from the notebook should be evaluated as a parity target unless explicitly rejected later.

---

## 6. Required mode separation

To preserve the notebook as-is without mixing conversion fidelity with the clean app workflow, the app should support clear output modes.

### 6.1 Core app mode

Purpose:

- controlled pipeline execution;
- stable backend workflow;
- run status;
- artifact tracking;
- current clean app behavior.

This mode may use app-native names and controlled outputs.

### 6.2 Notebook parity mode

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

### 6.3 Experimental/private mode

Purpose:

- run classifier or model-derived outputs that are not part of the clean core pipeline;
- preserve notebook logic for audit and experimentation;
- keep original notebook labels when required for conversion fidelity;
- optionally write neutral aliases beside original names;
- support probability-only ML classifier outputs.

### 6.4 Public/shared mode

Purpose:

- future controlled sharing;
- redacted summaries;
- no accidental exposure of internal/private artifacts.

Public/shared mode is separate from notebook parity mode. A parity artifact can exist privately without becoming public UI functionality.

---

## 7. Highest-priority true parity gaps

### 7.1 Full v6 paid-archive package outputs

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

### 7.2 Candidate tables and ranking outputs

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

### 7.3 Request-zone outputs

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

### 7.4 Paid imagery quote outputs

Notebook outputs:

```text
paid_imagery_quote_template_v6.csv
paid_imagery_quote_comparison_v6.csv
```

Required parity goal:

Add quote-row persistence and parity exports preserving fields such as provider, zone, candidate coverage, acquisition date, sensor, resolution, cloud cover, off-nadir angle, license, price, delivery time, coverage score, metadata completeness, and notes.

Priority: High.

---

## 8. Notebook raster and tensor parity gaps

### 8.1 DEM / terrain output family

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

### 8.2 SAR / radar output family

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

### 8.3 Pre-RTC SAR intermediate arrays

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

### 8.4 Optical / panchromatic output family

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

### 8.5 Hypercube / stacked tensor output family

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

## 9. Notebook semantic/report raster parity gaps

These outputs should be preserved for parity if the goal is notebook conversion fidelity. They should not be silently renamed away unless parity aliases are also written.

### 9.1 `REPORT_640_*` rasters

Notebook outputs:

```text
REPORT_640_Pottery_Report.tif
REPORT_640_Mass_Report.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
```

Current code existence:

`report_640.py` exists and is intended to write these outputs, but Phase 0 must verify the stage source and mark runtime parity as unknown unless a real run proves it.

Required classification:

```text
notebook-parity report/semantic raster stage
```

Do not classify as clean defensible core by default.

Priority: High.

---

### 9.2 `AI_BEH_*` and `AI_READY_*` series

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

Required classification:

```text
notebook-parity semantic raster stage
```

Do not classify as clean defensible core by default.

Priority: High.

---

## 10. Classifier / model output parity gaps

### 10.1 Original classifier labels

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

### 10.2 Probability-only ML classifier

Goal:

Add a future classifier design that can output class probabilities or calibrated probability bands for candidate objects.

Example output fields:

```text
object_id
cluster_id
top_class
class_probability
probability_band
top_3_classes
model_version
training_dataset_version
calibration_status
explanation_features
```

Possible class names can be explicit but must remain probability-based:

```text
tomb_like_probability
entrance_like_probability
mound_like_probability
wall_or_linear_feature_like_probability
natural_terrain_probability
modern_disturbance_probability
vegetation_or_crop_artifact_probability
unknown_probability
```

Probability quality levels:

```text
heuristic_score                  # no labeled/calibrated dataset
uncalibrated_model_probability   # trained model, not calibrated
calibrated_model_probability     # validation/calibration evidence exists
```

Required training data for meaningful probabilities:

- positive examples;
- negative examples;
- train/validation split;
- confusion matrix;
- calibration report;
- model/data versioning.

Priority: Future high, after parity inventory and candidate/object persistence are stable.

---

### 10.3 Deep learning model build/inference cells

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

## 11. Coordinate-bearing output parity

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

Priority: High for parity, separate from public UI decisions.

---

## 12. QA / diagnostics / provenance parity gaps

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

Priority: High.

---

## 13. Colab / Drive behavior

The app does not need to reproduce Colab UI mechanics exactly.

The conversion target is:

```text
output-equivalent behavior, not Colab-mechanic-equivalent behavior
```

Not a direct parity output gap unless a Colab-only step produces a file that is missing from the app.

---

## 14. Known notebook bugs and parity policy

### 14.1 `IRON_SWIR` formula

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

### 14.2 Broken constructor typo

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

## 15. Current app strengths to preserve while adding parity

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

## 16. Recommended implementation phases

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

### Phase 7 — Probability-only ML classifier design

Design probability-based candidate classification with class probabilities, probability bands, model versioning, dataset versioning, calibration status, and explicit prohibition of confirmation wording.

### Phase 8 — End-to-end parity test

Run app vs frozen notebook output comparison.

Compare file presence, row counts, required columns, raster shapes, CRS/transform, nodata, band order, checksums where deterministic, and numeric tolerance where Earth Engine variability exists.

---

## 17. Final rule

The objective is faithful notebook-to-Python-app conversion.

Do not delete notebook outputs from the plan just because they are experimental, oddly named, duplicate, or not part of the clean UI.

Use probability-only language for ML/classifier outputs. Do not use confirmation language.

Instead:

```text
preserve notebook outputs in notebook parity/private mode;
map them clearly;
validate them;
represent classifier results as probabilities or scores;
then decide separately what belongs in clean core app mode or public/shared mode.
```
