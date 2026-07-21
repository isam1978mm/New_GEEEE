# Blocker 2 Public-Only Unblocking Attempt — Failure Record — 2026-07-21

Status: failed execution path; Blocker 2 remains unresolved and app depth remains disabled.

This document records the outcome of the approved public-only attempt to unblock Blocker 2 without asking the user to conduct surveys, perform research, review source material, or contact source owners.

It must be read together with:

- `docs/DEPTH_REMAINING_BLOCKERS_AND_UNBLOCKING_PLAN_2026-07-20.md`
- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
- `docs/DEPTH_PUBLIC_SOURCE_ELIGIBILITY_MATRIX_2026-07-21.md`

## Decision

```text
blocker_id = 2
execution_path = public_only_online_evidence_search
execution_path_status = failed
blocker_status = unresolved
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

The public-only search did not produce any source that satisfies the complete calibration contract for Sentinel-1 relative-depth research.

This is a failure of the current execution path, not proof that depth calibration is impossible in all future circumstances.

## Scope completed

The search screened the main plausible public source classes:

1. controlled GPR test sites;
2. installed-target university test sites;
3. trial-trench and open-trench utility datasets;
4. municipal sewer and as-built engineering datasets;
5. underground storage-tank registries;
6. public tunnel projects and controlled tunnel datasets;
7. landfill and large buried-infrastructure inventories;
8. Sentinel-1 archaeology and construction-change studies;
9. simulated GPR datasets for software testing;
10. public sources with same-site background or anomaly-free areas.

The search also consolidated the results into a source eligibility matrix so method-only, context-only, simulated, incomplete, or scale-incompatible sources cannot be promoted into calibration truth.

## What was found

The public search found useful evidence for other purposes:

- independently installed or surveyed target depths at controlled GPR sites;
- public raw GPR radargrams;
- excavation-verified utility records;
- public engineering cover depth and pipe-elevation fields;
- public construction dates for some underground assets;
- large satellite-scale tunnels and landfill boundaries;
- same-site background, anomaly-free, or no-pipe controls;
- several independent project groups in some ground-method datasets.

These findings remain useful for:

- GPR and ground-method validation;
- geometry and excavation research;
- public engineering context;
- construction-date and confounder screening;
- software and synthetic testing;
- exploratory whole-site Sentinel-1 change analysis without a depth claim.

## Why the attempt failed

No screened public source supplied the full required combination:

```text
traceable depth_to_top
+ numerical depth-reference uncertainty
+ reliable Sentinel-1 sensor linkage
+ defensible satellite-scale analysis support
+ independently confirmed positive records
+ independently confirmed negative records
+ several independent physical-site groups
+ exact observation or construction dates
+ train, validation, and untouched holdout eligibility
```

The recurring failures were:

### F1 — Missing numerical uncertainty

Many controlled sites publish installed depths but do not publish survey, placement, or final depth-reference uncertainty.

### F2 — Ambiguous or incomplete depth reference

Some sources report a depth without establishing whether it means depth to target top, centre, axis, base, excavation depth, or another datum.

### F3 — Sentinel-1 scale mismatch

Most buried pipes, drums, cables, buckets, and individual test targets are too small and too closely spaced to serve as independent target-level Sentinel-1 calibration units.

### F4 — Missing matched sensor linkage

Ground-method datasets generally do not include matched Sentinel-1 observations and acquisition references tied to the independently known depth case.

### F5 — Missing independent negatives

Same-site background, no-pipe trenches, pre-installation measurements, anomaly-free radargrams, and open-trench empty areas may be useful controls, but they do not automatically satisfy the contract for independent `confirmed_no_target` physical-site records.

### F6 — Insufficient physical-site groups

Many strong controlled datasets contain numerous profiles or targets at only one compact physical site. Those profiles cannot be split as independent training, validation, and holdout sites.

### F7 — Large structures lack exact shallow labels

Public tunnel and landfill sources can be satellite scale, but they usually provide depth ranges, project-level summaries, capacities, volumes, or boundaries rather than exact shallow depth-to-top records with uncertainty.

## Prohibited response to this failure

Do not respond to this failure by:

- inventing uncertainty values;
- converting target centre or axis depth into depth-to-top without source support;
- treating notebook outputs as physical truth;
- treating profiles from one compact site as independent sites;
- treating same-site background as an independent negative holdout;
- using simulation as real scientific calibration;
- converting engineering capacity, volume, or generic cover rules into site-specific depth;
- fitting a model with an empty or research-ineligible holdout;
- enabling app depth output;
- reporting a confidence or confirmation percentage.

## Current consequence

```text
relative_depth = blocked_missing_contract_complete_calibration_pack
numerical_depth = blocked_missing_relative_model_and_holdout_validation
confidence_percentage = blocked_missing_calibration_and_holdout_evidence
visible_depth_result = not_available
```

Blocker 3 cannot begin because Blocker 2 did not produce a valid calibration pack.

Blocker 4 cannot begin because no scientifically validated model exists.

## Reopen conditions

Blocker 2 may be reopened only when a new source or package provides enough evidence to create contract-eligible records, including:

- independently documented depth to the top of the feature;
- numerical uncertainty or a source-backed bounded interval;
- exact site and observation grouping;
- matched approved sensor acquisitions;
- defensible Sentinel-1 scale and support;
- independently confirmed negatives;
- enough separate physical sites for train, validation, and untouched holdout splits.

A newly discovered public dataset may trigger reopening. Private source material may also trigger reopening only if its use is separately approved. This document does not authorize contacting people, requesting data, or asking the user to perform fieldwork or research.

## Final failure statement

```text
The public-only Blocker 2 unblocking attempt is complete and unsuccessful.
No eligible Sentinel-1 calibration records were produced.
Blocker 2 remains unresolved.
Depth training must not start.
App depth must remain off.
```
