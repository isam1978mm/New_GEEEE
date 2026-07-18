# Depth Validation Gates Specification

Status: Phase 8 design artifact only. No validation run has been performed, no depth implementation is approved, and no app depth result is enabled by this document.

## Plain-English purpose

This document defines the tests that must pass before the private local app may show any depth result.

There are three different questions:

1. **Does the software behave correctly?**
2. **Does the method work on physical sites that were not used to build it?**
3. **Is the result safe to enable for the supported conditions?**

Passing code tests answers only the first question. It does not prove that depth estimation works.

A depth result may be enabled only when the software tests, scientific tests, support checks, privacy checks, wording checks, and legacy-compatibility checks all pass for the requested output mode.

## Current gate

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
numerical_depth_model_status = not_fitted
confounder_testing_status = not_run
depth_stage_status = not_implemented
phase_8_design_status = defined
phase_8_execution_status = blocked
app_depth_output = not_available
```

No test result may be invented while the calibration dataset and implementation are absent.

## Validation levels

### Level 1 — Contract validation

Checks that the planned inputs, outputs, statuses, versions, and privacy boundaries are internally consistent.

This level may be prepared before a model exists.

Passing Level 1 does **not** approve relative or numerical depth.

### Level 2 — Software validation

Checks that the implemented code follows the frozen contracts and fails safely.

Passing Level 2 proves that the code behaves as designed. It does not prove that the scientific method is useful.

### Level 3 — Scientific validation

Checks performance using independently measured or independently documented known-depth records from physical sites not used for fitting or threshold selection.

This level decides whether relative categories or numerical ranges have evidence beyond simple baselines.

### Level 4 — Release validation

Checks the complete private local workflow, including compatibility, privacy, wording, optional frontend presentation, package integrity, and supported-condition enforcement.

Depth remains disabled until the applicable release level passes.

## Output-mode release matrix

| Requested mode | Minimum evidence required | Allowed result |
|---|---|---|
| `off` | Existing application regression tests | No depth output |
| `relative_only` | Levels 1–4 for Phase 3 relative validation | `relative_only` or refusal statuses |
| `numerical_range` | Levels 1–4 for Phases 3, 4, and 5 | `validated_range` or refusal statuses |

`calibrated_range` is a research status. It is not automatically approved for the normal app.

## Gate A — Dataset and provenance validation

The private calibration dataset must be validated before fitting.

Required checks:

- every active positive record has a traceable `known_depth_top_m`;
- reference units and uncertainty are present;
- every usable record has an independent evidence source;
- no app, notebook, classifier, PCA, target-mask, or generated-depth output is used as calibration truth;
- every record has stable `site_id`, `feature_id`, and `group_id` values;
- active splits do not share a `group_id`;
- repeated dates and related local features remain in one split;
- the final holdout contains physical sites unseen during fitting;
- dataset and feature-manifest hashes match;
- excluded and uncertain records are not silently included;
- private coordinates, source references, and records remain outside Git.

Failure behavior:

```text
training_status = blocked
app_depth_output = not_available
```

## Gate B — Frozen calibration fixtures

Future tests need small frozen fixtures that exercise contracts without exposing private data.

Allowed repository fixtures:

- synthetic schema-valid rows with clearly fake identifiers;
- tiny generated arrays containing no real coordinates;
- redacted expected JSON and CSV structures;
- invalid fixtures for failure testing;
- deterministic rule or model stubs that cannot be mistaken for a real validated model.

Private local fixtures:

- real reference records;
- coordinate-bearing feature rows;
- real site-group split manifests;
- trained model artifacts;
- real holdout predictions;
- evidence-source files.

Repository fixtures must never be presented as scientific validation data.

## Gate C — Unit tests for the future depth stage

Planned file:

```text
tests/unit/test_depth_estimation.py
```

Required unit cases:

1. mode `off` returns or records `not_available` without loading a model;
2. missing local model package does not substitute a proxy;
3. package hash mismatch follows the frozen package-integrity policy;
4. missing required feature returns `insufficient_data` or a defined technical failure;
5. blocked run quality returns `insufficient_data`;
6. unknown run quality returns no depth estimate;
7. unsupported finding family abstains;
8. unsupported soil, terrain, size, season, or radar geometry abstains;
9. out-of-range features abstain;
10. classifier score is absent from the model feature vector;
11. classifier class and probability are absent from the model feature vector;
12. target-derived geometry is absent unless a later independent contract explicitly approves it;
13. generated depth labels are rejected;
14. feature names and order match the frozen feature manifest;
15. preprocessing uses package-defined parameters only;
16. relative-only output contains no metre values;
17. unsupported output contains no metre values;
18. numerical bounds are finite, ordered, and nonnegative;
19. a best estimate is never emitted without its interval;
20. warnings contain stable codes and plain-English text;
21. expected scientific refusal completes without crashing the full pipeline;
22. unreadable or inconsistent core files remain visible as technical failures;
23. model, dataset, feature, schema, and support versions are recorded;
24. no automatic model or weight download occurs.

## Gate D — Integration tests for stage order and artifacts

Planned file:

```text
tests/integration/test_depth_estimation_outputs.py
```

Required integration cases:

- `DepthEstimationStage` runs only after `RunQualityStage`;
- depth does not alter classifier artifacts;
- depth does not alter legacy `experimental/` artifacts;
- depth does not alter GRID alignment or existing raster metadata;
- mode `off` reproduces the pre-depth pipeline behavior;
- expected refusal creates a completed depth summary without a false range;
- private detailed artifacts use `FILESYSTEM_ONLY` and `http_servable=false`;
- the stage manifest records status and frozen versions;
- a run remains complete when there are no classified candidates;
- old runs with no `depth/` directory remain readable;
- existing run-detail responses work without depth fields;
- deleting or cleaning a run handles optional depth files normally;
- an unexpected programming failure remains a visible failed stage rather than a scientific refusal.

## Gate E — Relative-depth scientific validation

Required before `relative_only` may be enabled.

Validation must use physical-site grouping and an untouched holdout.

Required comparisons:

- majority-class baseline;
- stratified-random baseline;
- one-feature threshold baseline;
- accepted interpretable relative-depth model.

Required measurements:

- balanced accuracy;
- macro F1;
- per-class precision and recall;
- shallow-versus-deep confusion;
- one-class-off and two-class-off error rates;
- confusion matrix;
- abstention rate;
- coverage among non-abstained cases;
- metrics by physical site;
- metrics by supported target, soil, terrain, season, moisture, and size groups when counts permit.

Release rule:

The accepted model must beat the frozen simple baselines on unseen physical sites and must not depend on one site or one confounder group.

No metre claim is allowed from this gate.

## Gate F — Numerical depth-range scientific validation

Required before `validated_range` may be enabled.

Required comparisons:

- median-depth baseline;
- accepted relative-class midpoint baseline;
- proposed numerical interval method.

Required measurements:

- median absolute error;
- mean absolute error;
- signed bias;
- root mean squared error as a secondary metric;
- interval coverage;
- median and mean interval width;
- coverage-width trade-off;
- percentage within preregistered metre tolerances;
- performance by physical site and depth band;
- subgroup performance when supported;
- abstention rate and non-abstained coverage.

Required rules:

- acceptance thresholds are fixed before final holdout evaluation;
- interval construction is frozen before final holdout evaluation;
- the holdout is not used to choose rounding precision;
- unsupported cases receive no numerical values;
- narrow intervals with poor coverage fail;
- unusably wide intervals fail or trigger refusal;
- output remains a range, not a single exact number.

## Gate G — Confounder and support validation

Required before either visible relative or numerical depth is approved for supported groups.

Required tests include:

- confounder-only baseline;
- sensor-only versus sensor-plus-controls comparison;
- feature-family ablation;
- leave-one-site-group-out sensitivity;
- matched or balanced cases when available;
- residual checks against size, soil, moisture, season, terrain, incidence angle, resolution, and observation quality;
- support-matrix coverage;
- out-of-support refusal tests;
- coordinate and site-identity leakage checks.

Failure rule:

If soil, site, season, target size, or another confounder explains the performance as well as the depth features, depth output remains blocked for that method or group.

## Gate H — Negative and no-target validation

Confirmed no-target and background examples must be tested separately.

Required checks:

- no artificial depth label is assigned to a confirmed negative;
- no-target cases do not receive a metre range;
- false-positive-like surface and sensor cases are represented;
- no-candidate runs complete normally;
- unsupported or ambiguous negatives return a refusal status rather than a confident category;
- negative-case behavior is reported, not hidden inside overall accuracy.

This gate does not prove target absence. It checks that the depth method does not invent depth for records without a valid positive reference.

## Gate I — Threshold sensitivity and stability

Required checks:

- nearby reasonable category boundaries do not cause uncontrolled changes;
- abstention thresholds are selected on training and validation data only;
- interval and support thresholds are not tuned on holdout data;
- deterministic input produces deterministic output;
- repeated loading of the same frozen package produces identical values and warning codes;
- harmless file-order or row-order changes do not alter matched candidate results;
- reasonable preprocessing sensitivity is documented;
- version changes are explicit and do not silently change historical outputs.

Large unstable shifts block release.

## Gate J — Legacy compatibility and regression

The existing app is the baseline contract.

Required checks:

- old runs without depth remain usable;
- classifier CSV and JSON schemas remain unchanged;
- legacy `experimental/` aliases remain unchanged;
- existing artifact names and paths remain unchanged;
- stage progress remains correct with depth disabled;
- downloads that existed before depth continue to work;
- normal app startup does not require a depth model or heavy model dependency;
- mode `off` passes the existing backend test suite;
- frontend builds and existing static tests pass;
- depth absence never changes a successful legacy run into a failed run.

Any regression keeps depth disabled.

## Gate K — Output schema, artifact, and privacy validation

Required checks:

- every status follows the frozen schema;
- metre fields are empty for `not_available`, `insufficient_data`, and `relative_only`;
- `calibrated_range` and `validated_range` are never confused;
- minimum, best, and maximum values are ordered;
- raw coordinates and local paths are absent from normal depth outputs;
- calibration records and source references are absent from normal outputs;
- detailed depth artifacts are private local files;
- no detailed depth artifact is HTTP-served during the initial validation stage;
- optional summary exposure contains only approved fields;
- artifact hashes and sizes are recorded;
- malformed outputs fail tests rather than being silently accepted.

## Gate L — Easy-English wording and accessibility validation

Required exact-behavior tests:

- `not_available` says depth is unavailable and does not imply no feature exists;
- `insufficient_data` gives one clear reason;
- `relative_only` includes the comparison wording and says metres are unavailable;
- `calibrated_range` is visibly research-only;
- `validated_range` says estimated range and includes quality and uncertainty;
- no physical-confirmation wording appears;
- no unsupported confidence percentage appears;
- classifier score is never displayed as depth confidence;
- loading does not temporarily show zero metres;
- unreadable files are reported as technical failures;
- old runs show a valid unavailable state;
- status is not communicated by colour alone;
- quality and warnings have visible text;
- the normal explanation avoids unexplained technical abbreviations.

## Gate M — Full private-local acceptance run

Before enabling a mode, perform one frozen full-run acceptance using:

```text
application commit
calibration dataset version
feature manifest version
model or rule version
support-policy version
wording version
frontend build version, when applicable
```

The acceptance record must include:

- commands or procedure used;
- test-suite results;
- dataset and package hashes;
- scientific metrics;
- subgroup and support results;
- abstention results;
- known limitations;
- approved mode;
- approved finding families;
- approved depth range;
- approved conditions;
- rejected or unsupported conditions;
- owner approval record for activation.

Private records and coordinates remain outside Git. A redacted aggregate acceptance report may be committed later.

## Required future test files

Likely additions after implementation approval:

```text
tests/unit/test_depth_estimation.py
tests/unit/test_depth_package.py
tests/unit/test_depth_output_schema.py
tests/integration/test_depth_estimation_outputs.py
tests/integration/test_depth_legacy_compatibility.py
tests/scientific/test_relative_depth_holdout.py
tests/scientific/test_numerical_depth_holdout.py
tests/scientific/test_depth_confounders.py
tests/scientific/test_depth_stability.py
frontend-v2/src/app/components/DepthResultsPanel.test.tsx
frontend-v2/src/app/api/depthResults.test.ts
```

Exact file organization may be adjusted during implementation, but the test responsibilities must not be dropped.

## Test evidence and storage

Repository-safe test evidence may include:

- pass/fail summaries;
- aggregate metrics;
- redacted confusion matrices;
- redacted interval-coverage summaries;
- test commands;
- commit and manifest versions;
- known limitations.

Private local evidence includes:

- site-level predictions;
- raw reference rows;
- coordinates;
- source documents;
- feature matrices;
- model artifacts;
- support-distance values tied to private candidates.

## Stop conditions

Stop validation and keep depth disabled when:

- known-depth records are absent;
- the dataset contract fails;
- train, validation, and holdout groups overlap;
- final holdout data influenced method design;
- simple baselines perform equally well or better;
- confounder-only performance explains the claimed result;
- subgroup or site performance is unstable;
- interval coverage fails;
- unsupported cases receive confident output;
- a proxy is converted directly into metres;
- depth changes existing classifier or legacy artifacts;
- private details become HTTP-served unexpectedly;
- wording implies physical confirmation;
- required tests are skipped without an approved reason;
- the full existing regression suite fails.

## Release decision rules

### Relative mode

May be considered only when:

- dataset and provenance gates pass;
- relative scientific holdout validation passes;
- confounder and support gates pass for approved groups;
- software, privacy, wording, and legacy tests pass;
- a frozen relative-only package exists.

### Numerical mode

May be considered only when all relative-mode gates pass and:

- the numerical method beats its baselines;
- interval coverage and error gates pass;
- metre-range support is documented;
- unsupported and out-of-range cases abstain;
- the numerical package and acceptance report are frozen.

Neither mode is approved merely because this specification exists.

## Phase 8 checklist

- [x] Separate contract, software, scientific, and release validation.
- [x] Define the release matrix for `off`, `relative_only`, and `numerical_range`.
- [x] Define calibration-dataset validation.
- [x] Define frozen-fixture privacy rules.
- [x] Define depth-stage unit tests.
- [x] Define pipeline and artifact integration tests.
- [x] Define relative-depth holdout tests.
- [x] Define numerical-range holdout tests.
- [x] Define confounder and support tests.
- [x] Define negative and no-target tests.
- [x] Define threshold and repeated-run stability tests.
- [x] Define legacy compatibility and regression tests.
- [x] Define output schema and privacy tests.
- [x] Define easy-English wording and accessibility tests.
- [x] Define the full private-local acceptance record.
- [ ] Populate independently measured or independently documented known-depth records.
- [ ] Build and validate the private calibration dataset.
- [ ] Fit and test the Phase 3 relative baseline.
- [ ] Fit and test a Phase 4 numerical method only if Phase 3 passes.
- [ ] Run Phase 5 confounder and support testing.
- [ ] Implement the Phase 6 backend stage.
- [ ] Implement the Phase 7 local presentation when approved.
- [ ] Create the planned automated tests.
- [ ] Run the complete backend and frontend regression suites.
- [ ] Produce a frozen acceptance report.
- [ ] Approve and enable any depth mode.

## Phase 8 decision

```text
Validation-gate design: complete
Automated depth tests: not created
Scientific validation: blocked
Full regression validation: not run
Relative-depth release: not approved
Numerical-depth release: not approved
App depth output: not available
```
