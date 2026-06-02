# Notebook-to-App Gaps for Faithful Parity

**Project:** GEE Screening  
**Source review:** `Notebook cells.md`, repository docs, and current app code  
**Primary goal:** Convert the notebook to a Python app as faithfully as possible, while keeping execution modes clear.

---

## 1. Correct framing

The challenge is not to remove notebook behavior.

The challenge is to convert the notebook into a Python app and preserve what the notebook does, including its output families, file names, folder structure, and experimental/classifier outputs where technically feasible.

Earlier wording that treated some notebook outputs as simply “risky” or “intentional omissions” is not the right framing for this conversion goal.

Correct framing:

```text
The notebook outputs should be tracked as notebook-parity requirements.
The app may keep them in a private/parity/experimental mode.
They should not be lost merely because the core app or public UI does not expose them.
```

This document therefore separates:

1. outputs that must be reproduced for notebook parity;
2. outputs already covered by the app, renamed, corrected, or partially covered;
3. outputs that require private/parity-mode handling rather than public/product exposure;
4. outputs that may require staged implementation because they depend on Earth Engine, model weights, Colab-only behavior, or unavailable source data.

---

## 2. Scope decision

Excluded from this gap register by project-owner decision:

- Interactive Colab point picker / map workflow.

That feature is not required as a parity gap at this time.

Everything else from the notebook should be evaluated as a parity target unless explicitly rejected later.

---

## 3. Required mode separation

To preserve the notebook “as is” without confusing it with the app’s clean review workflow, the app should support clear output modes.

### 3.1 Core app mode

Purpose:

- controlled pipeline execution;
- stable backend workflow;
- run status;
- artifact tracking;
- current clean app behavior.

This mode may use neutral names and controlled outputs.

### 3.2 Notebook parity mode

Purpose:

- reproduce notebook output families;
- preserve original notebook names where needed;
- preserve original folder conventions where needed;
- preserve original report/classifier/KMZ/GeoJSON/CSV outputs where technically feasible;
- produce an auditable output tree for comparison against notebook reference output.

This mode may include original notebook names such as `AI_BEH_*`, `AI_READY_*`, `REPORT_640_*`, `FINAL_TESLA_V7_2_*`, and original classifier labels if the goal is exact conversion fidelity.

### 3.3 Experimental/private mode

Purpose:

- run classifier or model-derived outputs that are not part of the core pipeline;
- preserve notebook logic for audit and experimentation;
- avoid blocking conversion fidelity because the label names are experimental.

This mode can keep original notebook labels if required for parity, while also optionally writing neutral aliases.

### 3.4 Public/shared mode

Purpose:

- future controlled sharing;
- redacted summaries;
- no accidental exposure of internal/private artifacts.

Public/shared mode is separate from notebook parity mode. A parity artifact can exist privately without being public UI functionality.

---

## 4. Highest-priority true parity gaps

These are the most important gaps to close to make the Python app match the notebook workflow.

---

### 4.1 Full v6 paid-archive package outputs

#### Notebook outputs

The notebook can produce the final v6 candidate/request/quote package:

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

#### Current app gap

The app does not yet provide a complete v6 package import/export parity path that validates these files, stores provenance, and exposes them as structured run outputs.

#### Required parity goal

Implement `gee-import-v6` or equivalent so the app can accept or reproduce the v6 package and keep every expected package file available under the run output tree.

Required behavior:

1. validate all required files;
2. validate schemas;
3. store package/file hashes;
4. persist imported candidates;
5. persist imported request zones;
6. persist imported quote rows;
7. preserve original v6 filenames;
8. write a parity manifest proving what was imported or reproduced.

#### Priority

Critical.

---

### 4.2 Candidate tables and ranking outputs

#### Notebook outputs

The notebook can produce candidate tables with ranking and quality fields such as:

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

#### Current app gap

The app can produce PCA anomaly and object extraction outputs, but those are not a full replacement for the notebook’s v6 candidate ranking tables.

#### Required parity goal

Add candidate persistence and export so the app can preserve notebook candidate-table semantics and reproduce:

```text
top25_enhanced_v6.csv
top25_enhanced_v6.geojson
stable_candidate_priority_list_v6.csv
quality_diagnostics_all_cells_v6.csv
```

#### Priority

Critical.

---

### 4.3 Request-zone outputs

#### Notebook outputs

The notebook can produce:

```text
request_zones_v6.csv
request_zones_v6.geojson
```

These are part of the paid archive workflow.

#### Current app gap

The app does not yet provide full request-zone persistence and parity export equivalent to the notebook.

#### Required parity goal

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

#### Priority

Critical.

---

### 4.4 Paid imagery quote template and comparison outputs

#### Notebook outputs

The notebook can produce:

```text
paid_imagery_quote_template_v6.csv
paid_imagery_quote_comparison_v6.csv
```

#### Current app gap

The app does not yet persist or reproduce these quote workflow files as structured app entities.

#### Required parity goal

Add quote-row persistence and parity exports preserving fields such as:

```text
quote_id
provider
zone_id
candidate_ids_covered
acquisition_date
sensor
resolution_m
cloud_cover_pct
off_nadir_deg
sun_elevation_deg
processing_level
license_terms
price
currency
delivery_time_days
coverage_score
metadata_complete
notes
```

#### Priority

High.

---

## 5. Notebook raster and tensor parity gaps

These are not “bad outputs.” They are notebook output families that should be tracked for parity.

---

### 5.1 DEM / terrain output family

#### Notebook outputs

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

#### Current app status

The app covers some DEM/terrain outputs under different names, but does not necessarily reproduce every notebook filename and folder path.

#### Required parity goal

Produce notebook-compatible DEM output names and folder structure in parity mode, even if the core app also writes cleaner internal names.

#### Priority

Medium-high.

---

### 5.2 SAR / radar output family

#### Notebook outputs

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

#### Current app status

The app has SAR RTC outputs and notebook-compatible SAR aliases for some outputs. Separate ascending/descending support stacks are still a parity gap unless deliberately deferred.

#### Required parity goal

Reproduce the full notebook SAR output family in parity mode, including ASC/DESC support outputs if technically feasible.

#### Priority

High.

---

### 5.3 Pre-RTC SAR intermediate arrays

#### Notebook outputs

```text
QA/sar/intermediates/per_image_products_db/*
QA/sar/intermediates/pair_median/*
QA/sar/intermediates/final_median_pre_rtc/*
QA/sar/intermediates/post_sample_pre_rtc/*
QA/sar/intermediates/post_rtc/*
QA/sar/intermediates/sar_intermediate_manifest.json
```

#### Current app status

The app may preserve final post-RTC equivalents, but pre-RTC intermediates are not fully reproduced.

#### Required parity goal

For notebook parity mode, either:

1. write the missing intermediate arrays; or
2. write a manifest explaining why a source-equivalent intermediate cannot be recovered.

For faithful conversion, option 1 is preferred where technically possible.

#### Priority

Medium-high.

---

### 5.4 Optical / panchromatic output family

#### Notebook outputs

```text
PAN_LS_Panchromatic_640.tif
PAN_S2_Panchromatic_10m_640.tif
PAN_LS_Panchromatic_640.npy
PAN_S2_Panchromatic_10m_640.npy
PAN_LAYERS_STACK_640.npy
```

#### Current app gap

These are notebook-only or not fully reproduced in the current app output tree.

#### Required parity goal

Add parity-mode generation for panchromatic support outputs if they are required to match the notebook reference output.

#### Priority

Medium.

---

### 5.5 Hypercube / stacked tensor output family

#### Notebook outputs

```text
FINAL_TESLA_V7_2_HYPERCUBE.tif
FINAL_TESLA_V7_2_HYPERCUBE.npy
FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
RADAR_STACK_HWC_640_*.npy
S1_FILTERED_LAYERS_STACK_640.npy
```

#### Current app status

Some hypercube outputs are implemented or aliased, but the full notebook stack family and resampled variants are not necessarily complete.

#### Required parity goal

Preserve notebook names and stack shapes in parity mode. Add a stack manifest containing:

- source layer list;
- band order;
- shape;
- dtype;
- nodata policy;
- source file mapping;
- any intentional difference.

#### Priority

High.

---

## 6. Notebook report / semantic raster parity gaps

These outputs should be preserved for parity if the goal is notebook conversion fidelity.

They should not be silently renamed away unless parity aliases are also written.

### 6.1 Report rasters

#### Notebook outputs

```text
REPORT_640_Pottery_Report.tif
REPORT_640_Mass_Report.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
```

#### Current app status

The app has code related to `REPORT_640_*` outputs, but parity should verify:

- exact filename;
- exact folder;
- exact band values or accepted tolerance;
- source formula;
- shape;
- transform;
- CRS;
- nodata policy.

#### Required parity goal

Treat these as required notebook-parity outputs.

Do not remove names solely because they sound semantic. If a clean app alias is desired, write both:

```text
notebook original name
neutral app alias
```

#### Priority

High.

---

### 6.2 AI_BEH and AI_READY series

#### Notebook outputs

```text
AI_BEH_* series
AI_READY_* series
AI_READY_640_Secret_* series
```

Examples include notebook-style names such as:

```text
AI_READY_640_Secret_Gold_Halo
AI_READY_640_Secret_Silver_Oxide
AI_READY_640_Secret_Tunnel_Ceiling
AI_READY_640_Secret_Thermal_Inertia
AI_READY_640_Secret_Chemical_Protector
AI_READY_640_Secret_Hidden_Doors
```

#### Current app status

Some app code may compute similar internal/parity layers, but the full notebook output family and naming should be verified.

#### Required parity goal

For notebook parity mode, preserve these original notebook output names and folder paths where feasible.

Optional: also write neutral aliases, but do not drop original names if the task is faithful conversion.

#### Priority

High.

---

## 7. Classifier / model output parity gaps

### 7.1 Original classifier labels

#### Notebook outputs / labels

The notebook contains classifier-style labels such as:

```text
Gold_Metal_Jar
Sarcophagus_Naos
Red_Mercury_Trace
Black_Mercury_Trace
Buried_Entrance
Weapons_Shield_Cache
Ancient_Well
```

#### Current app status

The current app experimental module uses neutral `Class_A` through `Class_N` identifiers.

That is good for clean app mode, but it is not full notebook parity if original labels are required.

#### Required parity goal

Notebook parity mode should be able to preserve original classifier output labels when the goal is exact conversion fidelity.

Recommended output strategy:

```text
experimental/classifications_original.csv      # original notebook labels
experimental/classifications_neutral.csv       # neutral aliases
experimental/class_mapping.json                # explicit mapping
experimental/summary.json
```

This keeps conversion fidelity and clean-mode compatibility.

#### Priority

Medium-high.

---

### 7.2 Deep learning model build/inference cells

#### Notebook behavior

The notebook contains Swin, UnetPlusPlus, ResNet50, SegFormer, YOLO-style, and CNN inference/build attempts.

#### Current app gap

The current app does not fully reproduce these model-build/inference cells.

#### Required parity goal

Track these cells separately because feasibility depends on:

- package availability;
- GPU/CPU runtime;
- model weights;
- training data;
- whether the notebook cell was actually runnable;
- whether source files exist.

For faithful conversion, preserve runnable behavior where possible and mark non-runnable cells as:

```text
not_implemented_missing_weights
not_implemented_missing_training_data
not_implemented_broken_notebook_cell
not_implemented_dependency_unavailable
```

#### Priority

Medium.

---

## 8. Coordinate-bearing output parity

### 8.1 KMZ / GeoJSON / CSV / map outputs

#### Notebook outputs

The notebook can emit exact-location artifacts such as:

```text
GeoJSON
KMZ
KML
CSV with lat/lon
Google Earth overlays
visual_inspection_map.html
field/navigation-style outputs
```

#### Correct framing

These are not automatically “bad” in this project context.

For faithful notebook conversion, they are parity outputs.

#### Required parity goal

Preserve them in notebook parity/private output mode when the goal is to match the notebook.

Recommended output strategy:

```text
parity/location/*.geojson
parity/kmz/*.kmz
parity/maps/visual_inspection_map.html
parity/navigation/*.kml
parity/navigation/*.csv
```

Add a manifest that states:

```text
These are notebook-parity outputs preserved for conversion fidelity.
They are not generated by the clean public/shared mode unless explicitly enabled.
```

#### Priority

High for parity, separate from public UI decisions.

---

## 9. QA / diagnostics / provenance parity gaps

### 9.1 Notebook QA files

#### Notebook outputs

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

#### Current app status

The app has its own manifests, run history, stage manifests, and QA files, but it does not necessarily reproduce every notebook QA filename.

#### Required parity goal

Write notebook-compatible QA outputs in parity mode, even if the app also keeps its own cleaner manifests.

Required approach:

```text
app-native QA files remain
notebook-compatible QA aliases are also written
parity manifest maps native files to notebook files
```

#### Priority

High.

---

## 10. Colab / Drive behavior

### 10.1 What to preserve

The notebook has Colab/Drive mechanics:

```text
Drive mount
Drive export waits
Drive refresh hacks
Colab shell listing
Colab JS auto-scroll / auto-run
pip install cells
```

### 10.2 Correct conversion target

The app does not need to reproduce Colab UI mechanics exactly.

But it should reproduce the resulting output files and pipeline effects where those effects matter.

So the target is:

```text
output-equivalent behavior, not Colab-mechanic-equivalent behavior
```

Examples:

- Do not need Drive mount if server storage writes the same files.
- Do not need Drive refresh if app output tree is complete.
- Do not need pip install cells if requirements are pinned.
- Do not need JS auto-scroll if app orchestration runs stages directly.

### 10.3 Status

Not a direct parity output gap unless a Colab-only step produces a file that is missing from the app.

---

## 11. Known notebook bugs and parity policy

### 11.1 `IRON_SWIR` formula

Notebook note identified this bug:

```text
IRON_SWIR = (B11 - B12) / (B11 - B12)
```

This collapses to 1 wherever the denominator is nonzero.

The app currently uses the corrected form:

```text
(B11 - B12) / (B11 + B12)
```

#### Parity policy

For faithful conversion, document this as a corrected notebook bug.

If strict bug-for-bug parity is ever needed, support it only behind an explicit compatibility flag such as:

```text
--compatibility reproduce-known-notebook-bugs
```

Default should remain corrected behavior.

---

### 11.2 Broken constructor typo

Notebook cell 233 uses:

```python
def init(self)
```

instead of:

```python
def __init__(self)
```

#### Parity policy

Do not reproduce broken code unless preserving it as a non-runnable source reference.

Mark as:

```text
not_implemented_broken_notebook_cell
```

---

## 12. Current app strengths to preserve while adding parity

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

Important:

Adding notebook parity mode must not break the current core app pipeline.

The clean app mode and notebook parity mode should coexist.

---

## 13. Recommended implementation phases

### Phase 1 — Output inventory lock

Create an authoritative notebook-output inventory from `Notebook cells.md` and/or a frozen notebook output bundle.

Deliverables:

```text
docs/NOTEBOOK_OUTPUT_INVENTORY_LOCKED.md
parity_expected_outputs.json
```

### Phase 2 — Parity output tree design

Define where notebook-parity outputs live in the app run directory.

Suggested structure:

```text
data/runs/<run_id>/
  app_native/
  parity/
    root/
    DEM_GEO8_TIFS/
    GEOTIFF_RADAR_BANDS/
    NPY_RADAR_BANDS/
    NPY_STACKS/
    OPT/
    QA/
    kmz/
    maps/
    experimental/
  manifests/
```

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

Compare:

- file presence;
- row counts;
- required columns;
- raster shapes;
- CRS/transform;
- nodata;
- band order;
- checksums where deterministic;
- numeric tolerance where Earth Engine variability exists.

---

## 14. Final rule

The objective is faithful notebook-to-Python-app conversion.

Do not delete notebook outputs from the plan just because they are experimental, oddly named, duplicate, or not part of the clean UI.

Instead:

```text
preserve them in notebook parity/private mode;
map them clearly;
validate them;
then decide separately what, if anything, belongs in clean core app mode or public/shared mode.
```
