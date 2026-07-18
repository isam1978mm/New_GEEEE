# Depth App Architecture Specification

Status: Phase 6 design artifact only. No depth stage, model, API field, frontend field, or numerical result is implemented by this document.

## Plain-English purpose

This document explains where a future depth-estimation step would fit inside the private local app.

The safe order is:

```text
existing sensor and feature stages
→ candidate extraction
→ classifier
→ alignment checks
→ run-quality checks
→ future depth estimation
```

Depth must come last because it depends on completed candidate and quality information. It must not change the classifier or weaken an existing successful run.

The future stage may examine a candidate only when the run is usable and a validated local depth package exists. Otherwise it must return `depth_status = not_available` or `depth_status = insufficient_data`.

## Current repository architecture

The current core pipeline ends with:

```text
pca_anomaly
object_extract
classifier
alignment_qa
run_quality
```

The future depth stage should be placed after `run_quality`:

```text
run_quality
depth_estimation
```

Reason:

- the classifier has already identified candidate records;
- alignment has already been checked;
- run quality has already decided whether the upstream data is usable;
- depth cannot influence the existing classifier result;
- weak or unsupported runs can be refused before a depth result is attempted.

## Current gate

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
numerical_depth_model_status = not_fitted
confounder_testing_status = not_run
phase_6_design_status = defined
phase_6_implementation_status = blocked
app_depth_output = not_available
```

Implementation remains blocked until the required calibration and validation phases pass.

## Proposed files

Only after the earlier gates pass, the first implementation slice should use:

```text
app/pipeline/stages/depth_estimation.py
tests/unit/test_depth_estimation.py
tests/integration/test_depth_estimation_outputs.py
docs/DEPTH_METHOD_CARD.md
```

Possible supporting modules may be added only when needed:

```text
app/pipeline/depth/package.py
app/pipeline/depth/features.py
app/pipeline/depth/support.py
app/pipeline/depth/schema.py
```

The implementation should remain small and separated. It must not become one large depth engine.

## Stage identity

Proposed stage name:

```text
depth_estimation
```

Because the current stage framework requires a parity category, the future stage should use:

```text
PARITY_REPLACES
```

Suggested reason:

> Replaces unsupported depth-named notebook proxies with a separately calibrated and validated local depth method.

This does not claim that the notebook already measured depth in metres.

## Stage placement

The future orchestrator order should end with:

```text
ObjectExtractStage
ClassifierStage
AlignmentQaStage
RunQualityStage
DepthEstimationStage
```

The public-safe stage-progress list must not be changed until implementation is approved.

Historical runs that do not contain a depth stage or depth directory must remain valid and readable.

## Input contract

The future depth stage may read only approved, versioned inputs.

### Required run-control inputs

```text
grid manifest
alignment QA summary
run-quality summary
classifier summary
candidate identifiers
object or candidate location window
approved feature manifest
local depth-method package
```

### Approved scientific inputs

Only features approved by `docs/DEPTH_FEATURE_INVENTORY.md` and frozen in the validated model package may be used.

Candidate families may include:

```text
raw Sentinel-1 VV_dB and VH_dB summaries
incidence-angle and orbit-geometry controls
small nonduplicative SAR ratios or differences
approved Sentinel-2 surface/context features
canonical Landsat LST and approved thermal context
DEM and terrain controls
valid-pixel and alignment metrics
observation count and temporal-quality metadata
independently documented physical metadata when available
```

### Candidate-routing rule

Classifier and object-extraction outputs may be used to identify:

```text
candidate_id
object_id
cluster_id
candidate sampling window
```

They must not become depth evidence merely because they selected the candidate.

In particular, the following cannot be depth-model features:

```text
classifier class
classifier score
classifier probability
classifier final finding summary
PCA anomaly score used as a target decision
target-mask area or shape derived from the same decision pipeline
generated depth label
```

A classifier family may be used only as an explicit support gate, such as checking whether a finding family is supported. It must not silently drive the predicted depth unless later calibration independently approves it as a model input.

## Run-quality gate

The stage must read:

```text
QA/run_quality/run_quality_summary.json
```

Required behavior:

- `status=PASS` may continue;
- `status=WARNING` may continue only when the validated depth method permits the recorded warning conditions;
- `status=BLOCKED` must return no depth result;
- `status=UNKNOWN` must return no depth result;
- `is_usable=false` must return no depth result.

A blocked or unknown run should produce:

```text
depth_status = insufficient_data
```

and a short reason copied into the depth warnings.

## Local model-package contract

The validated depth package must remain outside Git under an owner-controlled local path.

A future package should contain at least:

```text
depth_method_manifest.json
calibration_manifest.json
feature_manifest.json
preprocessing_manifest.json
support_rules.json
model artifact or rule definition
checksums.sha256
```

Every package load must verify:

```text
method version
calibration dataset version
feature manifest version
schema version
content hashes
supported finding families
supported depth range
supported sensor and confounder ranges
required feature names and order
```

The run must not download weights or models automatically.

The app must never substitute a notebook proxy when this package is missing or invalid.

## Configuration behavior

A future implementation should have an explicit local mode:

```text
off
relative_only
numerical_range
```

Default behavior remains:

```text
off
```

Rules:

- `off`: write no depth estimate and preserve normal pipeline behavior;
- `relative_only`: permitted only after Phase 3 passes;
- `numerical_range`: permitted only after Phases 3, 4, and 5 pass;
- an unavailable or invalid package must not silently change the selected mode;
- no mode may convert a raw ratio directly into metres.

The exact setting name should be chosen during implementation and documented in the method card.

## Output files

A future successful stage should write:

```text
depth/depth_estimates.csv
depth/depth_summary.json
depth/depth_method_manifest.json
```

Initial artifact classification:

```text
artifact_class = FILESYSTEM_ONLY
http_servable = false
```

This keeps detailed depth output private and local during validation.

A later Phase 7 decision may approve a selected local operator summary. That approval must not expose raw feature rows, coordinates, private paths, source records, or calibration records.

## Candidate output schema

Each candidate row may eventually contain:

```text
candidate_id
object_id
cluster_id
depth_status
estimated_depth_min_m
estimated_depth_max_m
estimated_depth_best_m
depth_category
depth_quality
depth_method_version
calibration_dataset_version
feature_manifest_version
support_status
support_distance
warnings
```

Rules:

- metre fields are empty unless `depth_status` is `calibrated_range` or `validated_range`;
- `estimated_depth_min_m <= estimated_depth_best_m <= estimated_depth_max_m`;
- no value may be below zero;
- unsupported candidates return `insufficient_data`;
- missing model or disabled mode returns `not_available`;
- no raw coordinates or local paths appear in these outputs;
- warnings use stable machine-readable codes plus a short plain-English reason.

## Summary output schema

`depth_summary.json` may eventually contain:

```text
schema_version
stage
mode
status
candidate_count
estimated_count
relative_only_count
insufficient_data_count
not_available_count
method_version
calibration_dataset_version
feature_manifest_version
run_quality_status
warnings
```

This summary must not claim physical confirmation.

## Status behavior

Allowed candidate depth statuses:

```text
not_available
insufficient_data
relative_only
calibrated_range
validated_range
```

Meaning:

- `not_available`: depth capability is disabled or no approved method package exists;
- `insufficient_data`: depth was considered but required quality or support conditions failed;
- `relative_only`: broad category only, with no metre claim;
- `calibrated_range`: a metre interval from a calibrated method, not yet final holdout-approved;
- `validated_range`: a metre interval from a method that passed the frozen holdout gates.

The normal app must never display `calibrated_range` as if it were `validated_range`.

## Expected failure behavior

Scientific limitations are normal outcomes, not pipeline crashes.

The stage should return a completed result with `not_available` or `insufficient_data` for expected cases such as:

```text
mode disabled
model package absent
unsupported finding family
run-quality block
missing optional sensor family
candidate outside calibration support
low valid-pixel coverage
high uncertainty
no classified candidates
```

Unexpected programming errors, unreadable core run files, or internally inconsistent schemas should remain visible as technical failures during development. They must not be hidden behind a fake depth result.

Implementation must define exactly which package-integrity failures are recoverable and test them before activation.

## Backward compatibility

Required behavior:

1. Old runs with no `depth/` directory remain readable.
2. Existing classifier CSV and JSON schemas remain unchanged.
3. Existing `experimental/` aliases remain unchanged.
4. Existing artifact names and locations remain unchanged.
5. Existing runs remain complete even when depth is absent.
6. The frontend must treat all depth fields as optional.
7. The normal classifier and output downloads must not depend on a depth package.
8. Turning depth mode off must reproduce the pre-depth pipeline behavior.

## Privacy boundary

This is a private local app.

The architecture therefore keeps:

```text
calibration records
known-depth source references
raw depth feature rows
model artifacts
support matrices
candidate coordinates
private source paths
```

in private local storage.

No public-service or public-exposure requirement is introduced by this architecture.

## Planned unit tests

A future implementation must test:

- disabled mode returns `not_available`;
- missing package does not substitute a proxy;
- blocked run quality returns `insufficient_data`;
- unsupported finding family abstains;
- missing required feature abstains or fails according to the frozen contract;
- classifier score is not included in the model feature vector;
- target-derived geometry is not included in the model feature vector;
- feature names and ordering match the package manifest;
- hash mismatch is handled according to the package-integrity contract;
- numerical bounds are ordered and nonnegative;
- unsupported cases contain no metre values;
- legacy runs without depth remain valid.

## Planned integration tests

A future implementation must test:

- depth runs after run quality;
- depth does not change classifier artifacts;
- depth does not change legacy `experimental/` artifacts;
- failed support checks produce private local outputs with no false range;
- detailed depth artifacts are `FILESYSTEM_ONLY` and not HTTP-served;
- stage manifest records method, dataset, and feature versions;
- complete runs with depth disabled match existing expected output behavior;
- old run-detail responses work when no depth output exists.

## Implementation gates

Coding may begin only when all of the following are true:

- [ ] Real independently measured or independently documented known-depth records exist.
- [ ] The calibration dataset passes `DEPTH_CALIBRATION_DATASET_CONTRACT.md`.
- [ ] The Phase 3 relative-depth baseline passes untouched-site validation.
- [ ] The Phase 4 numerical method passes when numerical mode is requested.
- [ ] Phase 5 confounder and support checks pass for approved conditions.
- [ ] A frozen local model package and hashes exist.
- [ ] Supported finding families and depth range are documented.
- [ ] Output wording and status behavior are approved.

Until those gates pass, no depth implementation should be added to the normal pipeline.

## Phase 6 checklist

- [x] Inspect the current final pipeline order.
- [x] Choose the future stage position after `run_quality`.
- [x] Define the stage input boundary.
- [x] Separate candidate routing from depth evidence.
- [x] Define local model-package requirements.
- [x] Define output files and schemas.
- [x] Define failure and abstention behavior.
- [x] Define backward-compatibility requirements.
- [x] Define private-local artifact behavior.
- [x] Define planned unit and integration tests.
- [ ] Populate known-depth calibration records.
- [ ] Validate the relative-depth baseline.
- [ ] Validate a numerical range method.
- [ ] Run confounder and support testing.
- [ ] Build a frozen approved model package.
- [ ] Implement `DepthEstimationStage`.
- [ ] Add and run tests.
- [ ] Approve any local frontend presentation.

## Phase 6 decision

```text
App architecture design: complete
Stage position: after run_quality
Detailed output visibility: private local filesystem only
Depth package: absent
Depth stage implementation: blocked
API integration: not approved
Frontend integration: not approved
App depth output: not available
```
