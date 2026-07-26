# River Road Radar-Linkage Execution Status — 2026-07-26

**Branch:** `main`  
**Status:** implementation complete; Earth Engine query not yet executed

## Completed

- Reactivated the radar-linkage feasibility plan after the user's explicit instruction to continue.
- Created the bounded execution plan for River Road, Auburn, John Sevier and Sconondoa.
- Added a reusable privacy-safe multi-date Sentinel-1 site-screen runner.
- Reused the tested neutral Buto feature path rather than creating a new radar-processing chain.
- Added focused unit tests for privacy, confounder controls, multi-date agreement, incidence-angle exclusion and insufficient-anchor refusal.
- Added a focused GitHub Actions workflow.
- Added the River Road private-input runbook and acquisition-screen manifest example.

## Repository commits

```text
a917504 docs: activate depth radar linkage feasibility execution
a5b6493 feat: add multi-date depth radar linkage screen
f115faf test: cover multi-date depth radar linkage screen
64de1a7 ci: verify depth radar linkage screen
ff484e6 docs: add River Road radar linkage runbook
36fa14f docs: add River Road acquisition manifest example
```

## Verification status

```text
focused_tests_committed = yes
github_actions_workflow_committed = yes
attached_ci_status_visible = no
local_clone_test_attempted = yes
local_clone_test_completed = no
local_clone_blocker = runtime_DNS_could_not_resolve_github
```

No test pass is claimed until either the GitHub Actions check appears or the focused tests are run in the user's local repository.

## Real River Road query status

```text
private_target_geometry_available = no
private_comparison_geometry_available = no
accepted_anchor_dates_available = no
earth_engine_query_executed = no
site_surface_response_decision = not_run
cross_site_depth_linkage_decision = not_evaluated
```

The real query cannot honestly run without the private geometry and acquisition-screen package. The repository deliberately rejects repository-local geometry and detailed outputs.

## Exact next action

Prepare outside Git:

```text
river_road_target.geojson
river_road_comparison.geojson
river_road_acquisition_screen.json
```

Then run the dry-run command in:

```text
docs/DEPTH_RIVER_ROAD_RADAR_LINKAGE_RUNBOOK_2026-07-26.md
```

If the dry run reports at least two accepted anchors, run the same command with `--execute` and store the detailed result outside Git.

## Depth boundary

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```

After River Road is completed or declared inconclusive, continue to Auburn without resuming generic candidate searching.