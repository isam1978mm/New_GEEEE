# Depth Confirmed-Background Candidate Qualification — 2026-07-20

Status: active evidence qualification for the private local depth-research workflow. This document separates independently documented ground-method background evidence from approved Sentinel-1 confirmed-negative calibration records. It does not approve private-pack import, model fitting, or app depth output.

## Purpose

The depth dataset contract requires independently supported `confirmed_no_target` records. A quiet satellite pixel, visually normal area, land-cover class, heuristic false positive, or pre-installation statement alone does not automatically satisfy this requirement.

Two current controlled-site candidates have documented pre-installation or pre-burial evidence:

```text
N1 = Texas A&M University-Corpus Christi controlled site
N2 = Ahmadu Bello University Geophysics Test Site
```

Both are useful candidates. Neither is currently approved as a Sentinel-1 confirmed-negative record.

## N1 — Texas A&M University-Corpus Christi

### Verified evidence

- the 50 m by 50 m site was surveyed before excavation and target placement to establish existing subsurface objects;
- construction occurred during February and March 2020;
- the field laboratory was completed on 2020-03-04;
- the conservative satellite policy freezes pre-event observations before 2020-02-01 and post-event observations from 2020-04-01 onward;
- the construction transition period remains excluded.

### Current interpretation

The pre-installation survey makes the site a strong background candidate. It does not yet prove that the selected Sentinel-1 analysis window was target-free, stable, and comparable.

### Missing approval evidence

```text
private site boundary = missing
private background/control boundary = missing
pre-installation survey report or data = not acquired
matching Sentinel-1 pre acquisitions = not verified
matching Sentinel-1 post acquisitions = not verified
same orbit and geometry = not verified
season and moisture comparability = not verified
surface-disturbance separation = not verified
```

### Current state

```text
N1_ground_method_background = documented_candidate
N1_sentinel_1_confirmed_negative = not_approved
N1_private_pack_import = not_approved
```

## N2 — Ahmadu Bello University

### Verified evidence

- pre-burial geophysical investigation was performed before target placement;
- the published study states that the pre-burial investigation found no major anomaly that would significantly influence the buried-target response study;
- post-burial measurements were later performed;
- the actual target depths are explicitly reported as depth to top.

### Current interpretation

The source supports an independently documented ground-method background state for the surveyed profiles. It does not yet create a same-sensor Sentinel-1 confirmed-negative record because the exact installation date and matched satellite conditions are missing.

### Missing approval evidence

```text
exact installation date or bounded event interval = missing
private site boundary = missing
private background/control boundary = missing
pre-burial raw data = available_on_request_not_acquired
matching Sentinel-1 pre acquisitions = not verified
matching Sentinel-1 post acquisitions = not verified
same orbit and geometry = not verified
season and moisture comparability = not verified
surface-disturbance separation = not verified
```

### Current state

```text
N2_ground_method_background = documented_candidate
N2_sentinel_1_confirmed_negative = not_approved
N2_private_pack_import = not_approved
```

## Approval rule

A controlled-site background candidate may become a private-pack `confirmed_no_target` record only after all applicable fields are supported:

```text
independent source establishes the pre-target condition
physical site or control window is privately and reproducibly defined
record date or bounded period is known
matching approved sensor acquisitions exist
orbit mode geometry and polarisation are controlled
season and moisture are comparable or explicitly controlled
construction transition and restoration disturbance are excluded
valid-pixel and quality gates pass
site group and leakage group are fixed
source uncertainty and limitations are recorded
```

Depth fields must remain empty for confirmed negatives.

## Non-qualifying substitutes

The following do not satisfy the depth negative contract by themselves:

- ESA WorldCover or another land-cover class;
- Dynamic World labels;
- mining or industrial polygons;
- visually undisturbed imagery;
- low classifier probability;
- no PCA anomaly;
- a quiet radar pixel;
- a heuristic false positive without an independent site investigation;
- an arbitrary background ring selected after seeing the target result.

Those sources may be useful contextual or hard-negative evidence for another governed workflow, but they do not independently establish absence of a buried reference feature.

## Next executable sequence

1. Run the aggregate Sentinel-1 coverage checker for the frozen Texas A&M pre/post periods.
2. Determine whether comparable orbit groups exist on both sides of construction.
3. Obtain or reconstruct a private neutral site window and separately reviewed background window.
4. Request the Texas A&M pre-installation survey materials.
5. Request the Ahmadu Bello construction date and pre-burial data.
6. Qualify ground-method negatives separately from satellite negatives.
7. Import no negative until the aggregate validator and evidence review both pass.

## Current decision

```text
confirmed_negative_record_count = 0
documented_ground_background_candidates = 2
sentinel_1_background_candidates = 2_pending_support
private_pack_negative_import_approved = false
next_repository_task = verify_TAMUCC_sentinel_1_coverage_workflow_readiness
owner_or_source_request_tasks = acquire_preinstallation_and_construction_materials
app_depth_enabled = false
```
