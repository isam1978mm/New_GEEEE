# Depth validation — F165 Meredosia elevation route — 2026-08-20

## Decision

Open a new **site-independent direct-elevation validation route** using Meredosia, Illinois as the first candidate.

This does **not** unblock Tyrone Step 4. Tyrone remains blocked on the missing 2004 immediate post-grading / pre-cover 3X surface. Existing M3 and Freeport/Tyrone record requests remain active in parallel.

The new route asks a different question:

> Can the direct geometry method be validated at a newer earthwork site where a trustworthy pre-work elevation surface and a trustworthy post-work/as-built surface both exist?

If yes, the numerical-depth concept can be tested without waiting for Tyrone's private 2004 construction records.

## Why the old eight-site audit must be re-scored

The prior site screens were built around Sentinel-1 / radar comparability. Several old rejection rules do not apply to direct elevation differencing:

- same radar surface material — not required;
- stable Sentinel-1 temporal window — not required;
- incidence-angle/orbit consistency — not required;
- approximately 20 m clean Sentinel-1 footprint — not required for 1 m-class lidar/survey work.

A site rejected for a radar-specific reason must therefore not automatically remain rejected for an elevation-only method.

## Meredosia first-candidate facts to verify

Candidate: Meredosia Power Station CCR closure, Illinois.

Current evidence indicates:

- 2018 CCR removal / closure construction occurred;
- official construction/CQA records and survey/as-built records exist;
- USGS/3DEP-era pre-2018 lidar exists over the Meredosia area, including a 2011 Meredosia tile;
- project survey work reportedly included UAS point clouds / DTMs during and after construction.

These facts make Meredosia a materially stronger direct-elevation candidate than it was under the radar screen.

## Important scientific corrections / guards

1. Do not call this Tyrone Step 4. It is a separate validation route.
2. `before - after = excavation depth` is only valid inside a spatially verified clean-excavation area.
3. Closure/cap-in-place areas, roads, pipelines, berms, fill, grading, or later cap material must be excluded unless their geometry is separately modeled.
4. Existence of lidar coverage is not enough. The pre-work lidar must contain usable ground/terrain returns inside the target excavation footprint.
5. The post-work/as-built surface must represent the excavated/final ground of the same footprint, not a later cap/fill surface.
6. Horizontal and vertical datums must be reconciled before differencing.
7. The historical/final-surface accuracy gate remains frozen; do not weaken it after seeing results.
8. Do not use known depth answers to fit, shift, tune, or select surfaces.
9. Do not change classifier, unrelated UI, NB formula, or production depth logic during this validation route.

## First go/no-go test

### F166 — Meredosia pre-work lidar usability

Determine whether a pre-2018 lidar dataset contains usable terrain/ground points inside the **actual Bottom Ash Pond clean-excavation footprint**.

Required checks:

1. identify the exact lidar acquisition date and product;
2. identify the Bottom Ash Pond clean-removal footprint from official closure/CQA/as-built material;
3. test lidar coverage over that footprint;
4. inspect whether points are present inside the footprint rather than water/no-data;
5. inspect classification / density / vertical accuracy metadata;
6. distinguish clean-removal area from capped-in-place or infrastructure areas.

### Decision rule

- If usable pre-work lidar terrain exists over a meaningful excavation footprint, Meredosia advances to post-work/as-built surface recovery and datum/accuracy screening.
- If the lidar footprint is mostly water/no-data or otherwise unusable, try the next pre-closure lidar epoch if one exists before 2018 construction.
- If no usable pre-work lidar exists, Meredosia closes and the old eight-site audit is re-scored candidate by candidate under elevation-only rules.

## Parallel Tyrone status

- Tyrone direct-elevation path: **BLOCKED at Step 4**.
- M3 Project `03141.01` request: active, no reply at last check.
- Freeport/Tyrone construction-record request: active, no reply at last check.
- These requests remain open but no longer gate all progress.

## Exact next action

Run F166 now: verify actual pre-2018 Meredosia lidar terrain coverage inside the clean-excavation footprint.