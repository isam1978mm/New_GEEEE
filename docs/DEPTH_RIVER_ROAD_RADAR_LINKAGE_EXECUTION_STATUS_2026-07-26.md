# River Road Radar-Linkage Execution Status — 2026-07-26

**Branch:** `main`  
**Status:** site screen inconclusive at geometry gate; move to Auburn

## Completed

- Reactivated the bounded radar-linkage feasibility plan.
- Created the execution plan for River Road, Auburn, John Sevier and Sconondoa.
- Added the privacy-safe multi-date Sentinel-1 runner, focused tests, CI workflow, River Road runbook and manifest example.
- Reused the tested neutral Buto feature path rather than creating a new radar-processing chain.
- Rechecked the official River Road Record of Decision and current EPA site profile.

## Evidence available

The public record supports:

- an inactive protected landfill cap;
- a minimum three-foot final cover statement;
- 129 excavated certification pits;
- surveyed pit locations and pit-by-pit values known to exist;
- a roughly east-west landfill approximately 1,000 by 2,100 feet;
- continuing cap maintenance and institutional controls.

These facts are sufficient to retain River Road as a feasibility candidate, but not to draw the private test polygons.

## Geometry decision

The runbook requires target and comparison polygons supported by a visible source or reviewed imagery. The available public text provides only approximate dimensions and location. The final-cover certification drawing and accepted pit-location sheet still cannot be rendered or visually reviewed.

Creating rectangles from the public centroid and approximate dimensions would invent the capped boundary and could include:

- the uninvestigated southeast knob;
- roads and wooded edges;
- drainage channels, berms and sedimentation structures;
- leachate, gas and monitoring infrastructure;
- borrow or maintenance areas.

No defensible matched comparison polygon can be confirmed from the presently visible evidence. The geometry rule is therefore not weakened.

## River Road result

```text
private_target_geometry_available = no
private_comparison_geometry_available = no
accepted_anchor_dates_available = no
earth_engine_query_executed = no
site_surface_response_decision = site_screen_inconclusive
inconclusive_reason = visible_reviewed_geometry_unavailable
cross_site_depth_linkage_decision = not_evaluated
```

River Road is not rejected as scientific evidence. It remains on hold for a genuinely readable final-cover drawing, survey sheet or reviewed private imagery package.

## Verification status

```text
focused_tests_committed = yes
github_actions_workflow_committed = yes
attached_ci_status_visible = no
local_clone_test_attempted = yes
local_clone_test_completed = no
local_clone_blocker = runtime_DNS_could_not_resolve_github
```

No test pass is claimed until CI appears or the focused tests run locally.

## Next action

Proceed directly to Auburn McMaster Street. Do not resume generic candidate searching.

Auburn is stronger for the next step because the public record describes a later vacant compacted-gravel surface and states that licensed as-built drawings contain actual local cover thicknesses and mapped geometries. The immediate task is to recover or render the Auburn as-built appendix and identify at least two comparable subareas for a depth-ordering screen.

## Depth boundary

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```
