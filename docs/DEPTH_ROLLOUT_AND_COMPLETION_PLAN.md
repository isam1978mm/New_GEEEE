# Depth Rollout and Completion Plan

Status: Phase 9 planning artifact only. It defines execution order and completion gates. It does not implement a depth model, backend stage, API field, frontend panel, or depth result.

## Plain-English purpose

This document prevents the project from jumping directly from planning to showing depth in the app.

The correct order is:

```text
understand current signals
→ build a private known-depth dataset
→ test broad relative depth
→ test numerical ranges
→ test soil, terrain, moisture, size, season, and site bias
→ implement the backend stage
→ add the local explanation panel
→ run all validation and compatibility tests
→ enable only the mode that actually passed
```

If a step fails, the following steps remain blocked.

## Current project position

```text
feature inventory = complete
calibration schema = complete
known-depth records = absent
relative-depth design = complete
relative-depth fitting = blocked
numerical-range design = complete
numerical fitting = blocked
confounder-control design = complete
confounder testing = blocked
backend architecture design = complete
backend implementation = blocked
presentation design = complete
frontend implementation = blocked
validation design = complete
validation execution = blocked
app depth output = not_available
```

The next real work is not backend or frontend coding.

The next real work is:

```text
populate and validate a private local calibration dataset
```

## Required rollout order

### Step 1 — Preserve the scope lock

Keep the target definition fixed:

```text
depth to the top of the independently documented reference feature
```

First possible output:

```text
relative shallow / medium / deep
```

Numerical metre ranges remain later.

Do not change this definition during fitting unless the plan and all dependent contracts are versioned again.

### Step 2 — Maintain the feature inventory

Use `docs/DEPTH_FEATURE_INVENTORY.md` as the approved starting inventory.

Before an experiment:

- freeze the exact feature list;
- record source bands, formulas, units, resolution, nodata, preprocessing, and acquisition information;
- exclude classifier scores, classifier classes, PCA decisions, target masks, generated labels, and unknown-provenance depth arrays;
- keep duplicate algebraic transforms from being treated as independent evidence.

Output:

```text
feature_manifest.json
```

### Step 3 — Build the private calibration dataset

Use `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`.

The dataset remains:

```text
local
private
outside Git
not HTTP-served
not visible in the normal frontend
```

Required work:

1. enter independently measured or independently documented known-depth records;
2. enter confirmed no-target or background cases;
3. record uncertainty in each known depth;
4. record site, feature, and group identifiers without putting raw coordinates in Git;
5. record soil, surface, moisture, season, terrain, target size, and target family when available;
6. separate train, validation, and untouched physical-site holdout groups;
7. version and hash the dataset;
8. produce an exclusion ledger.

No app or notebook result may be used as the true depth label.

### Step 4 — Run the relative-depth experiment

Use `docs/DEPTH_RELATIVE_BASELINE_SPEC.md`.

Run simple methods first:

```text
majority baseline
stratified-random baseline
one-feature rule
ordinal logistic regression
small decision tree
```

The experiment asks only whether approved signals can distinguish broad depth categories on unseen physical sites.

Do not claim metres.

Pass condition:

- better than simple baselines on untouched sites;
- acceptable confusion between shallow and deep;
- documented abstention;
- stable performance across supported conditions;
- no site or confounder leakage.

Failure condition:

```text
relative_depth_status = not_approved
```

If relative depth fails, stop. Do not continue to numerical modelling.

### Step 5 — Run numerical range research only if Step 4 passes

Use `docs/DEPTH_NUMERICAL_RANGE_SPEC.md`.

Start with simple numerical baselines and interval methods.

The result must be a range, not one exact number.

Required evaluation includes:

- median absolute error;
- bias;
- interval coverage;
- interval width;
- site-level performance;
- performance by depth band and supported groups;
- out-of-support refusal;
- reference-depth uncertainty.

Failure condition:

```text
numerical_depth_status = not_approved
```

A failed numerical phase does not invalidate an already passed relative-only method.

### Step 6 — Run confounder and support testing

Use `docs/DEPTH_CONFOUNDER_CONTROL_SPEC.md`.

Test whether the model is learning depth or merely learning:

- physical site;
- soil or surface;
- moisture or season;
- terrain;
- target size;
- target family or material;
- radar angle or orbit geometry;
- resolution or preprocessing;
- observation count or data quality.

Unsupported combinations must return:

```text
depth_status = insufficient_data
```

Only groups with documented support may be approved.

### Step 7 — Freeze the private method package

A method package must be created outside Git only after the applicable scientific gates pass.

Minimum package contents:

```text
depth_method_manifest.json
calibration_manifest.json
feature_manifest.json
preprocessing_manifest.json
support_rules.json
model artifact or rule definition
checksums.sha256
```

The package must identify:

- method version;
- calibration dataset version;
- feature order;
- supported finding families;
- supported depth range;
- supported sensor and confounder ranges;
- abstention rules;
- hashes.

The app must not download or invent a package automatically.

### Step 8 — Implement the backend stage

Use `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`.

Future stage:

```text
DepthEstimationStage
```

Future location:

```text
RunQualityStage
→ DepthEstimationStage
```

The first code slice must:

- default to mode `off`;
- preserve old runs;
- preserve classifier and `experimental/` artifacts;
- read only approved features;
- verify package hashes and versions;
- refuse blocked or unsupported runs;
- write detailed outputs as `FILESYSTEM_ONLY` and `http_servable=false`;
- never substitute a notebook proxy for a missing model.

Implementation should be small and testable, not a monolithic depth engine.

### Step 9 — Implement the local explanation panel

Use `docs/DEPTH_EASY_ENGLISH_PRESENTATION_SPEC.md`.

The depth panel remains separate from the classifier panel.

It may show:

```text
depth result
relative category or estimated range
quality
main uncertainty
method version
```

It must not show raw feature rows, coordinates, private source references, local paths, or calibration records.

It must not display an invented confidence percentage.

### Step 10 — Execute all validation gates

Use `docs/DEPTH_VALIDATION_GATES_SPEC.md`.

Run:

- contract validation;
- unit tests;
- integration tests;
- physical-site scientific holdout tests;
- negative and no-target tests;
- confounder and support tests;
- repeated-run stability tests;
- package-integrity tests;
- output-schema and privacy tests;
- easy-English wording tests;
- old-run and classifier compatibility tests;
- complete backend regression suite;
- frontend build and static tests.

Passing software tests alone is not sufficient.

### Step 11 — Produce a frozen acceptance report

The private acceptance record must identify:

```text
application commit
calibration dataset version
feature manifest version
model or rule version
support policy version
wording version
approved output mode
approved finding families
approved depth range
approved conditions
unsupported conditions
all test and scientific results
known limitations
```

Private site-level material stays outside Git.

A redacted aggregate report may be committed.

### Step 12 — Enable only the approved mode

Possible final modes:

```text
off
relative_only
numerical_range
```

Rules:

- `off` remains the default until activation is approved;
- `relative_only` may be enabled when relative validation passes even if numerical validation fails;
- `numerical_range` requires all relative, numerical, confounder, software, privacy, wording, and compatibility gates to pass;
- unsupported candidates must still return `insufficient_data`;
- old runs remain usable without depth.

## Stop rules

Stop and keep depth disabled when:

- known-depth records are absent;
- the dataset contract fails;
- train and holdout physical groups overlap;
- a label comes from the app or notebook;
- simple baselines perform equally well or better;
- site, soil, season, size, terrain, or another confounder explains the result;
- subgroup performance is unstable;
- intervals are inaccurate or too wide;
- unsupported cases receive confident output;
- a proxy ratio is converted directly into metres;
- classifier or legacy outputs change;
- private details become normally downloadable or HTTP-served;
- wording implies physical confirmation;
- the full regression suite fails.

## Definition of complete

Depth work is complete only when all applicable items are true:

- the depth definition is fixed;
- the private calibration dataset is populated, versioned, hashed, and traceable;
- physical-site holdout results are documented;
- the approved mode beats its baselines;
- confounder and support testing pass;
- unsupported cases abstain;
- uncertainty is shown honestly;
- the backend stage is implemented and tested;
- the optional local panel is implemented and tested;
- old runs and existing outputs remain compatible;
- detailed artifacts remain private and local;
- a frozen acceptance report exists;
- activation is explicitly approved.

Planning completion is not product completion.

## Phase 9 checklist

- [x] Lock the rollout order.
- [x] Identify the next real action as calibration-data population.
- [x] Keep backend implementation after scientific validation.
- [x] Keep frontend implementation after backend and wording approval.
- [x] Define stop rules.
- [x] Define method-package freezing order.
- [x] Define final acceptance-report requirements.
- [x] Define relative-only and numerical activation paths separately.
- [x] Define the final completion meaning.
- [ ] Populate independently measured or independently documented known-depth records.
- [ ] Validate and hash the private calibration dataset.
- [ ] Run the relative-depth experiment.
- [ ] Approve or reject relative-only output.
- [ ] Run numerical-range research only if relative depth passes.
- [ ] Run confounder and support testing.
- [ ] Freeze an approved local method package.
- [ ] Implement and test the backend stage.
- [ ] Implement and test the local depth panel when approved.
- [ ] Run all validation and regression gates.
- [ ] Produce the frozen acceptance report.
- [ ] Approve and enable an output mode.

## Phase 9 decision

```text
Rollout-order design: complete
Depth planning phases: documented
Next real action: populate private calibration dataset
Known-depth records: absent
Relative experiment: blocked
Numerical experiment: blocked
Backend implementation: blocked
Frontend implementation: blocked
Depth activation: not approved
Current app depth output: not_available
```
