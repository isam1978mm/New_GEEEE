# UI Finalization Plan

## Purpose

This document defines the smallest practical set of UI implementation goals needed to finish the operator workflow before any VPS-oriented packaging or deployment work.

The intent is to finish the public-safe operator flow without reopening backend parity, GRID, or notebook-science decisions that are already settled.

## Current UI Status

The current UI can already do a few important things:

- stage a point and submit a run
- show immediate queue feedback
- show a visible artifact area
- exclude filesystem-only and experimental outputs from the visible artifact list

The current UI does not yet prove the complete operator workflow. It does not yet prove:

- full run status polling
- real artifact loading from the API
- guarded download flow end to end
- recent-run history or run lookup
- a full local run-validation workflow from submit to completed review

## Final UI Target Before VPS

Before any VPS-focused work, the UI should support this operator-safe workflow:

- create a run from the UI
- show the run ID after submission
- poll run status from the public API
- show clear done and failed states
- show only redacted or otherwise public-safe error messages
- list real public-safe artifacts from the API
- provide guarded download links for public-safe artifacts
- allow recent-run history or explicit run lookup
- avoid leaks of coordinates, bounds, transforms, local paths, bundle environment variables, stack traces, or internal GRID override controls

This target is about operator usability and public-surface correctness. It is not a claim of fresh-ROI notebook parity or a change in production science behavior.

## Implementation Phases

### Phase 1: Run Lifecycle UI

Scope:

- map the current run-create and run-detail DTOs to the UI
- queue a run from the existing submission flow
- display the returned run ID
- poll `/runs/{run_id}` every 2 seconds while the run is `queued` or `running`
- stop polling on terminal `done`, `failed`, or `cancelled` state
- show a manual refresh option if polling fails
- show queued, running, done, and failed states safely
- ensure background pipeline stage failures cleanly mark the run as failed in the database
- ensure `/runs/{run_id}` exposes a public-safe failed state
- verify the current `RuntimeError` pattern `Caught handled exception, but response already started` does not break the response chain for run lifecycle status
- add tests for run lifecycle rendering and safe error handling
- Investigate whether stage failures already mark the run as failed in the DB. If not, fix the orchestrator to do so before adding UI rendering.
- If failed runs can remain stuck in running, verify existing stale-run-on-startup cleanup handles them or add a follow-up note if it does not.

Acceptance criteria:

- a submitted run shows its run ID in the UI
- the UI polls every 2 seconds until the run reaches a terminal state
- terminal states are rendered clearly without stack traces or internal exception details
- if polling fails, the operator can trigger a manual refresh without reloading the full page
- handled background stage failures are visible as a stable public-safe failed state
- the response chain remains valid even when background execution fails after the initial run-create response
- failure messaging remains redacted and public-safe
- tests cover lifecycle transitions and public-safe failure output

### Phase 2: Artifacts and Results UI

Scope:

- fetch the real artifact list for a live run from the API
- render the artifact list from live data instead of sample placeholders
- provide guarded download links for public-safe artifacts
- ensure `LOCAL_SENSITIVE` artifacts use only the guarded download route
- verify `LOCAL_SENSITIVE` downloads return `403` when `ALLOW_NETWORK_BIND=true`
- ensure `FILESYSTEM_ONLY` artifacts never render in the UI at all, not even as hidden DOM content
- show empty, missing, and not-yet-ready artifact states cleanly
- add redaction and leak tests for artifact rendering

Acceptance criteria:

- live public-safe artifacts appear in the UI after run completion
- filesystem-only and experimental outputs remain hidden from the public artifact view
- `FILESYSTEM_ONLY` artifacts are absent from rendered UI output, not merely hidden with styling
- guarded download links resolve only through the approved route
- `LOCAL_SENSITIVE` artifact access respects the guarded route policy and network-bind restriction
- empty and missing states do not look like failures when the API is still valid
- tests verify artifact filtering, link generation, and leak-safe rendering

### Phase 3: Run History and VPS Readiness

Scope:

- add recent-run history or explicit run lookup
- add operator guidance in the UI and runbook for the completed flow
- keep assumptions compatible with a future VPS-hosted operator workflow
- create [UI_SMOKE_TEST.md](UI_SMOKE_TEST.md) as the documented local validation checklist
- allow the UI to link to or summarize that checklist afterward without embedding validation-only internals directly into the main operator flow

Acceptance criteria:

- an operator can return to a recent run or look up a known run ID
- the UI and runbook describe the normal operator workflow clearly
- the UI does not assume notebook-local validation-only features are public runtime controls
- a documented smoke checklist exists for a full local run from creation through artifact review in [UI_SMOKE_TEST.md](UI_SMOKE_TEST.md)

## Explicit Non-Goals

This UI finalization plan does not include:

- SAR math changes
- GRID behavior changes
- notebook code changes
- tolerance changes
- reference manifest behavior changes
- public exposure of the notebook-exact GRID override
- any claim of fresh-ROI notebook parity

The UI phase should consume the accepted backend/public API surface as it exists. If a future UI need reveals a backend gap, that should be handled as a separate explicit goal.

## Validation Checklist

Implementation work under this plan should validate all of the following:

- frontend or static tests, if available
- API and public-surface tests
- unit and integration tests
- create and maintain [UI_SMOKE_TEST.md](UI_SMOKE_TEST.md)
- leak scans for:
  - `NOTEBOOK_REFERENCE_BUNDLE_DIR`
  - `grid_spec_override`
  - `crsTransform`
  - `bounds_utm`
  - `C:\`
  - `/content`
  - `RUN_lon`
  - `traceback`
- a manual local UI smoke test covering:
  - create run from UI
  - see run ID
  - poll status
  - see done or failed state
  - load artifacts
  - test download links
  - verify no coordinate, path, or traceback leaks

## Scope Guardrails

- Production GRID remains app-authoritative under Option B.
- Notebook-exact GRID remains validation/replay-only.
- Fresh-ROI notebook parity remains unclaimed.
- Reference bundle and manifest work stays outside normal public UI behavior.
- The UI should present the accepted production truth, not validation-only internals.
