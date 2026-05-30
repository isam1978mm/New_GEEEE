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
   the page shows `Target Input`, `Run lifecycle`, `Status history`, `Output Browser`, `Key Downloads`, `Run outputs`, and `Run lookup`.

2. Select a completed run.
   Expected result:
   the run lookup or recent-runs list loads the selected run without exposing local paths, coordinates, or internal-only fields.

3. Verify lifecycle and current status display.
   Expected result:
   the lifecycle panel shows run ID, state, detail, and current stage with readable operator-facing labels.

4. Verify Goal D status history timeline.
   Expected result:
   ordered public-safe status events are visible for the selected run and render as a readable timeline, not raw JSON.

5. Verify stage progress count and compact stage checklist.
   Expected result:
   stage progress is visible, ordered, and readable as compact status pills, including empty or historical fallback states where applicable.

6. Verify full operator output browser appears before public `Run outputs`.
   Expected result:
   the grouped output browser is visible first, followed by the public-safe artifact list.

7. Verify key downloads are visible near the top of the output browser.
   Expected result:
   high-value artifacts such as `QA/RUN_MANIFEST.json`, `DEM_GEO8_TIFS/DEM_640.tif`, FINAL_TESLA files, REPORT_640 files, and the post-RTC sample entry appear when implemented, without fake links for unavailable files.

8. Verify grouped output browser density.
   Expected result:
   output families are collapsed by default, group headers show family names and counts, files sort deterministically inside groups, and the full tree is no longer one giant vertical card list.

9. Expand and collapse output groups.
   Expected result:
   individual groups expand into compact tables, and the `Expand all` / `Collapse all` controls work without changing download URLs.

10. Verify output search/filter behavior.
    Expected result:
    filtering by folder, filename, or path narrows visible grouped outputs without changing the total output count badge or creating unavailable links.

11. Download representative artifacts from the operator output browser:
   - `DEM_GEO8_TIFS/DEM_640.tif`
   - `QA/RUN_MANIFEST.json`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
   - `QA/sar/intermediates/post_rtc/final_VV_dB.npy`
   Expected result:
   each download resolves through the guarded route and returns the real artifact filename.

12. Verify unavailable or not-implemented outputs show safe unavailable behavior.
   Expected result:
   not-implemented outputs appear in a secondary collapsed section, and unavailable downloads do not expose internal details.

13. Verify recent runs and explicit run lookup.
   Expected result:
   recent runs load, a pasted run ID loads the requested run, and active runs resume polling.

14. Verify failed, empty, and loading states if available.
   Expected result:
   loading, failed, historical, and no-history states remain operator-readable and do not show raw exceptions.

15. Verify sensitive files are not exposed or downloadable:
   - `.env`
   - credentials
   - local path maps
   - DB files
   - logs
   - service-account-like files
   Expected result:
   the UI and guarded routes do not expose these files or leak internal path/config values.

16. If browser automation is unavailable, record that literal browser `Ctrl+F5` and click-through remains operator-required.
    Expected result:
    the smoke record explicitly distinguishes automated HTTP/static checks from manual browser visual checks.

## Completion Rule

The smoke test passes only when the operator can load a completed run, verify lifecycle and Goal D status history timeline behavior, inspect the compact grouped output browser before public outputs, download representative guarded artifacts, and confirm no sensitive files or internal-only values are exposed.
