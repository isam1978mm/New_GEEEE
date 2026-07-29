# Local Numerical Depth MVP — Operator Guide

## Current capability

This first feasible depth version can write real metre ranges for reviewed local zones that already have measured depth records.

For the Tyrone beta package:

| Local zone | Minimum | Best | Maximum |
|---|---:|---:|---:|
| `tyrone_tp5` | 0.65532 m | 0.68072 m | 0.70612 m |
| `tyrone_tp6` | 0.85090 m | 0.94996 m | 1.04902 m |

The result is labelled:

```text
calibrated_range
provisional_local
local_calibration_only
not_transferable
not_global_model
```

## Important limitation

This version does **not yet estimate the depth of a new unknown AOI from radar**.

It does three useful things first:

1. places the measured Tyrone depth ranges inside the app's real depth-output format;
2. verifies run quality before writing metre values;
3. proves that private numerical depth can be added without changing Option 5 or exposing private files.

The next scientific step is to connect reviewed radar features to these anchors so a new candidate can be interpolated inside local support.

## Recommended first-use method

Use the post-run command on an already completed app run. This avoids timing problems with the normal background pipeline.

The normal run directory is:

```text
<data_dir>\runs\<run_id>
```

With the default settings, that is usually:

```text
C:\Dev\New_GEE\data\runs\<run_id>
```

Adjust the path if your repository or `DATA_DIR` is different.

## Step 1 — Build the private Tyrone package

From the repository root in PowerShell:

```powershell
python scripts\build_tyrone_local_depth_package.py `
  --output-dir C:\Dev\New_GEE\private\tyrone-local-depth
```

Generated private files:

```text
depth_method_manifest.json
checksums.sha256
depth_candidates.template.json
```

The directory should remain outside Git.

## Step 2 — Prepare reviewed candidate mappings

Copy:

```text
C:\Dev\New_GEE\private\tyrone-local-depth\depth_candidates.template.json
```

to a separate private working file, for example:

```text
C:\Dev\New_GEE\private\tyrone-reviewed-candidates.json
```

Replace the placeholder candidate IDs with local operator labels. Keep the approved zone IDs unchanged:

```json
{
  "schema_version": "local_depth_candidates_v1",
  "candidates": [
    {
      "candidate_id": "reviewed-local-plot-5",
      "zone_id": "tyrone_tp5"
    },
    {
      "candidate_id": "reviewed-local-plot-6",
      "zone_id": "tyrone_tp6"
    }
  ]
}
```

Do not assign an unknown location to either Tyrone zone merely to obtain a number.

## Step 3 — Run local depth on a completed run

```powershell
python scripts\run_local_depth_for_existing_run.py `
  --run-dir C:\Dev\New_GEE\data\runs\<run_id> `
  --package-dir C:\Dev\New_GEE\private\tyrone-local-depth `
  --candidate-input C:\Dev\New_GEE\private\tyrone-reviewed-candidates.json
```

The command does not call Earth Engine and does not rerun the classifier.

## Outputs

The completed run receives private local files:

```text
depth\depth_estimates.csv
depth\depth_summary.json
depth\depth_method_manifest.json
depth_inputs\candidates.json
```

These depth artifacts are filesystem-only and are not exposed through the public artifact API.

## Expected successful summary

```text
status = calibrated_range
candidate_count = 2
estimated_count = 2
run_quality_status = PASS
```

A blocked or unusable run returns `insufficient_data` and leaves all metre fields empty.

## Re-running after candidate review

The command protects an existing reviewed candidate file. To intentionally replace it:

```powershell
python scripts\run_local_depth_for_existing_run.py `
  --run-dir C:\Dev\New_GEE\data\runs\<run_id> `
  --package-dir C:\Dev\New_GEE\private\tyrone-local-depth `
  --candidate-input C:\Dev\New_GEE\private\tyrone-reviewed-candidates.json `
  --force
```

## Normal pipeline activation

The code supports conditional registration with:

```text
LOCAL_DEPTH_MODE=local_calibrated
LOCAL_DEPTH_PACKAGE_DIR=<private package directory>
```

Do not use this as the primary workflow yet. A normal background run does not currently create the reviewed `depth_inputs/candidates.json` mapping before the depth stage. The post-run command is the complete usable path for this MVP.

## Next implementation step

Add a local feature-calibration layer that:

1. measures an approved radar feature for the two Tyrone anchors;
2. freezes the feature definition and observation period;
3. accepts a new candidate only inside the same local support conditions;
4. interpolates a provisional metre range between the anchors;
5. abstains outside the anchor range or when uncertainty is too wide.

Until that layer passes a local test, the current MVP must not be described as automatic radar depth estimation.
