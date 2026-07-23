# Depth Blocker 2 - Private/Direct Data Route

**Date:** 2026-07-23  
**Status:** authorized and started  
**Branch:** `main`

## Decision

The public-candidate search is closed at its 15-candidate hard stop. Do not continue general internet searching for more sites.

The active route is now a **private/direct survey and engineering data intake** using the existing depth-calibration contract and private-pack tools.

This route does not lower the evidence standard. It changes how the missing evidence is obtained.

## Goal

Build a private calibration pack with independent measured depth and confirmed-negative records that can pass the existing validator.

The technical readiness floor is:

- one eligible known-depth positive in `train`;
- one eligible confirmed negative in `train`;
- one eligible known-depth positive in `validation`;
- one eligible confirmed negative in `validation`;
- one eligible known-depth positive in `holdout`;
- one eligible confirmed negative in `holdout`;
- no `site_id`, `feature_id`, or `group_id` reuse across splits.

This six-record floor only proves contract readiness. Scientific model fitting may require more sites and records.

## Minimum positive-site evidence

Each known-depth positive must provide:

1. a mapped physical target or engineered buried mass large enough for the approved Sentinel-1 experiment;
2. measured depth from the observation surface to the **top** of the target;
3. a numerical uncertainty or bounded interval;
4. the survey or construction date and the depth-valid observation period;
5. survey datum/control or enough information to reproduce the depth difference;
6. target dimensions and material/finding family;
7. soil/surface, terrain, season/moisture, and major construction context;
8. a traceable evidence document or measurement file independent of the satellite pipeline;
9. a stable neutral source reference for the private `source_index.csv`;
10. enough geometry and dates to match Sentinel-1 acquisitions privately.

Preferred source files include original survey points, CAD/GIS surfaces, signed as-built drawings, completion reports, survey-control notes, and later settlement/topographic surveys.

## Minimum confirmed-negative evidence

A confirmed negative must cover an analysis footprint large enough for Sentinel-1 and must be supported by independent evidence, such as:

- pre-construction or pre-placement survey proving no target was present;
- multi-point subsurface investigation covering the analysis footprint;
- construction records proving the comparison area remained empty;
- a controlled test-site background area with documented absence;
- another independently reviewed no-target source.

A quiet radar pixel, nearby untreated-looking land, a single borehole, or visual interpretation is not enough.

## Uncertainty routes

A positive may use either:

### Published bound

A signed/sealed record states numerical vertical accuracy, registration tolerance, survey-control accuracy, or a bounded depth interval.

### Derived survey consistency

Use spatial-block resampling plus an unchanged-area accuracy floor. This route requires raw or reconstructable before/after elevations, point locations, and documented stable overlap.

Required label:

```text
depth_reference_method = derived_survey_consistency
uncertainty_is_published_accuracy = false
```

Do not use single-point leave-one-out and do not invent a default uncertainty.

## Existing repository tools

Use the existing private workflow only:

```powershell
python .\scripts\init_depth_calibration_pack.py
python .\scripts\add_depth_calibration_record.py --create-template
python .\scripts\add_depth_calibration_record.py
python .\scripts\add_depth_calibration_record.py --write
python .\scripts\validate_depth_calibration_pack.py
python .\scripts\finalize_depth_calibration_manifest.py --dataset-id "depth-calibration-v001" --dataset-version "v001"
```

The populated dataset, coordinates, source paths, evidence files, and site-level records must remain outside Git in the owner-controlled private dataset folder.

## Execution order

1. Obtain one complete private/direct site package.
2. Review it against Gates 0-8 before entering a record.
3. Initialize the private pack outside Git.
4. Add the first positive and its source-index entry.
5. Add a genuinely confirmed negative for the same split.
6. Repeat with independent groups for validation and untouched holdout.
7. Validate and finalize the pack.
8. Only after the pack passes, run the Sentinel-1 radar-linkage experiment.
9. Do not fit or expose app depth until held-out validation passes.

## Elk Plain handling

Elk Plain remains a hold, not a rejection. It may enter this route only if a directly supplied signed/sealed survey-control note, final record survey, or equivalent document provides the missing numerical control/accuracy information and the later gates can be satisfied.

Do not resume broad Elk Plain web searching.

## What is blocked right now

No private/direct evidence package has been supplied in this session. Therefore:

```text
private_pack_initialization = ready
private_record_intake_tools = ready
known_depth_private_records = absent
confirmed_negative_private_records = absent
contract_readiness = blocked
scientific_depth_validation = blocked
app_depth_output = not_available
```

## Exact next input required

Provide one private/direct site package containing the survey/engineering files listed above. The first review will be read-only and will return only:

- good to go for private intake;
- hold with one clearly missing document;
- reject with the first unrecoverable gate.

No further general candidate search is authorized by this route.