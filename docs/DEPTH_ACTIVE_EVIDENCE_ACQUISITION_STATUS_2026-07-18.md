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

Current candidates include:

- Guangzhou University GPR data with underground pipelines described at different layouts and depths; archive inspection is required to find an explicit depth table.
- Hacimusalar geophysical survey data over a shallow buried wall; the associated article and numerical ground-truth details require verification.
- Real GPR and non-destructive-testing databases with concrete cover depth or laboratory specimens; useful for method development but not automatically transferable to buried-field Sentinel-1 estimation.
- Simulated GPR datasets with exact generated depths; useful for software and baseline testing only, not real calibration evidence.

None of these candidates should be rejected merely because they are not immediately ready. Each candidate moves through a qualification workflow.

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
- [ ] Inspect the Guangzhou archive structure for explicit pipeline-depth metadata.
- [ ] Inspect Hacimusalar files and related publication for numerical wall depth and uncertainty.
- [ ] Screen real GPR cover-depth and laboratory datasets as supporting evidence.
- [ ] Expand the search to utility-owner, civil-engineering, archaeological, and infrastructure repositories.
- [ ] Build a candidate-evidence register with provenance, depth fields, site groups, licences, and suitability decisions.
- [ ] Import the first verified record into the private calibration pack.
- [ ] Run the relative-depth experiment when the private pack reaches contract readiness.

## Current decision

```text
overall_depth_work = active_evidence_acquisition
software_work = active
online_search = active
candidate_screening = active
private_pack_record_count = 0
relative_model_claim = not_yet_supported
numerical_model_claim = not_yet_supported
app_depth_output = not_available
```

The correct response to missing evidence is to continue searching and qualifying evidence, not to stop the project.