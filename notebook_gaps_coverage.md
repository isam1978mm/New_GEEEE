# Notebook Gaps Coverage Plan

**Project:** GEE Screening  
**Goal:** Cover the gaps between the original notebook and the Python app by planning a faithful notebook-parity path before implementation.

---

## 1. Purpose

This document defines the phases and goals required to cover notebook-to-app gaps.

Current phase tracking lives in:

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/PHASE_4_COVERAGE_CHECKLIST.md`
- `docs/PHASE_4_FINAL_COVERAGE_SUMMARY.md`
- `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md`

The objective is **faithful notebook-to-Python-app conversion**.

The app should not drop notebook outputs simply because they are experimental, oddly named, duplicate, Colab-specific, coordinate-bearing, or not part of the clean public UI.

Instead, notebook behavior should be separated into execution/output modes:

1. core app mode;
2. notebook parity mode;
3. experimental/private mode;
4. public/shared mode.

Notebook-parity mode should preserve original notebook output families, names, folders, and artifacts where technically feasible.

Classifier/model outputs must use probability-only wording. They may express class probabilities, probability bands, or model scores, but not confirmation language.

---

## 2. Mode model

### 2.1 Core app mode

Purpose:

- stable backend workflow;
- clean app-native pipeline;
- run status lifecycle;
- artifact tracking;
- controlled API/frontend behavior;
- app-native output names.

Core app mode should remain stable while parity work is added.

### 2.2 Notebook parity mode

Purpose:

- reproduce notebook output families;
- preserve original notebook filenames;
- preserve original notebook folder conventions;
- write notebook-compatible aliases for app-native outputs;
- create an auditable output tree for comparison against a frozen notebook reference.

This mode may include original notebook names such as:

```text
AI_BEH_*
AI_READY_*
REPORT_640_*
FINAL_TESLA_V7_2_*
RADAR_*_640_*
```

### 2.3 Experimental/private mode

Purpose:

- preserve classifier/model-derived notebook behavior;
- support original notebook classifier labels if needed for conversion fidelity;
- optionally write neutral aliases beside original labels;
- keep experimental outputs separate from core app outputs;
- support probability-only ML/classifier outputs.

Recommended classifier output strategy:

```text
experimental/classifications_original.csv
experimental/classifications_neutral.csv
experimental/class_mapping.json
experimental/summary.json
experimental/probability_scores.csv
experimental/model_card.json
experimental/calibration_report.json
```

### 2.4 Public/shared mode

Purpose:

- future controlled sharing;
- redacted summaries;
- no accidental exposure of internal/private/parity artifacts.

Public/shared mode is separate from notebook parity mode. A parity artifact may exist privately without becoming a public UI feature.

---

## 3. Probability-only classifier language rule

Future classifier/model outputs must use probability-only language.

Allowed wording:

```text
probability
class probability
model-estimated probability
likelihood score
probability band
candidate resembles training examples
heuristic score
uncalibrated model probability
calibrated model probability
```

Forbidden output wording:

```text
confirmed
found
proven
dig target
definitely
```

Allowed output examples:

```text
object_id: 17
top_class: tomb_like
class_probability: 0.36
probability_band: 30-40%
model_version: tomb_classifier_v0.1
training_dataset_version: training_set_v0.1
calibration_status: uncalibrated
```

Explicit class names are allowed when framed as probabilities:

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

Probability quality levels must be explicit:

```text
heuristic_score                  # no labeled/calibrated dataset
uncalibrated_model_probability   # trained model, not calibrated
calibrated_model_probability     # validation/calibration evidence exists
```

A value must not be called a calibrated probability unless calibration evidence exists.

---

## 4. Coverage principle

Do not ask Codex to “convert the notebook” in one task.

Work must proceed in locked phases.

Each phase must have:

- narrow scope;
- allowed files;
- explicit non-goals;
- validation commands;
- exact changed-file expectations;
- final report requirements;
- GitHub validation before deploy or next phase.

---

## 5. Phase 0 — Output inventory lock

### Goal

Create the authoritative list of notebook outputs the app must track for faithful parity.

### Questions answered

```text
What exactly does the notebook output?
Which files already exist in the app?
Which files are renamed equivalents?
Which files are partial?
Which files are missing?
Which files require private/parity mode?
Which files require external dependencies?
Which files come from broken or non-runnable notebook cells?
Which stage files exist but still need runtime/parity verification?
Which classifier/model outputs should become probability-only outputs later?
```

### Deliverables

```text
docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md
docs/parity_expected_outputs.json
```

### Scope

Docs/data only.

No runtime implementation.

### Required output families

The inventory must cover:

- v6 candidate package outputs;
- candidate/ranking CSV and GeoJSON outputs;
- request-zone outputs;
- quote-template and quote-comparison outputs;
- DEM/terrain outputs;
- SAR/radar outputs;
- pre-RTC SAR intermediates;
- panchromatic/optical outputs;
- hypercube/tensor outputs;
- `REPORT_640_*` outputs;
- `AI_BEH_*` outputs;
- `AI_READY_*` outputs;
- classifier/model outputs;
- future probability-only classifier outputs;
- coordinate/map/KMZ/GeoJSON outputs;
- QA/provenance outputs.

### Critical Phase 0 verification rule

File existence is not enough.

Before Codex marks any app output as `implemented`, Codex must open the relevant stage/source file and confirm the code path that writes it.

For every stage file reviewed, Codex must record or summarize:

- stage class name;
- `stage.name`;
- artifact names written;
- relative paths written;
- artifact class;
- `http_servable` setting;
- formulas or source inputs if visible;
- output category:
  - app-native;
  - notebook-compatible alias;
  - notebook-parity semantic/report raster;
  - QA/provenance;
  - coordinate-bearing;
  - experimental/private;
  - probability-classifier output;
- whether runtime output presence is proven;
- whether notebook-value parity is proven.

If code exists but runtime output presence or notebook-value parity is not proven, Codex must use:

```text
unknown_needs_verification
```

or `partial`, not `implemented`.

### `secret_layers.py` and `report_640.py` classification rule

Codex must not classify these as clean defensible core by default:

```text
app/pipeline/stages/secret_layers.py
app/pipeline/stages/report_640.py
```

Correct classification:

```text
secret_layers.py  -> notebook-parity semantic raster stage
report_640.py     -> notebook-parity report/semantic raster stage
```

They may be preserved for faithful notebook parity, but Phase 0 must not treat them as neutral core science unless clearly qualified.

The inventory should mark their runtime and value parity as unproven unless a real run/reference comparison proves otherwise.

### JSON schema expectation

Each JSON item should include:

```text
id
family
notebook_paths_or_patterns
app_current_equivalent_paths_or_patterns
status
target_mode
target_phase
parity_priority
requires_coordinates
requires_external_dependency
notes
```

Recommended optional fields:

```text
stage_file
stage_class
stage_name
artifact_names
relative_paths
artifact_class
http_servable
classification
runtime_output_verified
notebook_value_parity_verified
probability_only_required
calibration_required
verification_notes
```

Allowed statuses:

```text
implemented
renamed_equivalent
partial
missing
notebook_only_pending
requires_external_dependency
broken_notebook_cell
unknown_needs_verification
```

Allowed target modes:

```text
core_app
notebook_parity
experimental_private
public_shared
not_applicable
```

### Success gate

- Only the two Phase 0 docs/data files changed.
- JSON parses with Python `json` module.
- Markdown states faithful notebook conversion is the objective.
- Markdown does not say notebook outputs should be removed because they are risky.
- Markdown states original notebook names are preserved for parity where feasible.
- Markdown states file existence is not parity proof.
- Markdown states `secret_layers.py` and `report_640.py` are notebook-parity semantic/report raster stages, not clean defensible core by default.
- Markdown states ML/classifier outputs must use probability-only wording.
- Unknown or unverified outputs are listed honestly.

### Codex task status

Planned.

---

## 6. Phase 1 — Parity mode architecture

### Goal

Define and implement the app structure for notebook-parity outputs without disrupting core app behavior.

### Target output layout

Recommended structure:

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
    navigation/
    experimental/
  manifests/
```

### Deliverables

Potential deliverables:

```text
docs/PARITY_MODE_CONTRACT.md
app/pipeline/parity/
tests/parity/
```

### Non-goals

- No raster math changes.
- No candidate import yet.
- No request-zone persistence yet.
- No UI changes unless explicitly approved later.

### Success gate

- Parity manifest format exists.
- Parity output helpers are tested.
- Core app pipeline still works.
- Existing artifact serving policy is not weakened.

---

## 7. Phase 2 — v6 package import/export parity

### Goal

Cover the most important business/review outputs from the notebook.

### Outputs to cover

```text
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

### Deliverables

Potential deliverables:

```text
gee-import-v6 command or module
schema validators
candidate import records
request-zone import records
quote-row import records
package manifest
package hash manifest
```

### Success gate

- App can import a v6 package.
- Required files are validated.
- CSV/GeoJSON schemas are validated.
- Original filenames are preserved.
- Package can be exported or rebuilt.
- No claim interpretation is added.

---

## 8. Phase 3 — Raster and tensor parity aliases

### Goal

For outputs already computed by the app, write notebook-compatible aliases and folders.

### Examples

```text
dem.tif -> DEM_GEO8_TIFS/DEM_640.tif
VV_dB.tif -> GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_*.tif
VH_dB.tif -> GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_*.tif
logRatio_dB.tif -> GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_*.tif
incidence.tif -> GEOTIFF_RADAR_BANDS/RADAR_angle_640_*.tif
hypercube.tif -> NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif
hypercube.npy -> NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
```

### Success gate

- No source math changes.
- Alias outputs match source outputs.
- Manifest maps each alias to its app-native source.
- Tests verify file presence, shape, dtype, CRS/transform where applicable.

---

## 9. Phase 4 — Missing notebook raster families

### Goal

Add notebook output families that are not currently produced or not fully reproduced.

### Buckets

```text
DEM hillshade
missing curvature variants
separate ASC/DESC Sentinel-1 support stacks
PAN_LS panchromatic outputs
PAN_S2 panchromatic outputs
PAN_LAYERS_STACK_640.npy
S1_FILTERED_LAYERS_STACK_640.npy
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.*
AI_BEH_* series
AI_READY_* series
REPORT_640_* rasters
```

### Success gate

Each output is either produced or explicitly marked with a reason:

```text
implemented
not_implemented_missing_source
not_implemented_missing_dependency
not_implemented_notebook_cell_broken
not_implemented_needs_reference_output
```

No silent omissions.

---

## 10. Phase 5 — QA and intermediate parity

### Goal

Reproduce notebook QA/provenance outputs.

### Outputs

```text
QA_GRID_dx_m_640.tif
QA_GRID_dy_m_640.tif
QA_GRID_validmask_640.tif
RUN_MANIFEST.json
QA_RADAR_CELL25_PAIR_IDS_*.json
QA_S1_MASTER_UNITS.json
QA_RADAR_META_*.json
SUMMARY_RADAR_*.csv
QA/sar/intermediates/per_image_products_db/*
QA/sar/intermediates/pair_median/*
QA/sar/intermediates/final_median_pre_rtc/*
QA/sar/intermediates/post_sample_pre_rtc/*
QA/sar/intermediates/post_rtc/*
sar_intermediate_manifest.json
```

### Success gate

- App-native QA remains.
- Notebook-compatible QA is also written.
- SAR pair provenance is preserved.
- Missing intermediates are either produced or honestly explained.

---

## 11. Phase 6 — Coordinate/map/private parity outputs

### Goal

Preserve notebook location/map outputs in private parity mode.

### Outputs

```text
GeoJSON
KMZ
KML
CSV with lat/lon
visual_inspection_map.html
Google Earth overlays
navigation-style files
```

### Correct framing

These are notebook-parity outputs, not automatically public app features.

### Suggested output paths

```text
parity/location/*.geojson
parity/kmz/*.kmz
parity/maps/visual_inspection_map.html
parity/navigation/*.kml
parity/navigation/*.csv
```

### Success gate

- Files exist in the parity/private tree.
- Manifest marks them as coordinate-bearing parity artifacts.
- They are not accidentally mixed into clean core app outputs.
- Public/shared behavior remains a separate later decision.

---

## 12. Phase 7 — Classifier/model parity

### Goal

Preserve notebook classifier/model outputs as conversion artifacts while enforcing probability-only wording for any interpreted model outputs.

### Original-label examples

```text
Gold_Metal_Jar
Sarcophagus_Naos
Red_Mercury_Trace
Black_Mercury_Trace
Buried_Entrance
Weapons_Shield_Cache
Ancient_Well
```

### Recommended output strategy

```text
experimental/classifications_original.csv
experimental/classifications_neutral.csv
experimental/class_mapping.json
experimental/summary.json
experimental/probability_scores.csv
```

### Deep learning/model cells to track

```text
Swin
UnetPlusPlus
ResNet50
SegFormer
YOLO-style / CNN cells
archeo_dictionary model cells
```

### Success gate

- Runnable classifier outputs are reproduced.
- Original labels are preserved for parity when required.
- Neutral labels remain available for clean app mode.
- Any model interpretation is expressed as probability or score only.
- Missing weights/dependencies/data are documented, not hidden.

---

## 13. Phase 8 — Probability-only ML classifier design

### Goal

Design the future candidate classifier that outputs class probabilities and probability bands, not confirmation wording.

### Required output fields

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

### Required probability levels

```text
heuristic_score
uncalibrated_model_probability
calibrated_model_probability
```

### Required design docs

Potential deliverables:

```text
docs/PROBABILITY_CLASSIFIER_CONTRACT.md
docs/ML_DATASET_REQUIREMENTS.md
docs/CLASSIFIER_CALIBRATION_PLAN.md
```

### Required validation concepts

```text
positive examples
negative examples
train/validation split
confusion matrix
calibration report
model card
dataset version
```

### Success gate

- The classifier contract forbids confirmation wording.
- It distinguishes heuristic scores from calibrated probabilities.
- It defines dataset and calibration requirements.
- It does not require immediate model training.

---

## 14. Phase 9 — End-to-end parity harness

### Goal

Compare the app output tree against a frozen notebook output tree.

### Proposed command

```bash
python -m app.tools.parity_compare \
  --notebook-reference <path> \
  --app-run <run_id>
```

### Checks

```text
file presence
folder structure
required columns
row counts
CSV schema
GeoJSON validity
raster shape
CRS
transform
nodata
band order
dtype
numeric tolerance
manifest completeness
accepted differences
```

### Success gate

- Produces a parity report.
- Separates hard failures from accepted differences.
- No manual guessing.
- Can be run repeatedly against frozen notebook reference output.

---

## 15. Phase 10 — Clean app vs parity app decision

### Goal

After parity exists, decide what belongs in normal app UI/API.

Do not decide this before parity work is complete.

Each output can later be classified as:

```text
core app visible
operator-only
parity/private only
experimental only
probability-classifier output
not exposed
```

### Success gate

- Decisions are based on complete parity inventory and working outputs.
- No notebook output is dropped without explicit decision.
- Any classifier result that is exposed uses probability-only wording.

---

## 16. Immediate next Codex task

The next Codex task should be Phase 0 only.

No implementation.

No runtime code.

No UI changes.

No database changes.

No pipeline changes.

### Codex MASTER TASK — Phase 0

```text
PROJECT: GEE_screening
BRANCH: main
SCOPE: Phase 0 only — notebook parity output inventory lock.

Goal:
Create an authoritative documentation/data inventory of notebook outputs that the Python app must track for faithful notebook parity.

Do not implement pipeline code.
Do not change app behavior.
Do not modify API, frontend, database models, tests, or runtime code.
Do not rename existing app outputs.
Do not remove or sanitize notebook output names.
Do not treat original notebook labels as product claims; record them as parity output names.
For classifier/model outputs, record the future requirement that interpreted outputs must use probability-only wording.

Inputs to review:
- gaps.md
- notebook_gaps_coverage.md
- docs/NOTEBOOK_VS_APP_OUTPUTS.md
- Notebook cells.md if present in repo
- docs/CLASS_MAPPING.md
- docs/EXPERIMENTAL_MODULE.md
- app/pipeline/stages/*
- app/pipeline/stages_experimental/*

Important correction:
File existence is not enough. Do not mark an output as implemented unless the code path writing it is identified from source-file inspection. If runtime output presence or notebook-value parity is not proven, use `unknown_needs_verification` or `partial`.

For every stage file reviewed, record or summarize:
- stage class name
- stage.name
- artifact names written
- relative paths written
- artifact_class
- http_servable setting
- output formulas or source inputs if visible
- whether the output is app-native, notebook-compatible alias, notebook-parity semantic/report raster, QA/provenance, coordinate-bearing, experimental/private, or probability-classifier output
- whether runtime output presence is proven
- whether notebook-value parity is proven

Special classification rule:
Do not classify `app/pipeline/stages/secret_layers.py` or `app/pipeline/stages/report_640.py` as clean defensible core by default.
Classify them as:
- `secret_layers.py`: notebook-parity semantic raster stage
- `report_640.py`: notebook-parity report/semantic raster stage

Create:
1. docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md
2. docs/parity_expected_outputs.json

The markdown document must include:
- purpose and scope
- mode separation:
  - core app mode
  - notebook parity mode
  - experimental/private mode
  - public/shared mode
- all notebook output families:
  - v6 candidate package outputs
  - candidate/ranking CSV + GeoJSON outputs
  - request-zone outputs
  - quote-template/comparison outputs
  - DEM/terrain outputs
  - SAR/radar outputs
  - pre-RTC SAR intermediates
  - panchromatic/optical outputs
  - hypercube/tensor outputs
  - REPORT_640 outputs
  - AI_BEH / AI_READY outputs
  - classifier/model outputs
  - future probability-only classifier outputs
  - coordinate/map/KMZ/GeoJSON outputs
  - QA/provenance outputs
- for each family:
  - notebook output names
  - current app status
  - target mode
  - target phase
  - parity requirement
  - known blocker if any
  - accepted difference if any
  - verification status

The JSON file must be machine-readable and include an array of expected outputs or output families.
Each item must include:
- id
- family
- notebook_paths_or_patterns
- app_current_equivalent_paths_or_patterns
- status
- target_mode
- target_phase
- parity_priority
- requires_coordinates
- requires_external_dependency
- notes

Optional but recommended JSON fields:
- stage_file
- stage_class
- stage_name
- artifact_names
- relative_paths
- artifact_class
- http_servable
- classification
- runtime_output_verified
- notebook_value_parity_verified
- probability_only_required
- calibration_required
- verification_notes

Allowed statuses:
- implemented
- renamed_equivalent
- partial
- missing
- notebook_only_pending
- requires_external_dependency
- broken_notebook_cell
- unknown_needs_verification

Allowed target modes:
- core_app
- notebook_parity
- experimental_private
- public_shared
- not_applicable

Allowed phases:
- phase_1_parity_mode_architecture
- phase_2_v6_package
- phase_3_raster_tensor_aliases
- phase_4_missing_raster_families
- phase_5_qa_intermediates
- phase_6_coordinate_map_private_parity
- phase_7_classifier_model_parity
- phase_8_probability_classifier_design
- phase_9_e2e_parity_harness
- later_decision

Validation required before final report:
- git diff --name-only must show only:
  - docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md
  - docs/parity_expected_outputs.json
- JSON must parse with python json module.
- Markdown must mention that faithful notebook conversion is the objective.
- Markdown must not say risky outputs should be removed.
- Markdown must state original notebook names are preserved for parity where feasible.
- Markdown must state file existence is not parity proof.
- Markdown must state `secret_layers.py` and `report_640.py` are notebook-parity semantic/report raster stages, not clean defensible core by default.
- Markdown must state classifier/model interpreted outputs must use probability-only wording.
- Commit changes to main with message:
  "Lock notebook parity output inventory"

Final report must include:
- commit hash
- changed files
- confirmation no runtime code changed
- JSON item count
- any outputs marked unknown_needs_verification
- any outputs marked partial
- list of stage files inspected
```

---

## 17. Validation plan after Codex returns

After Codex returns, validate with GitHub before approving Phase 1.

Checks:

```text
main HEAD commit
exact changed files
commit diff
JSON parses
no runtime files changed
no API/frontend/database/pipeline implementation hidden in docs task
all required output families included
unknown_needs_verification items listed honestly
partial items listed honestly
stage files inspected are named
secret_layers.py and report_640.py are not classified as clean defensible core
classifier/model outputs are tracked with probability-only wording requirement
```

Approve Phase 1 only after Phase 0 passes validation.

---

## 18. Final rule

The goal is faithful notebook-to-Python-app conversion first.

Do not remove notebook outputs from the plan just because they are experimental, duplicate, coordinate-bearing, or not part of the clean UI.

Preserve them in notebook parity/private mode, validate them, express future classifier/model interpretations as probabilities or scores, then decide later what belongs in core app mode or public/shared mode.
