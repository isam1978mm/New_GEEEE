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

1. Create a run from the UI.
   Expected result:
   the UI accepts the submission and returns a visible run ID.

2. Confirm the UI starts polling run status.
   Expected result:
   the UI checks run status every 2 seconds while the run is still `queued` or `running`.

3. Observe terminal state handling.
   Expected result:
   the UI stops polling when the run reaches `done`, `failed`, or `cancelled`.

4. Verify failed-run handling if a run fails.
   Expected result:
   the UI shows a public-safe failed state without stack traces or internal exception content.

5. Verify polling-failure behavior.
   Expected result:
   if polling fails, the UI offers a manual refresh option.

6. Load the public-safe artifact list.
   Expected result:
   the UI renders the real artifact list from the API for the selected run.

7. Test artifact download links.
   Expected result:
   public-safe downloads use the guarded route and resolve correctly.

8. Check artifact filtering.
   Expected result:
   `FILESYSTEM_ONLY` artifacts do not render in the UI at all.

9. Check network-bind protection for `LOCAL_SENSITIVE` downloads when applicable.
   Expected result:
   when `ALLOW_NETWORK_BIND=true`, guarded access to `LOCAL_SENSITIVE` artifacts returns `403`.

10. Verify leak safety.
    Expected result:
    the UI does not expose coordinates, bounds, transforms, local paths, bundle environment variables, internal GRID overrides, or traceback text.

## Completion Rule

The smoke test passes only when the operator can submit a run, follow it to a terminal state, review the real public-safe artifact results, use guarded downloads, and confirm no public-surface leak terms appear in the visible UI or API responses.
