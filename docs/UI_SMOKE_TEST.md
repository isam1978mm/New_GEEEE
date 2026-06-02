# UI Smoke Test

## Purpose

This checklist is the final local operator smoke test for the local-first React operator UI after parity closeout and Phase 9E-D cutover.

It is a validation checklist, not a claim of fresh-ROI notebook parity.

## Preconditions

- the app is running locally on the intended port
- the operator can open the local UI
- required local configuration is already in place
- the operator is using the accepted production API surface, not internal validation-only hooks
- a completed run exists for download verification
- a disposable terminal run exists if delete flow will be tested

## Startup And Readiness Checks

1. Start the app locally.
2. Verify `/healthz`.
3. Verify `/readyz`.
4. If `/readyz` returns `ee_not_ready`, stop and fix service-account configuration before continuing.
5. Open the homepage on the actual local port.
6. Hard reload the browser with `Ctrl+F5`.

## Manual Operator Checklist

1. Verify the homepage loads the React operator dashboard.
   Expected result:
   the page shows `Target Input`, `Run Dashboard`, `Run lookup`, `Recent Runs`, `Run Archive`, `Overview`, `Exports`, `Status History`, and `Diagnostics`.

2. Verify the queue form fields.
   Expected result:
   the queue form shows `Latitude`, `Longitude`, and `Run name`, and the `Queue Run` action remains disabled until latitude and longitude are valid.

3. Verify external tile preview OFF behavior.
   Expected result:
   the target preview shows `Map preview disabled`, and no external tile preview is claimed while tiles are disabled.

4. Verify external tile preview ON behavior.
   Expected result:
   when enabled in `Settings` and valid coordinates are entered, the target preview shows a visible 3x3 tile grid with a target marker, or a clear tile-load error if the template/provider fails.

5. Queue a run and verify active-run updates.
   Expected result:
   the run is queued successfully and live progress updates without needing to click `Open` again.

6. Select a completed run.
   Expected result:
   the run lookup or recent-runs list loads the selected run without exposing local paths, coordinates, or internal-only fields.

7. Verify the tabbed dashboard layout.
   Expected result:
   the selected-run area is organized into `Overview`, `Exports`, `Status History`, and `Diagnostics` tabs; the default `Overview` tab is compact and does not read like one long report.

8. Verify lifecycle and current status display on the Overview tab.
   Expected result:
   the lifecycle panel shows run ID, state, detail, and current stage with readable operator-facing labels.

9. Verify Recent Runs and Run Archive.
   Expected result:
   `Recent Runs` shows the latest three loaded runs when available; `Run Archive` expands to older runs from the current API response and its client-side search/filter narrows the loaded archive list. If the API only returns a limited recent-run set, record that limitation.

10. Verify compact stage status pills.
   Expected result:
   stage progress is visible, ordered, and readable as compact status pills with short labels; at normal laptop width it wraps to no more than two rows.

11. Verify public `Run outputs` and `Key Downloads` on the Overview tab.
   Expected result:
   public-safe `Run outputs` and `Key Downloads` are visible near the top of the selected-run dashboard before the deep export browser.

12. Verify Goal D status history timeline.
   Expected result:
   the Overview tab shows only a compact latest-event summary, while the `Status History` tab contains the full ordered public-safe timeline and renders as readable events, not raw JSON.

13. Verify Status History default expansion behavior.
   Expected result:
   status history is collapsed by default for `done` and `cancelled` runs, and auto-expanded for `running`, `failed`, or `stale_failed` runs when such a run is available.

14. Verify grouped Exports browser density.
   Expected result:
   the `Exports` tab contains the grouped output browser; output families are collapsed by default, group headers show family names and counts, files sort deterministically inside groups, and the full tree is no longer one giant vertical card list.

15. Expand and collapse export groups.
   Expected result:
   individual groups expand into compact tables, and the `Expand all` / `Collapse all` controls work without changing download URLs.

16. Verify export search/filter behavior.
    Expected result:
    filtering by folder, filename, or path narrows visible grouped outputs without changing the total output count badge or creating unavailable links.

17. Verify Advanced / unavailable outputs.
    Expected result:
    unavailable or not-implemented outputs are secondary and collapsed under `Advanced / unavailable outputs`; legacy notebook-only SAR pre-RTC intermediates do not appear as operator deliverables, and detailed reason text is visible only when expanded.

18. Download representative artifacts from `Run outputs`, `Key Downloads`, or the `Exports` tab:
   - `DEM_GEO8_TIFS/DEM_640.tif`
   - `QA/RUN_MANIFEST.json`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
   - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
   - `QA/sar/intermediates/post_rtc/final_VV_dB.npy`
   Expected result:
   each download resolves through the guarded route and returns the real artifact filename.

19. Verify unavailable or not-implemented outputs show safe unavailable behavior.
   Expected result:
   not-implemented outputs appear in a secondary collapsed section, and unavailable downloads do not expose internal details.

20. Verify real diagnostics only.
   Expected result:
   the `Diagnostics` tab shows only source-backed QA availability, accepted documented exceptions, or a clear empty state; it does not show fake PCA/cloud metrics or invented failure causes.

21. Verify recent runs and explicit run lookup.
   Expected result:
   recent runs load, a pasted run ID loads the requested run, and active runs resume polling.

22. Verify Run Archive search/filter/sort and Storage Health.
   Expected result:
   archive search, status filter, and sort controls work; `Storage Health` appears with totals and recommendation lists; active runs are not suggested for deletion.

23. Verify safe run deletion.
   Expected result:
   completed or failed runs show a delete option in the Run Archive; active runs show `Cannot delete active run`; confirmation requires typing the run name or run ID; deleting a disposable test run removes it from the archive without showing local paths.

24. Verify deletion audit / freed-space summary.
   Expected result:
   the delete flow reports freed space, and the deleted-runs summary updates without exposing local paths.

25. Verify Settings.
   Expected result:
   `Settings` opens as a real local-operator panel, `External map tiles` is OFF by default, `Privacy warning` is clear, `Tile URL template` is editable only when tiles are enabled, `Status polling interval` is shown as read-only, and `Show advanced / unavailable outputs` changes the default expansion behavior of the Exports view after refresh.

26. Verify external-tile privacy behavior.
   Expected result:
   while external tiles are disabled, no external map request is made; if the operator enables them, the UI makes clear that external tile providers may receive browser map viewport requests, and the setting persists after refresh.

27. Verify failed, empty, and loading states if available.
   Expected result:
   loading, failed, historical, and no-history states remain operator-readable and do not show raw exceptions.

28. Verify sensitive files are not exposed or downloadable:
   - `.env`
   - credentials
   - local path maps
   - DB files
   - logs
   - service-account-like files
   Expected result:
   the UI and guarded routes do not expose these files or leak internal path/config values.

29. Verify internal debug/runtime files are not shown as operator deliverables:
   - `grid_manifest.json`
   - `run_status_history.json`
   - `stage_*.manifest.json`
   - `npy_radar_bands/*.npy`
   - `stacks/tensor_support/*`
   - `full_job/field_ops/*`
   - `kmz/*`
   - `objects/object_mask.npy`
   - `objects/object_patches/*.npy`
   Expected result:
   these internal or exact-context artifacts do not appear in the operator output browser even if they exist on disk.

30. If browser automation is unavailable, record that literal browser `Ctrl+F5` and click-through remains operator-required.
    Expected result:
    the smoke record explicitly distinguishes automated HTTP/static checks from manual browser visual checks.

## Completion Rule

The smoke test passes only when the operator can load a completed run, verify the compact tabbed dashboard, verify lifecycle and Goal D status history behavior, inspect grouped exports without a giant single-page artifact list, download representative guarded artifacts, and confirm no sensitive files or internal-only values are exposed.
