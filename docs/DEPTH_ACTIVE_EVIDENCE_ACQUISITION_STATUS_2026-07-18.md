# Depth Active Evidence Acquisition Status — 2026-07-18

## Current status

The depth work is **active**, not stopped.

The project currently has two separate status tracks:

```text
research_and_evidence_work = active
app_depth_claim_and_activation = gated
```

The absence of a ready calibration pack does not end the work. It defines the current workstream: search, screen, acquire, inspect, and qualify external calibration evidence; improve safe local intake tooling; and prepare reproducible experiments.

## What may proceed now

The following work is approved on `main`:

1. Search public, institutional, and professionally managed datasets for independently documented depth evidence.
2. Inspect candidate archives and metadata for explicit per-record or per-site depth values.
3. Verify provenance, licence, measurement method, uncertainty, dates, sites, and grouping.
4. Download and inspect public research datasets in private local storage when needed.
5. Contact dataset authors or custodians for missing depth tables or documentation.
6. Build neutral private source-index entries for evidence that passes screening.
7. Develop import, conversion, validation, and experiment tooling using synthetic fixtures or verified public data.
8. Test baselines and data-processing code without claiming scientific success.
9. Match candidate evidence sites to available satellite observations where the site, date, scale, and sensor support a defensible experiment.
10. Reject unsuitable sources and record why they are unsuitable.

## What remains gated

The following require verified evidence and scientific validation:

```text
claim_that_depth_estimation_works
relative_depth_release
numerical_depth_release
normal_app_depth_output
frontend_depth_result
```

A gate is not a stop-work order. It prevents unsupported output while research continues.

## Evidence search findings so far

### Verified installed or surveyed physical-depth candidates

- **TU1208 / IFSTTAR Nantes**: independently surveyed controlled targets and public raw GPR data. Target-level depth-reference extraction is still in progress.
- **IAG/USP**: installed controlled targets with an open table of eight real depths. The extracted values are now stored in a repository-safe machine-readable candidate file, with material, orientation, and dimensions added for the Line 4 drums and reference pipe.
- **Texas A&M University–Corpus Christi**: controlled 50 m by 50 m site with known target types, orientations, and depths from approximately 0.5 m to 3.0 m. Target-level construction tables and raw measurements still need to be obtained.
- **Ahmadu Bello University**: controlled 55 m by 55 m site with an open table of eight explicit depth-to-top values from 0.5 m to 1.2 m. The values are now stored in the candidate file; underlying field datasets are available from the authors on request.

### Candidates still under review

- Guangzhou University GPR data with underground pipelines described at different layouts and depths. The public archive preview exposes many raw files but no obvious depth table or README.
- Hacimusalar multi-method survey data over a buried wall. A publication reports an interpreted depth of approximately 1.2 m, but independent excavation or engineering confirmation has not yet been found.
- Morocco utilities and voids GPR data. Useful for detection and classification, but public metadata does not establish independently documented numerical depths.
- Simulated GPR datasets with exact generated depths. Useful for software and baseline testing only, not real calibration evidence.

None of these candidates should be rejected merely because they are not immediately ready. Each candidate moves through a qualification workflow.

## Extracted public evidence

Repository-safe public candidate evidence now contains:

```text
physical_site_groups_with_extracted_tables = 2
candidate_target_rows = 16
explicit_depth_to_top_rows = 8
controlled_real_depth_rows_with_target_top_support = 8
reported_reference_uncertainty_rows = 0
private_pack_import_approved_rows = 0
```

The missing uncertainty values remain an active evidence-recovery task. They were not guessed or replaced with invented defaults.

## Satellite-scale finding

Official Sentinel-1 IW GRD High Resolution products have approximately 20 m by 22 m independent spatial resolution with 10 m pixel spacing.

The compact controlled sites therefore do not support one satellite sample per buried object. Individual targets, trenches, and neighboring objects mix within the same resolution footprints.

The active satellite path is now:

```text
whole_physical_site_or_large_isolated_section_pre_post_experiment
```

not:

```text
individual_small_target_satellite_depth_row
```

Texas A&M–Corpus Christi is the strongest immediate pre/post candidate because its construction occurred during the Sentinel-1 mission era and an official pre-installation survey is documented. Ahmadu Bello is also a priority after its exact installation dates are recovered. TU1208 and IAG/USP remain valuable for ground-method truth and later post-installation satellite sanity checks.

## Software verification

The owner ran the committed validator and tests on Windows with Python 3.13.5.

Observed results:

```text
public-candidate validator = validation_passed
candidate readiness = candidate_evidence_structurally_valid_not_import_approved
candidate source count = 2
candidate physical-site groups = 2
candidate target rows = 16
candidate validator tests = 7 passed
C1 redaction-risk tests = 3 passed
full unit suite = 940 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, one expected raster georeferencing warning, and the local pytest cache-write access warning. They did not affect the passing result.

The public candidate file remains correctly unapproved for private-pack import because no reference-uncertainty rows are yet documented and the satellite support experiment has not passed.

## Qualification workflow

For every candidate source:

```text
find source
→ verify licence and provenance
→ inspect files and metadata
→ locate explicit depth truth
→ confirm measurement method and uncertainty
→ identify independent sites or groups
→ determine sensor and scale compatibility
→ classify as direct evidence, supporting evidence, software-only evidence, or unsuitable
→ import only verified records
```

## Status vocabulary

Use these terms consistently:

```text
active_evidence_acquisition
candidate_under_review
evidence_verified
evidence_rejected_with_reason
dataset_contract_ready
relative_research_ready
app_activation_not_approved
```

Do not describe the overall project as blocked while evidence search, source inspection, data acquisition, tooling, or experiments can continue.

## Immediate execution queue

- [x] Implement private calibration-pack initializer.
- [x] Implement aggregate-only validator and finalizer.
- [x] Harden readiness to require eligible positives and negatives in each split.
- [x] Implement dry-run-first private record intake.
- [x] Search online and identify initial candidate datasets.
- [x] Inspect the public Guangzhou archive preview.
- [x] Inspect the Hacimusalar dataset description and related publications.
- [x] Identify four independently installed or surveyed physical-site candidates.
- [x] Build a candidate-evidence register.
- [x] Extract IAG/USP real target depths and target mapping.
- [x] Extract Ahmadu Bello explicit depth-to-top values.
- [x] Create a machine-readable public candidate file.
- [x] Implement an aggregate-only candidate evidence validator.
- [x] Add candidate-validator regression tests.
- [x] Run the first satellite-scale compatibility screen.
- [x] Run the candidate validator: structurally valid and correctly not import-approved.
- [x] Run candidate-validator tests: 7 passed.
- [x] Run C1 privacy tests: 3 passed.
- [x] Run the full unit suite: 940 passed.
- [ ] Extract TU1208 target-level depth-to-top definitions.
- [ ] Obtain Texas A&M–Corpus Christi target-level construction tables and raw-data availability.
- [ ] Recover reference-depth uncertainty for IAG/USP and Ahmadu Bello.
- [ ] Recover exact construction dates for the satellite-era controlled sites.
- [ ] Verify Sentinel-1 acquisition coverage and observation geometry.
- [ ] Define private whole-site and background windows.
- [ ] Run matched pre/post approved-feature extraction.
- [ ] Add independently documented confirmed-background records.
- [ ] Import only records that satisfy the complete private calibration contract.
- [ ] Run the relative-depth experiment when the private pack reaches contract readiness.

## Current decision

```text
overall_depth_work = active_evidence_acquisition
software_work = active
online_search = active
candidate_screening = active
independent_depth_sources_found = 4
physical_site_groups_with_extracted_target_tables = 2
public_candidate_target_rows = 16
candidate_register = created
candidate_validator = implemented_and_verified
candidate_validator_tests = 7_passed
full_unit_suite = 940_passed
satellite_scale_screen = complete_first_pass
private_pack_record_count = 0
relative_model_claim = not_yet_supported
numerical_model_claim = not_yet_supported
app_depth_output = not_available
```

The correct response to missing evidence is to continue searching and qualifying evidence, not to stop the project.
