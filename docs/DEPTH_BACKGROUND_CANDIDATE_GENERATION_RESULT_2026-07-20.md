# Depth Background Candidate Generation Result — 2026-07-20

Status: second private candidate generation completed successfully. The first four candidates were visually rejected; visual review of the new eight-candidate set remains pending.

This result records software and workflow status only. It does not approve any candidate as a valid background, create a confirmed no-target record, calculate a signal difference, estimate depth, train a model, import calibration rows, or enable app depth output.

## Software verification

The owner ran the focused and complete unit suites on Windows with Python 3.13.5 for the original four-direction generator.

Observed results:

```text
background candidate tests = 11 passed
C1 redaction-risk tests = 3 passed
full unit suite = 982 passed
failures = 0
warnings = 4 non-blocking
```

After the generator was extended with optional diagonal directions, the owner ran the focused generator suite again:

```text
background candidate tests = 13 passed
failures = 0
warning = pytest cache-write warning only
```

The C1 privacy test and full unit suite have not yet been rerun after the diagonal-mode extension.

## First private generation result

The owner ran the candidate generator first in dry-run mode and then in explicit write mode.

Observed dry-run result:

```text
status = private_background_candidates_dry_run_ready
candidate_count = 4
candidate_directions = north, east, south, west
candidate_width_meters = 50
candidate_height_meters = 50
edge_gap_meters = 100
output_written = false
network_request_made = false
visual_review_required = true
```

Observed write result:

```text
status = private_background_candidates_written
candidate_count = 4
candidate_directions = north, east, south, west
candidate_width_meters = 50
candidate_height_meters = 50
edge_gap_meters = 100
output_written = true
network_request_made = false
visual_review_required = true
comparison_window_only = true
confirmed_no_target_record = false
```

## First visual review result

The first four candidates were displayed over local satellite imagery and rejected:

```text
north = rejected
 east = rejected
south = rejected
 west = rejected
```

Reasons included industrial or treatment infrastructure, buildings or paved areas, roads, residential development, and roundabout or transport surfaces. None was accepted as a reasonable open-ground comparison window.

## Second private generation result

The owner generated a second set using the extended eight-direction mode.

Observed result:

```text
status = private_background_candidates_written
candidate_count = 8
candidate_directions = north, east, south, west, northeast, southeast, southwest, northwest
candidate_width_meters = 50
candidate_height_meters = 50
edge_gap_meters = 300
diagonal_candidates_included = true
output_written = true
network_request_made = false
visual_review_required = true
comparison_window_only = true
confirmed_no_target_record = false
```

Privacy and release flags remained:

```text
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Decision

```text
candidate_generation_software_verified = true
first_private_candidate_set_created = true
first_private_candidate_set_rejected = true
second_private_candidate_set_created = true
second_candidate_count = 8
background_selected = false
background_approved = false
site_background_match_started = false
scientific_signal_validation_run = false
app_depth_enabled = false
```

The 300-metre edge gap is a workflow spacing choice, not a scientific approval threshold.

## Manual review gate

One candidate may be selected only after local visual review confirms, as far as reasonably possible, that it:

1. does not overlap the controlled site;
2. is outside the known construction footprint;
3. has reasonably comparable surface and environmental context;
4. avoids obvious roads, buildings, water, dense vegetation, or unrelated major construction;
5. remains a comparison window rather than an independently confirmed no-target calibration record.

The review must use the local private candidate files. Coordinates and geometry must not be copied into Git.

## Next permitted action

```text
load the eight second-set candidates over local satellite imagery
→ compare them against the site polygon
→ select one candidate or reject all eight
→ only after selection, create the canonical private background file
→ run the no-network site-background matcher dry run
```

## Checklist

- [x] Run original focused candidate-generator tests: 11 passed.
- [x] Run original C1 privacy tests: 3 passed.
- [x] Run original full unit suite: 982 passed.
- [x] Create first four private candidate files.
- [x] Visually review and reject the first four candidates.
- [x] Extend the generator with optional diagonal directions.
- [x] Run extended focused generator tests: 13 passed.
- [x] Create the second eight-candidate private set.
- [ ] Rerun C1 privacy tests after the extension.
- [ ] Rerun the full unit suite after the extension.
- [ ] Visually review the second eight-candidate set.
- [ ] Select one candidate or reject all eight.
- [ ] Run the no-network site-background match dry run.
- [ ] Execute exact acquisition matching only after explicit background review.
