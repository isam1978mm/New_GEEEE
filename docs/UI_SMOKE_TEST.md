# UI Smoke Test

## Purpose

This checklist is the final local operator smoke test for the UI workflow after implementation work lands.

It is a validation checklist, not a claim of fresh-ROI notebook parity.

## Preconditions

- the app is running locally on the intended port, currently `8007`
- the operator can open the local UI
- required local configuration is already in place
- the operator is using the accepted production API surface, not internal validation-only hooks

## Restart And Readiness Checks

- after changing `.env` or application code, restart the FastAPI server before testing
- after restarting the server, hard reload the browser with `Ctrl+F5`
- open the UI on the actual running port, currently `http://127.0.0.1:8007`
- check `http://127.0.0.1:8007/readyz` before creating a run
- if `/readyz` returns `ee_not_ready`, stop and fix Earth Engine configuration before creating a run
- verify `EE_SERVICE_ACCOUNT_KEY_PATH` points to an existing service-account JSON file
- ensure each `.env` setting is on its own line; do not join multiple settings on one line
- be aware that the DEM stage can fail almost immediately if Earth Engine is not ready
- failed runs can still appear in history, but they will not produce downloadable outputs

## Smoke Test Steps

1. Enter the target point and create a run from the UI.
   Expected result:
   the UI requires valid latitude and longitude values before enabling the queue button, accepts the submission, and returns a visible run ID.

   Operator note:
   if `/readyz` is not healthy first, do not queue the run. Fix readiness, restart the server, and hard reload the browser before trying again.

2. Confirm the UI starts polling run status and progress.
   Expected result:
   the UI checks run status every 2 seconds while the run is still `queued` or `running`, shows the current public-safe stage, renders the stage checklist, and shows a `Status history` timeline with the latest safe run event.

3. Observe terminal state handling.
   Expected result:
   the UI stops polling when the run reaches `done`, `failed`, or `cancelled`, while keeping the final stage checklist visible.

4. Verify failed-run handling if a run fails.
   Expected result:
   the UI shows a public-safe failed state without stack traces or internal exception content.

   Operator note:
   if the run fails during `DEM`, check `/readyz` and Earth Engine service-account configuration before assuming there is a pipeline bug.

5. Verify polling-failure behavior.
   Expected result:
   if polling fails, the UI offers a manual refresh option.

6. Refresh or inspect recent-run history.
   Expected result:
   the UI lists recent public-safe runs from the API without exposing internal run data.

7. Use explicit run lookup.
   Expected result:
   entering a run ID loads that run, updates the lifecycle panel, and resumes polling if the run is still active.

8. Select a run from history.
   Expected result:
   the selected run shows its run ID, status, public-safe stage progress, status history, terminal state, and artifacts when available.

9. Load the public-safe artifact list.
   Expected result:
   the UI renders the real artifact list from the API for the selected run.

   Operator note:
   failed runs are expected to show no downloadable outputs.

10. Test artifact download links.
   Expected result:
   public-safe downloads use the guarded route and resolve correctly.

11. Check artifact filtering.
   Expected result:
   `FILESYSTEM_ONLY` artifacts do not render in the UI at all.

12. Check network-bind protection for `LOCAL_SENSITIVE` downloads when applicable.
   Expected result:
   when `ALLOW_NETWORK_BIND=true`, guarded access to `LOCAL_SENSITIVE` artifacts returns `403`.

13. Verify leak safety.
    Expected result:
    the UI does not expose coordinates, bounds, transforms, local paths, bundle environment variables, internal GRID overrides, or traceback text.

## Completion Rule

The smoke test passes only when the operator can submit a run, follow it to a terminal state, review the real public-safe artifact results, use guarded downloads, and confirm no public-surface leak terms appear in the visible UI or API responses.
