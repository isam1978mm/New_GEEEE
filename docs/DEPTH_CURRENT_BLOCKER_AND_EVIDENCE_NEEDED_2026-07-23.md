# Current Depth Blocker and Evidence Needed

**Date:** 2026-07-23  
**Branch:** `main`  
**Status:** authoritative plain-English clarification

## The project is not fully blocked

The application, satellite processing, classifier reliability work, testing, and other non-depth work may continue.

The blocked capability is specifically:

```text
reliable relative-depth research
numerical depth estimation
app depth output
```

The project must not claim a real depth estimate until independent physical evidence and held-out validation exist.

## Current blocker

The repository has no usable calibration dataset containing independently verified physical depth.

The missing dataset must establish, without using the notebook or satellite prediction as truth:

1. the real depth from the observation surface to the **top of a buried reference feature**;
2. a numerical uncertainty or bounded accuracy for that depth;
3. the mapped physical area and dates for matching Sentinel-1 observations;
4. independently confirmed no-target comparison areas;
5. independent site groups for train, validation, and untouched holdout;
6. evidence that radar differences track depth rather than grading, vegetation, moisture, or other surface work.

This is the current reason depth remains unavailable. It is not a software bug and it cannot be solved by inventing values or by reusing notebook predictions as labels.

## What evidence is being looked for

For each positive site, the useful evidence package would contain:

- a signed survey, as-built record, engineering record, or controlled-site measurement;
- a mapped buried feature large enough for the approved Sentinel-1 experiment;
- measured depth to the **top** of that feature;
- survey accuracy, registration tolerance, or another defensible numerical uncertainty;
- construction and survey dates;
- enough geometry to match the site to Sentinel-1 observations;
- target material, dimensions, surface condition, terrain, and major construction context;
- a traceable source independent of the app and notebook.

For each negative site or comparison area, the useful evidence would independently prove that the analysis footprint contains no target. Examples include:

- a documented empty controlled-test area;
- a pre-placement survey showing no target;
- multi-point investigation covering the full comparison footprint;
- construction records proving the area remained empty.

A quiet radar pixel, an untreated-looking nearby area, or one borehole is not enough.

## Minimum structure needed

The validator's technical floor requires three independent split groups:

| Split | Required positive | Required negative |
|---|---:|---:|
| Train | 1 | 1 |
| Validation | 1 | 1 |
| Holdout | 1 | 1 |

No site, feature, or group may be reused across those splits.

This six-record floor only proves that the data contract can run. It does not by itself prove that a scientifically useful depth model exists. More records may be needed.

## Where the missing evidence could come from

The evidence could come from any legitimate data holder or future measurement source, for example:

- a site owner;
- an engineering or surveying company;
- an agency's complete project file;
- a university or controlled-test-site team;
- a professional field survey.

The project owner is **not assumed to already possess these files**. No task is assigned to the owner unless access to such a source actually exists.

## What has stopped

The general public-candidate search reached its agreed stopping rule and is closed.

Do not:

- start another broad internet search for more sites;
- treat the three hold candidates as usable calibration sites;
- ask the project owner to produce records they have never said they possess;
- lower the evidence standard merely to pass the validator.

## What can happen next

### When no new evidence is available

Record the blocker honestly and continue other project work that does not claim depth.

### When one evidence package becomes available

Review it read-only and return one decision:

```text
good_to_go_for_private_intake
hold_missing_one_obtainable_item
reject_first_unrecoverable_gate
```

### After enough independent packages are available

Populate the private calibration pack outside Git, validate it, run the radar-linkage experiment, and only then consider model fitting and app integration.

## Current state

```text
public_candidate_search = closed
usable_known_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
private_calibration_pack_tools = ready
real_calibration_records = absent
relative_depth_research = blocked_missing_independent_evidence
numerical_depth = not_available
app_depth_output = disabled
other_project_work = may_continue
```

## One-sentence summary

Depth is blocked because the project has no independent measured depth-and-negative dataset across separate train, validation, and holdout sites; the search for more public candidates is closed, and other project work may continue without claiming depth.