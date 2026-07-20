# Depth Background Candidate Generation Result — 2026-07-20

Status: private candidate generation completed successfully. Visual review and candidate selection remain pending.

This result records software and workflow status only. It does not approve any candidate as a valid background, create a confirmed no-target record, calculate a signal difference, estimate depth, train a model, import calibration rows, or enable app depth output.

## Software verification

The owner ran the focused and complete unit suites on Windows with Python 3.13.5.

Observed results:

```text
background candidate tests = 11 passed
C1 redaction-risk tests = 3 passed
full unit suite = 982 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write warning.

## Private generation result

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
private_candidate_files_created = true
candidate_count = 4
background_selected = false
background_approved = false
site_background_match_started = false
scientific_signal_validation_run = false
app_depth_enabled = false
```

The four generated rectangles are screening candidates only. Their 100-metre edge gap is a workflow spacing choice, not a scientific approval threshold.

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
open the private site polygon and all four candidates in a local map viewer
→ compare north, east, south, and west candidates against imagery
→ choose one candidate or reject all four
→ record only the selected direction in repository documentation
→ run the no-network site-background matcher dry run
```

If all four candidates are unsuitable, generate a new set using a different explicit edge gap rather than approving a poor background.

## Checklist

- [x] Run focused candidate-generator tests: 11 passed.
- [x] Run C1 privacy tests: 3 passed.
- [x] Run full unit suite: 982 passed.
- [x] Run private dry generation check.
- [x] Create four private candidate files.
- [x] Preserve aggregate-only console output.
- [ ] Visually review all four private candidates.
- [ ] Select one candidate or reject all four.
- [ ] Run the no-network site-background match dry run.
- [ ] Execute exact acquisition matching only after explicit background review.
