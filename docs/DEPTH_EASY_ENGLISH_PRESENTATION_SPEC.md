# Depth Easy-English Presentation Specification

Status: Phase 7 design artifact only. No depth panel, API field, frontend field, or depth estimate is implemented by this document.

## Plain-English purpose

A future depth result must be understandable without reading model details, radar formulas, or calibration files.

The app should answer four simple questions:

1. Is a depth result available?
2. Is it only a broad comparison, or is it a range in metres?
3. How reliable is the result for this case?
4. What is the main reason for uncertainty or refusal?

The app must not make the result sound like physical confirmation.

## Current gate

```text
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
numerical_depth_model_status = not_fitted
confounder_testing_status = not_run
phase_7_design_status = defined
phase_7_implementation_status = blocked
app_depth_output = not_available
```

The current app must not display a depth category, metre range, depth quality, or confidence percentage.

## UI placement

The future depth presentation should be a separate optional card near the classifier results.

Recommended order:

```text
Classifier Results
Depth Estimate
```

Rules:

- The classifier card remains unchanged when no depth result exists.
- The depth card does not replace or reinterpret the classifier result.
- Old runs without depth files remain fully readable.
- Failure to load depth data must not hide classifier data.
- The depth card may be absent or show `Depth is not available for this run.`
- Detailed private depth artifacts remain outside the normal downloadable UI unless a later local-operator decision approves selected files.

## Required visible fields

A future local depth card may show only the fields needed to explain the result:

```text
Depth result
Depth range or relative category
Quality
Main uncertainty
Method version
```

Optional secondary fields:

```text
Support status
Calibration dataset version
Additional warnings
```

The normal card should not show:

```text
raw feature vectors
raw radar ratios
candidate coordinates
private source references
local file paths
calibration rows
support-distance mathematics
internal model coefficients
```

## Status wording

Allowed internal statuses:

```text
not_available
insufficient_data
relative_only
calibrated_range
validated_range
```

### `not_available`

Meaning:

The approved depth capability is disabled, absent, or has not been validated.

Preferred text:

> Depth is not available for this run.

Optional reason examples:

> The depth method is not enabled.

> No approved local depth model is installed.

> This run was created before depth results were available.

Do not say:

> No underground feature exists.

A missing depth result says nothing about whether a feature exists.

### `insufficient_data`

Meaning:

The depth method was considered, but this case did not meet its data-quality or support requirements.

Preferred text:

> Depth could not be estimated because the available data is not strong enough for this case.

Reason examples:

> The radar coverage was not usable enough.

> This soil type is not sufficiently represented in the calibration data.

> The target size is outside the supported calibration range.

> The terrain or radar viewing angle differs from the calibrated cases.

> Required sensor information is missing.

Do not display empty metre fields as zero.

### `relative_only`

Meaning:

The method can compare this candidate with calibrated examples only in broad terms. It cannot provide metres.

Preferred text:

> This candidate looks shallow compared with the calibrated examples. A depth in metres is not available.

Alternative category text:

> This candidate looks medium-depth compared with the calibrated examples. A depth in metres is not available.

> This candidate looks deep compared with the calibrated examples. A depth in metres is not available.

Required visible label:

```text
Experimental relative result
```

The words `shallow`, `medium-depth`, and `deep` must not appear without the comparison sentence and the no-metres warning.

### `calibrated_range`

Meaning:

A model produced a metre range using calibration data, but the method has not passed the final untouched-site validation gate.

This status should normally remain private to research and must not be presented as an approved normal-app result.

Research-only text:

> Experimental calibrated range: 1.5 to 3 metres. This method has not yet passed final independent-site validation.

The UI must visually distinguish this status from `validated_range`.

### `validated_range`

Meaning:

The frozen method passed its required held-out physical-site validation for the supported conditions.

Preferred text:

> The estimated depth to the top of this candidate is between 1.5 and 3 metres. The estimate quality is medium. The main uncertainty is limited calibration for this soil type.

Required language:

- `estimated`;
- `range` or `between`;
- `depth to the top` when the longer explanation is opened;
- one quality label;
- one main uncertainty reason.

Do not say:

> The candidate is buried at 2.2 metres.

> The object is definitely 2.2 metres deep.

> Satellite data confirmed the depth.

## Quality wording

Allowed quality labels:

```text
low
medium
high
```

Preferred display:

```text
Low quality
Medium quality
High quality
```

Meaning:

- `Low quality`: the case barely meets supported conditions or the predicted interval is wide.
- `Medium quality`: the case is reasonably represented, but meaningful uncertainty remains.
- `High quality`: the case is well represented and validation shows stable performance under similar conditions.

`High quality` must not mean physical confirmation.

The quality label must come from frozen validation rules. The frontend must not calculate quality from display values.

## No invented percentages

The UI must not display a confidence percentage such as `30%`, `70%`, or `95%` unless:

1. the percentage has a precise definition in the frozen method manifest;
2. it was calibrated and validated on held-out physical sites;
3. its wording explains what the percentage means;
4. frontend tests confirm the percentage is not presented as probability that a physical feature exists.

Until those conditions are met, use `low`, `medium`, or `high` quality with a plain-English uncertainty reason.

## Range formatting

Rules for metre ranges:

- show a range, not only one number;
- use the unit `metres` in sentences and `m` in compact fields;
- do not show more decimal places than validation supports;
- use the same rounding rule for minimum, best, and maximum values;
- never round a valid positive interval into an inverted or zero-width range;
- never show negative depth;
- hide `estimated_depth_best_m` in the main sentence unless a later design proves it adds value;
- never display a best estimate without the full range nearby.

Example compact display:

```text
Estimated range: 1.5–3 m
Quality: Medium
Main uncertainty: Limited calibration for this soil type
```

Example expanded explanation:

> This is an estimated depth to the top of the candidate, not a physical measurement. The range is based on cases that were independently documented and processed with the same method.

## Warning priority

When several warnings exist, the card should show one main reason first.

Recommended priority:

1. unsupported condition;
2. missing or weak sensor data;
3. out-of-calibration range;
4. limited subgroup calibration;
5. wide model interval;
6. lower-priority technical warning.

Additional warnings may appear under an expandable `Why?` or `Details` section.

Warnings must be mapped from stable machine-readable codes. The frontend must not invent scientific explanations.

Example mapping:

```text
unsupported_soil_type
→ This soil type is not supported by the current calibration data.

low_valid_pixel_coverage
→ Too little usable sensor data was available for this candidate.

outside_target_size_support
→ This target size is outside the supported calibration range.

wide_prediction_interval
→ The estimated range is wide, so the depth quality is low.
```

## Empty and loading states

### Loading

Preferred text:

> Loading depth result…

Loading must not briefly show zero metres or a default category.

### No depth artifact

Preferred text:

> Depth is not available for this run.

### No candidates

Preferred text:

> No candidate is available for depth review in this run.

### Depth package disabled

Preferred text:

> Depth estimation is turned off.

### Technical read failure

Preferred text:

> The saved depth result could not be read.

A technical read failure must not be changed into `insufficient_data`, because that would hide a software or file problem as a scientific limitation.

## Candidate presentation

When several candidates exist:

- show one row or card per candidate;
- use the existing candidate, object, or cluster identifier;
- sort only by an explicit documented rule;
- do not automatically label the shallowest estimate as the best candidate;
- do not combine separate candidate intervals into one area depth;
- do not display classifier score as depth confidence;
- keep classifier result and depth result in separate columns or sections.

Possible columns:

```text
Candidate
Depth result
Quality
Main uncertainty
Method
```

Metre columns appear only for `calibrated_range` or `validated_range`.

## Area summary rule

A run-level summary may mention depth only when at least one candidate has an approved visible status.

Examples:

### Relative only

> One candidate has an experimental shallow-looking result. A depth in metres is not available.

### Validated range

> The strongest supported candidate has an estimated depth range of 1.5 to 3 metres. The estimate quality is medium.

### Mixed support

> Depth was estimated for one candidate. Two other candidates did not have enough supported data.

### None supported

> Depth could not be estimated for the candidates in this run.

The phrase `strongest supported candidate` must be tied to a documented selection rule. It must not silently mean the highest classifier score.

## Privacy boundary

This is a private local app.

The normal depth card must not expose:

```text
raw coordinates
coordinate proxies
private evidence references
calibration site identifiers
private local paths
raw model features
model files
```

This requirement protects the local workflow. It does not introduce a public-service requirement.

## Accessibility and readability

Required presentation behavior:

- status must not be communicated by colour alone;
- quality must include a text label;
- warnings must be readable without hovering;
- sentences should remain understandable at normal browser zoom;
- tables need clear headers;
- loading and unavailable states need visible text;
- abbreviations such as `OOD`, `MAE`, or `SAR` should not appear in the main explanation;
- method versions may remain compact technical text in a secondary details area.

## Proposed frontend files

Only after implementation gates pass, likely files include:

```text
frontend-v2/src/app/api/depthResults.ts
frontend-v2/src/app/components/DepthResultsPanel.tsx
```

Existing classifier files should not be repurposed as depth files.

The depth panel should consume a stable backend or artifact DTO. It must not calculate the scientific result in TypeScript.

## Planned wording tests

Future tests must verify exact behavior for:

- `not_available`;
- `insufficient_data`;
- shallow relative-only result;
- medium relative-only result;
- deep relative-only result;
- calibrated research range;
- validated range;
- low, medium, and high quality;
- missing uncertainty reason;
- multiple warnings and priority selection;
- no candidate;
- missing depth artifact;
- unreadable depth artifact;
- old run with no depth directory;
- no metre fields for unsupported states;
- no invented percentage;
- no physical-confirmation wording;
- no use of classifier score as depth confidence.

## Implementation gates

Frontend or API implementation may begin only when:

- [ ] Real independently measured or independently documented known-depth records exist.
- [ ] The calibration dataset contract passes.
- [ ] The Phase 3 relative-depth baseline passes untouched-site validation for relative output.
- [ ] The Phase 4 numerical range method passes for metre output.
- [ ] Phase 5 confounder and support checks pass for the displayed conditions.
- [ ] The Phase 6 backend stage and output schemas are implemented and tested.
- [ ] Stable warning codes and quality rules are frozen.
- [ ] Exact visible wording is approved.

## Phase 7 checklist

- [x] Define where the future depth card belongs.
- [x] Keep classifier and depth presentation separate.
- [x] Define wording for every depth status.
- [x] Define relative-only wording with no metre claim.
- [x] Define numerical-range wording with uncertainty.
- [x] Define low, medium, and high quality wording.
- [x] Prohibit invented confidence percentages.
- [x] Define range rounding and formatting rules.
- [x] Define warning priority and code mapping.
- [x] Define loading, missing, and technical-failure states.
- [x] Define multi-candidate and area-summary behavior.
- [x] Define privacy and accessibility rules.
- [x] Define planned frontend files and wording tests.
- [ ] Populate known-depth calibration records.
- [ ] Validate relative-depth output.
- [ ] Validate numerical depth ranges.
- [ ] Complete confounder testing.
- [ ] Implement and test the backend depth stage.
- [ ] Implement the local depth panel.
- [ ] Approve depth display in the normal app.

## Phase 7 decision

```text
Easy-English presentation design: complete
Depth status wording: defined
Quality wording: defined
Warning wording policy: defined
Frontend implementation: blocked
API integration: blocked
App depth panel: not added
Current app depth output: not available
```
