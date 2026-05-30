# UI Smoke Test

## Purpose

This checklist is the final local operator smoke test for the local-first operator UI after parity closeout.

It is a validation checklist, not a claim of fresh-ROI notebook parity.

## Preconditions

- the app is running locally on the intended port
- the operator can open the local UI
- required local configuration is already in place
- the operator is using the accepted production API surface, not internal validation-only hooks
- a completed run exists for download verification

## Startup And Readiness Checks

1. Start the app locally.
2. Verify `/healthz`.
3. Verify `/readyz`.
4. If `/readyz` returns `ee_not_ready`, stop and fix service-account configuration before continuing.
5. Open the homepage on the actual local port.
6. Hard reload the browser with `Ctrl+F5`.

## Manual Operator Checklist

1. Verify the homepage loads the local operator workspace shell.
   Expected result:
   the page shows `Target Input`, `Run lifecycle`, `Status history`, `Full operator output tree`, `Run outputs`, and `Run lookup`.

2. Select a completed run.
   Expected result:
   the run lookup or recent-runs list loads the selected run without exposing local paths, coordinates, or internal-only fields.

3. Verify lifecycle and current status display.
   Expected result:
   the lifecycle panel shows run ID, state, detail, and current stage with readable operator-facing labels.

4. Verify Goal D status history timeline.
   Expected result:
   ordered public-safe status events are visible for the selected run and render as a readable timeline, not raw JSON.

5. Verify stage progress count and stage list.
   Expected result:
   stage progress is visible, ordered, and readable, including empty or historical fallback states where applicable.

6. Verify full operator output tree appears before public `Run outputs`.
   Expected result:
   the full local output tree panel is visible first, followed by the public-safe artifact list.

7. Expand or inspect output rows.
   Expected result:
   operator output rows show grouped files, filenames, relative paths, sizes, and guarded download links where implemented.

8. Download representative artifacts from the operator output tree:
   - `DEM_GEO8_TIFS/DEM_640.tif`
   - `QA/RUN_MANIFEST.json`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
   - `QA/sar/intermediates/post_rtc/final_VV_dB.npy`
   Expected result:
   each download resolves through the guarded route and returns the real artifact filename.

9. Verify unavailable or not-implemented outputs show safe unavailable behavior.
   Expected result:
   not-implemented outputs appear under the not-implemented section, and unavailable downloads do not expose internal details.

10. Verify recent runs and explicit run lookup.
   Expected result:
   recent runs load, a pasted run ID loads the requested run, and active runs resume polling.

11. Verify failed, empty, and loading states if available.
   Expected result:
   loading, failed, historical, and no-history states remain operator-readable and do not show raw exceptions.

12. Verify sensitive files are not exposed or downloadable:
   - `.env`
   - credentials
   - local path maps
   - DB files
   - logs
   - service-account-like files
   Expected result:
   the UI and guarded routes do not expose these files or leak internal path/config values.

## Completion Rule

The smoke test passes only when the operator can load a completed run, verify lifecycle and Goal D status history timeline behavior, inspect the full operator output tree before public outputs, download representative guarded artifacts, and confirm no sensitive files or internal-only values are exposed.
