# UI Smoke Test

## Purpose

This checklist is the final local operator smoke test for the UI workflow after implementation work lands.

It is a validation checklist, not a claim of fresh-ROI notebook parity.

## Preconditions

- the app is running locally
- the operator can open the local UI
- required local configuration is already in place
- the operator is using the accepted production API surface, not internal validation-only hooks

## Smoke Test Steps

1. Enter the target point and create a run from the UI.
   Expected result:
   the UI requires valid latitude and longitude values before enabling the queue button, accepts the submission, and returns a visible run ID.

2. Confirm the UI starts polling run status and progress.
   Expected result:
   the UI checks run status every 2 seconds while the run is still `queued` or `running`, shows the current public-safe stage, and renders the stage checklist.

3. Observe terminal state handling.
   Expected result:
   the UI stops polling when the run reaches `done`, `failed`, or `cancelled`, while keeping the final stage checklist visible.

4. Verify failed-run handling if a run fails.
   Expected result:
   the UI shows a public-safe failed state without stack traces or internal exception content.

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
   the selected run shows its run ID, status, public-safe stage progress, terminal state, and artifacts when available.

9. Load the public-safe artifact list.
   Expected result:
   the UI renders the real artifact list from the API for the selected run.

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
