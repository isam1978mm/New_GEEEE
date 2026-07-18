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

### Verified physical-depth evidence candidates

- **TU1208 / IFSTTAR Nantes controlled test site**: targets were physically installed, geolocated with a theodolite, and assigned depths from surveyed target and surface elevations. Public raw GPR data and a detailed site paper are available. Published follow-on work reports three pipe layers at approximately 0.9 m, 1.5 m, and 2.1 m, but the depth-to-top versus center-depth definition still requires extraction from the original site figures.
- **IAG/USP controlled geophysics test site**: targets were installed at known positions and depths. Published work reports seven target lines spanning approximately 0.5 m to 2.5 m, including a GPR study of precisely buried drums from approximately 0.5 m to 2.0 m. Actual target tables and raw-data access still require extraction.

### Candidates still under review

- Guangzhou University GPR data with underground pipelines described at different layouts and depths. The public archive preview exposes many raw files but no obvious depth table or README.
- Hacimusalar multi-method survey data over a buried wall. A publication reports an interpreted depth of approximately 1.2 m, but independent excavation or engineering confirmation has not yet been found.
- Morocco utilities and voids GPR data. Useful for detection and classification, but public metadata does not establish independently documented numerical depths.
- Simulated GPR datasets with exact generated depths. Useful for software and baseline testing only, not real calibration evidence.

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
- [x] Inspect the public Guangzhou archive preview.
- [x] Inspect the Hacimusalar dataset description and related publications.
- [x] Identify TU1208 as independently surveyed physical-depth evidence.
- [x] Identify IAG/USP as installed known-depth evidence.
- [x] Build a candidate-evidence register with provenance, depth fields, site groups, licences, and suitability decisions.
- [ ] Extract TU1208 target-level depth-to-top values from the original site figures.
- [ ] Extract IAG/USP actual target depths and target metadata from the published tables.
- [ ] Confirm raw-data access and machine-readable target mapping for IAG/USP.
- [ ] Complete Guangzhou metadata inspection or contact the authors for the depth map.
- [ ] Find independent confirmation for Hacimusalar or keep it as supporting evidence only.
- [ ] Expand the search to additional independent physical sites so holdout validation is possible.
- [ ] Run satellite-scale and approved-feature compatibility screening.
- [ ] Import the first verified, supportable record into the private calibration pack.
- [ ] Run the relative-depth experiment when the private pack reaches contract readiness.

## Current decision

```text
overall_depth_work = active_evidence_acquisition
software_work = active
online_search = active
candidate_screening = active
independent_depth_sources_found = 2
candidate_register = created
private_pack_record_count = 0
relative_model_claim = not_yet_supported
numerical_model_claim = not_yet_supported
app_depth_output = not_available
```

The correct response to missing evidence is to continue searching and qualifying evidence, not to stop the project.
