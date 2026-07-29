# Operator-calibrated local depth mode

Date: 2026-07-29

## What this mode does

This mode returns a **real local depth range in metres** by interpolating between two or more measured local anchors.

It is designed to ship a practical depth feature without waiting for a global public calibration dataset.

Example output:

```text
Local provisional depth range: 0.80–1.20 m
Best local estimate: 1.00 m
Quality: provisional local
```

## What this mode does not do

It is not a global model.

It does not estimate depth without local measurements.

It does not extrapolate beyond the shallowest and deepest measured anchors.

It does not use classifier output, PCA anomaly, target masks, or a misleading depth-named feature.

## What the operator must provide

At least two measured local anchors from the same AOI or a genuinely comparable local area.

Each anchor needs:

```text
anchor ID
one consistently calculated local signal value
measured minimum depth
measured best depth
measured maximum depth
```

Every anchor and candidate must use the same signal formula, units, processing period, orbit rules, surface controls, and spatial-reduction method.

The current implementation does **not yet calculate the candidate signal automatically**. The operator supplies the reviewed signal value and its uncertainty.

## Safety rules built into the code

The package is rejected unless:

- it contains at least two anchors;
- anchor IDs are unique;
- signal values are unique;
- measured best depths change strictly and monotonically with the signal;
- every depth range is finite and nonnegative;
- package checksums pass.

A candidate receives no metre output when:

- the signal name does not match;
- the signal or uncertainty is invalid;
- the candidate lies outside the anchor signal range;
- its uncertainty interval extends beyond anchor support;
- run quality is blocked;
- the candidate schema and package type do not match.

## Files added

```text
app/pipeline/depth/interpolation.py
app/pipeline/depth/loader.py
scripts/build_operator_local_depth_package.py
scripts/run_operator_local_depth_for_existing_run.py
```

Editable examples:

```text
docs/examples/operator_depth_config.example.json
docs/examples/operator_depth_candidates.example.json
```

## Step 1 — Prepare the calibration config

Copy the example:

```powershell
cd C:\Dev\New_GEE
Copy-Item docs\examples\operator_depth_config.example.json C:\PrivateDepth\my-aoi-config.json
```

Edit the copied file and replace every example anchor with your measured local anchors.

Important:

```text
signal_name must describe the exact calculation
signal_units must be correct
anchor signal values and candidate signal values must use the same method
validation_status should remain provisional unless independent validation exists
```

## Step 2 — Build the private package

```powershell
python scripts\build_operator_local_depth_package.py `
  --config C:\PrivateDepth\my-aoi-config.json `
  --output-dir C:\PrivateDepth\my-aoi-package
```

The command creates:

```text
depth_method_manifest.json
checksums.sha256
candidate_input_template.json
```

It validates the package before reporting success.

## Step 3 — Prepare candidate input

Copy the generated template or the repository example:

```powershell
Copy-Item C:\PrivateDepth\my-aoi-package\candidate_input_template.json `
  C:\PrivateDepth\my-candidates.json
```

For each candidate, provide:

```json
{
  "candidate_id": "candidate-001",
  "signal_name": "local_vv_minus_vh_db",
  "signal_value": 2.0,
  "signal_uncertainty": 0.1
}
```

`signal_uncertainty` widens the returned metre range. It must use the same units as `signal_value`.

## Step 4 — Run it on an existing completed app run

The run must already contain a usable run-quality result.

```powershell
python scripts\run_operator_local_depth_for_existing_run.py `
  --run-dir C:\Dev\New_GEE\data\runs\<RUN_ID> `
  --package-dir C:\PrivateDepth\my-aoi-package `
  --candidate-input C:\PrivateDepth\my-candidates.json
```

To intentionally replace existing reviewed candidate input:

```powershell
python scripts\run_operator_local_depth_for_existing_run.py `
  --run-dir C:\Dev\New_GEE\data\runs\<RUN_ID> `
  --package-dir C:\PrivateDepth\my-aoi-package `
  --candidate-input C:\PrivateDepth\my-candidates.json `
  --force
```

## Private outputs

```text
depth/depth_estimates.csv
depth/depth_summary.json
depth/depth_method_manifest.json
```

The artifacts remain filesystem-only and are not exposed through HTTP.

## Optional normal-pipeline activation

The existing pipeline registration is reused:

```text
LOCAL_DEPTH_MODE=local_calibrated
LOCAL_DEPTH_PACKAGE_DIR=C:\PrivateDepth\my-aoi-package
```

The candidate input must exist in the run before the depth stage executes:

```text
depth_inputs/candidates.json
```

Default mode remains:

```text
LOCAL_DEPTH_MODE=off
```

## How the interpolation works

For a candidate between two anchors:

```text
weight = (candidate signal - shallow signal) / (deep signal - shallow signal)
```

The code linearly interpolates the measured minimum, best, and maximum depth values.

It also evaluates the candidate signal uncertainty interval. The lowest supported minimum and highest supported maximum become the final reported range.

The code never extends the line beyond the measured signal range.

## Labels that always remain attached

```text
operator_calibrated_local_interpolation
local_calibration_only
not_transferable
not_global_model
no_extrapolation
```

## Current status

```text
known-zone lookup = supported
operator local interpolation = implemented in PR #52
automatic signal extraction = not implemented yet
global numerical depth = not ready
unknown-AOI depth without local anchors = not supported
```

## Next implementation slice

Add a reviewed signal-extraction command that computes one approved neutral feature for anchors and candidates using exactly the same source, orbit, dates, grid, and reduction rules. That will remove manual signal entry while keeping the local-anchor requirement and no-extrapolation boundary.
