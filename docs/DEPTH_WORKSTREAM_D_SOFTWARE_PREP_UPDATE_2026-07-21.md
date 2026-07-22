# Depth Workstream D Software-Preparation Update — 2026-07-21

Status: `software_preparation_active`; scientific validation remains blocked.

## Decision

The broad Blocker 2 landfill search is stopped. Słabomierz–Krzyżówka is retained as a strong post-closure settlement-method reference with published matched surfaces and centimetre-level checks, but it is not a contract-ready buried-depth calibration pack.

Blocker 2 has therefore not passed the authoritative pass condition. The private calibration pack still lacks eligible known-depth positives and independently confirmed negatives across train, validation, and untouched holdout physical-site groups.

The execution plan explicitly allows Workstream D software preparation before the private pack is ready, so the next work moved to frozen baselines, synthetic evaluation behavior, privacy-safe aggregation, and preregistration.

## Completed in this update

### D1 — Baseline definitions

The existing `docs/DEPTH_RELATIVE_BASELINE_SPEC.md` already defines the required relative baselines and marks baseline design complete.

### D2 — Synthetic evaluation harness

Added:

- `scripts/depth_evaluation_harness.py`
- `tests/unit/test_depth_evaluation_harness.py`

The harness provides deterministic software-test implementations for:

- majority-class baseline;
- stratified-random baseline with a frozen seed;
- one-feature threshold baseline with already-frozen thresholds;
- median-depth baseline;
- relative-class midpoint baseline;
- physical-group leakage rejection;
- balanced accuracy and macro F1;
- per-class precision, recall, and F1;
- ordinal one-class-off and two-class-off rates;
- shallow-versus-deep confusion;
- abstention and non-abstained coverage;
- numerical interval coverage and width;
- minimum-count subgroup suppression;
- unsupported-condition refusal;
- aggregate-only output with identity-field checks;
- an explicit synthetic-fixture-only guard.

The harness always reports:

```text
scientific_validation_run = false
training_started = false
private_rows_printed = false
```

Local focused validation passed 11 harness tests. No GitHub Actions run was attached to the commit.

Harness commits:

- implementation: `70f6792b772798c2a77f189f1379aee55f6ba92a`
- tests: `6b8ecc056b76c1daddb098529d0e4f3f75304628`

### D3 — Preregistration framework

Added:

- `docs/DEPTH_PREREGISTRATION_FRAMEWORK_V1.md`
- `tests/unit/test_depth_preregistration_contract.py`

The framework freezes:

- the software-versus-science boundary;
- train/validation-only selection rules;
- holdout-access prohibition;
- required relative and numerical metrics;
- required baseline comparisons;
- confounder and support checks;
- abstention rules;
- amendment policy;
- the required final private freeze record.

Numeric acceptance thresholds remain intentionally pending. They may be set only after a contract-ready dataset exists and training/validation-only dataset-size, prevalence, uncertainty, and performance analysis is available. Missing freeze values keep `holdout_opened=false`.

Local focused validation passed 14 combined harness and preregistration tests. No scientific result was produced.

Preregistration commits:

- framework: `a346ee728d18e44d49a3381ba6b3b3d67fa0fe45`
- tests: `d26af3a505c9c6411f7d37dbaeb945c8bbe0f88d`

## Current blocker state

```text
blocker_1_cause_attribution = unresolved
blocker_2_contract_ready_pack = blocked_missing_contract_ready_pack
workstream_D1_baseline_design = completed
workstream_D2_synthetic_harness = completed_software_only
workstream_D3_preregistration_framework = framework_frozen_threshold_values_pending
workstream_C_private_pack = blocked_missing_qualified_records
workstream_E_relative_validation = gated
workstream_F_numerical_validation = gated
workstream_G_app_release = gated
depth_mode = off
visible_depth_result = not_available
```

## Waiting for

```text
contract_eligible_known_depth_positive_sites
+ independently_confirmed_negative_sites
+ group_separated_train_validation_holdout_coverage
+ complete_reference_uncertainty
+ sensor_and_scale_support
+ frozen_neutral_feature_manifest
+ finalized_private_pack_hashes
```

## Next valid step

Continue only the finite unresolved evidence tasks needed to form a contract-ready private pack, especially reference uncertainty and confirmed negatives. Do not fit a model, open the holdout, claim depth performance, or enable app depth until the pack passes.
