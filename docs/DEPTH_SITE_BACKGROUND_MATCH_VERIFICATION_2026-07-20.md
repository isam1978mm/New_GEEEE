# Depth Site–Background Matcher Verification — 2026-07-20

Status: software verification passed on `main`. Private background selection and execution remain active work.

## Owner verification

The owner ran the focused matcher tests, the C1 privacy tests, and the complete unit suite on Windows with Python 3.13.5.

Observed results:

```text
site-background matcher tests = 9 passed
C1 redaction-risk tests = 3 passed
full unit suite = 971 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write access warning. They did not affect the passing result.

## Verified behavior

The passing tests confirm that the matcher:

- rejects repository-local geometry and output paths;
- rejects identical site and background geometries;
- rejects invalid clean analysis windows;
- makes no network request during dry run;
- requires explicit background-review confirmation before execution;
- matches exact Sentinel-1 image identities separately for clean pre and clean post periods;
- counts unmatched images without printing identities;
- refuses readiness when exact clean-post support is absent;
- rejects duplicate image identities;
- keeps the matched-image manifest private and outside Git;
- prints no coordinates, geometry, private paths, or image identities.

## Current decision

```text
site_background_matcher_software_ready = true
private_background_polygon_selected = false
private_background_visual_review_complete = false
exact_site_background_match_executed = false
scientific_signal_validation_run = false
depth_model_training_started = false
app_depth_enabled = false
```

The next work is to generate several non-overlapping private background candidates around the reviewed site footprint, visually screen them, and select one comparison polygon. A selected background remains a comparison window, not an independently confirmed no-target calibration record.

## Checklist

- [x] Fix the identical-geometry test setup.
- [x] Pass all 9 focused matcher tests.
- [x] Pass all 3 C1 privacy tests.
- [x] Pass all 971 unit tests.
- [x] Keep the privacy allowlist unchanged.
- [ ] Generate private background candidates.
- [ ] Visually review candidate surface and construction context.
- [ ] Select one non-overlapping background polygon.
- [ ] Run the no-network match dry run.
- [ ] Execute exact acquisition matching.
- [ ] Freeze the matched image manifest privately.
