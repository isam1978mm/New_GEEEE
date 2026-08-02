# Option 5 — Existing-Run Surface-Change Execution

Date: 2026-08-01

## Purpose

This slice makes the merged dual-window radar surface-change stage usable for an already completed app run.

It does not rerun the full pipeline and does not touch the deferred operator depth-calibration panel.

## Blocking integration defect fixed

The frontend requests:

```text
/runs/<run_id>/artifacts/option5_surface_change_summary/download/option5_surface_change_summary.json
```

The artifact download allowlist previously had no filename mapping for `option5_surface_change_summary`. A successfully produced summary could therefore be rejected by the download route and appear unavailable in the UI.

The safe public mapping is now:

```text
option5_surface_change_summary -> option5_surface_change_summary.json
```

## Existing-run command

From the repository root:

```powershell
$env:EE_REAL_EXECUTION_ENABLED = "true"
$env:OPTION5_SURFACE_CHANGE_ENABLED = "true"
python scripts/run_surface_change_for_existing_run.py --run-id <RUN_ID>
```

Use `--force` only when intentionally replacing an existing `surface_change` stage result:

```powershell
python scripts/run_surface_change_for_existing_run.py --run-id <RUN_ID> --force
```

## What the command does

The command:

1. confirms the run exists in the app database;
2. refuses to operate while the run is queued or running;
3. reuses the completed run's existing grid, DEM, after-window SAR result and pair diagnostics;
4. fetches only the immediately preceding same-duration Sentinel-1 window;
5. applies the existing orbit, pair-support, grid, incidence and valid-pixel gates;
6. writes the normal Option 5 surface-change artifacts;
7. upserts those artifacts into the app database;
8. writes the standard `stage_surface_change.manifest.json` stage record;
9. preserves the completed run's existing status.

The normal results panel can then load:

```text
option5_surface_change_summary.json
```

without creating a new full run.

## Output boundary

The result remains:

- radar-backscatter surface-change review only;
- not measured displacement;
- not settlement;
- not elevation change;
- not physical confirmation;
- not numerical depth.

The stage may return `not_available` when the scientific compatibility gates are not met. That is an expected abstention, not a pipeline failure.

## Safety and scope controls

This slice:

- does not expose coordinates or private filesystem paths;
- does not make local-sensitive rasters HTTP-served;
- does not create a depth calibration row;
- does not start depth-model training;
- does not modify the operator local-depth panel;
- does not restart the broad Option 1 candidate search;
- does not change a completed run to `running`, `failed` or `done` again.

## Required validation

Before merge:

- focused existing-run execution tests;
- public artifact filename contract test;
- full unit and integration suite;
- forbidden `ee.Authenticate` guard;
- direct-file-streaming guard;
- notebook safety guard;
- production frontend validation workflow.
