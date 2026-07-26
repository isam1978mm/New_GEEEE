# Numerical Depth Estimation — Radar-Linkage Feasibility Plan Hold — 2026-07-26

**Branch:** `main`  
**Status:** on hold by user decision  
**Related plan:** `docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`

---

## Decision

The radar-linkage feasibility-screen plan is **on hold for now**.

Do not begin its execution phases until the user explicitly reactivates the plan.

This hold supersedes the earlier execution status `radar_linkage_feasibility_screen = approved_next_phase` in the related decision document. The research design is preserved for possible later use; it is not cancelled or rejected.

---

## Current authoritative status

```text
broad_candidate_search = paused
broad_document_search = paused
radar_linkage_feasibility_screen = on_hold
feasibility_dataset_build = not_started
scientific_analysis_branch = not_started
calibration_record_created = false
training_started = false
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

---

## Work that must not start while on hold

- do not build the exploratory depth-gradient dataset;
- do not run the River Road, Auburn, John Sevier or Sconondoa radar-linkage screen;
- do not create a new Sentinel-1 scientific analysis branch for this plan;
- do not resume broad candidate or document searching for this plan;
- do not enable numerical depth in the app;
- do not treat proxy records as calibration truth.

Existing candidate dossiers and research records must remain preserved.

---

## Reactivation rule

Execution may resume only after an explicit user instruction to restart or continue the radar-linkage feasibility plan.

When reactivated, resume from the preserved implementation order in:

`docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_SCREEN_DECISION_2026-07-26.md`
