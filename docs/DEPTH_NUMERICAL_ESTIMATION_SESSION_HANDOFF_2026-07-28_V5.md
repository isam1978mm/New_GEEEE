# Numerical depth evidence search — session handoff — 2026-07-28 V5

## Goal

Unlock a defensible numerical depth output in the New_GEEEE app.

This work is about the app and its calibration evidence. Do not discuss the uploaded notebook unless the user specifically asks about it.

## Current status

```text
usable positive site groups = 0
usable confirmed negative site groups = 0
usable calibration rows = 0
numerical depth ready = no
app depth enabled = false
Earth Engine query executed = no
training started = false
plan changed = no
```

One successful pair would not complete the full dataset. Independent site groups and confirmed negatives will still be needed across train, validation and holdout.

## Locked approved plan

Continue only with full-scale vegetated zones that:

- retain at least 30–40 m clean width after excluding edges, slopes, drainage, roads and equipment;
- contain final measured as-built depths, not design values;
- provide a second exact measured depth or confirmed negative zone;
- share equivalent radar-facing soil and vegetation;
- have coordinate-tied polygons;
- include numerical depth or survey uncertainty;
- remained stable during a usable Sentinel-1 period.

Do not change this plan without user approval. Do not run Earth Engine until every documentary gate passes.

Reject immediately:

- narrow plots;
- scattered points requiring invented polygons;
- nominal or design-only depths;
- threshold labels such as `greater than 3 feet`;
- volume-derived averages;
- different surface materials or vegetation treatments;
- repaired, eroded, trenched, ponded or redeveloped surfaces.

## How we worked

1. Cheap screen first: width, surface, construction date and likely stability.
2. Prefer primary regulator, owner, CQA, as-built and monitoring records.
3. Stop at the first fatal blocker.
4. Use an isolated branch and draft PR only for blocked public-record recovery.
5. Never merge recovery branches.
6. Read PDF text first; render only decisive maps, profiles, tables and survey pages.
7. Never invent geometry from an ungeoreferenced drawing.
8. Record each final decision as JSON in `data/` and Markdown in `docs/` on `main`.
9. Close every temporary PR without merging.
10. Report plainly: good to go or not, blocker, app status and next action.

A temporary Middlesex downloader was accidentally added to `main` and immediately removed in commit `ca03494f4012b929b382782d17fd9054bf8b3542`.

## Exact stopping point

Latest completed candidate: **Syncrude Oil Sands Soil Reconstruction Project**.

Decision: **NOT GOOD TO GO**.

The recovered report proves a seven-hectare program with nine mixtures at nominal 20 cm and 40 cm depths. The Typical Plot Configuration is only about **22 m × 44 m**. The 22 m width fails before any edge, planting or sampling exclusion.

```text
latest decision commit = 3e2967b15ea31b0c3516bb64a90c0d05dc2177e0
latest JSON commit = eb377e47fd17368279256dc906b80d38bed93ff6
temporary PR = #32
workflow run = 30367952520
artifact ID = 8691608148
PR state = closed
merged = no
open temporary PRs = 0
active candidate = none
```

The next session must start a new candidate screen. Do not restart this candidate.

## Strongest near-misses

### Tyrone Dam 3X

Strongest overall pair:

- 4.06-acre and 4.50-acre plots;
- final measured means of 26.8 and 37.4 inches;
- published 95% intervals;
- common cover and revegetation program;
- enough width.

Fatal blockers: no public coordinate-tied polygons and no exact plot-level unchanged Sentinel-1 period.

Only reopen if public GPS, CAES, GIS, CAD or surveyed vertices are found together with later plot-specific stability evidence.

### Syncrude 1990 capping study

Strong replicated measured plots:

- 60 m × 60 m plots;
- 50 measurements per plot;
- measured means near 39, 58 and 80 cm.

Fatal blockers: no numerical uncertainty, no surveyed geographic plot coordinates, variable peat/vegetation and no proof the exact plots survived unchanged after 2014.

### NAS Alameda Site 2

Strong 336-point final grid with possible shallow and deep clusters. Failed because there are no official shallow/deep polygons, the best deep cluster crosses infrastructure and the survey uncertainty appendix is missing.

### Aitik

Two approximately 50 m × 50 m stable vegetated plateaus with nominal 1.0 m and 1.5 m protective layers. Failed because depths are design configurations, not final measured values, and coordinates/uncertainty are missing.

## Other completed decisions in this session

All are **NOT GOOD TO GO**:

- Ford River Raisin: surface contours, not cap thickness; no different east/west measured depth.
- Olympic View: narrow perimeter pits and no published thickness values.
- Central Maui and Peter Pitchess: one repeated uniform depth design.
- Salzburg Road: good measurement plan, but completed measurement tables unavailable.
- Allen Harbor: 2-foot and 3-foot descriptions, not measured as-built depths.
- SLAPS: planned cut surfaces and contamination verification, not final depth.
- Tyrone Dam 1: only `greater than 3 feet` acreage categories.
- Middlesex Sampling Plant: cleanup survey units, not depth zones; later redevelopment.
- Little Rock USNR: one common depth; treatments differ by seed and mulch.
- Detour Lake: design depths, major confounders and disturbed surfaces.
- South Bison Hill: nominal depths, missing coordinates/uncertainty and dense infrastructure.
- Aurora: large cells, but construction report unavailable and treatments vary other materials.
- Syncrude 1990: measured depths but missing uncertainty, coordinates and stability.
- Syncrude Soil Reconstruction: plots only 22 m wide.

Cheap-screen rejects that should not be repeated without genuinely new evidence include Camp Pendleton OU3, Chino Rubio Peak, Questa, Berkeley/César Chávez, Morenci, Century, Rosebery, Cannington, Cadia, Golden Sunlight, Loy Yang, Kestrel, Mt Leyshon, Mt Morgan, Kidston, Whistle, Ronneburg and other narrow research plots.

## Next steps

### Immediate search

Search by evidence type rather than site name:

```text
as-built thickness survey
final cover thickness grid
matched subgrade final-grade survey
surveyed plot corners
northing easting cover thickness
GIS or CAD as-built cover
construction certification thickness
CQA thickness table
GPR cover thickness map
financial assurance release as-built
```

Prefer polygons at least 50–60 m wide before exclusions.

Prioritized rescue routes, only if the missing evidence itself is found:

1. Tyrone Dam 3X coordinates plus exact later stability;
2. Syncrude 1990 uncertainty, coordinates and post-2014 persistence;
3. NAS Alameda omitted survey appendix and official infrastructure-free polygons.

### If a candidate passes

1. Extract official polygons and measured depths.
2. Record uncertainty.
3. Apply conservative exclusions.
4. Confirm clean width and stable dates.
5. Create provisional private calibration rows.
6. Run `scripts/validate_depth_calibration_pack.py`.
7. Only after validation, run a bounded Earth Engine comparison.
8. Continue collecting independent sites and negatives.

### If a candidate fails

1. Stop at the first fatal blocker.
2. Add one JSON result and one Markdown decision on `main`.
3. Close the temporary PR without merging.
4. Continue the approved search unchanged.

## Required reading

Read in this order:

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-28_V5.md`
2. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-27_V4.md`
3. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
4. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
5. `docs/DEPTH_FEATURE_INVENTORY.md`
6. `scripts/validate_depth_calibration_pack.py`
7. `docs/DEPTH_TYRONE_DAM3X_COVER_DEPTH_PAIR_RESULT_2026-07-27.md`
8. `data/tyrone_dam3x_cover_depth_pair_screen_result.json`
9. `docs/DEPTH_SYNCRUDE_1990_CAPPING_STUDY_RESULT_2026-07-28.md`
10. `data/syncrude_1990_capping_study_depth_pair_screen_result.json`
11. `docs/DEPTH_AITIK_COVER_TRIAL_RESULT_2026-07-28.md`
12. `data/aitik_cover_trial_depth_pair_screen_result.json`
13. `docs/DEPTH_SYNCRUDE_SOIL_RECONSTRUCTION_RESULT_2026-07-28.md`
14. `data/syncrude_soil_reconstruction_depth_pair_screen_result.json`
15. `docs/DEPTH_TYRONE_DAM1_COVER_DEPTH_PAIR_RESULT_2026-07-28.md`
16. `data/tyrone_dam1_cover_depth_pair_screen_result.json`
17. `docs/DEPTH_MIDDLESEX_SAMPLING_PLANT_RESULT_2026-07-28.md`
18. `data/middlesex_sampling_plant_depth_pair_screen_result.json`
19. `docs/DEPTH_LITTLE_ROCK_USNR_COVER_RESULT_2026-07-28.md`
20. `data/little_rock_usnr_cover_depth_pair_screen_result.json`
21. `docs/DEPTH_DETOUR_LAKE_COVER_TRIAL_RESULT_2026-07-28.md`
22. `data/detour_lake_cover_trial_depth_pair_screen_result.json`
23. `docs/DEPTH_SOUTH_BISON_HILL_COVER_RESULT_2026-07-28.md`
24. `data/south_bison_hill_cover_depth_pair_screen_result.json`
25. `docs/DEPTH_AURORA_SOIL_CAPPING_RESULT_2026-07-28.md`
26. `data/aurora_soil_capping_depth_pair_screen_result.json`
27. The earlier completed-candidate list inside V4.
28. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-27_V3.md` only for older history.

## Final handoff

There is no active candidate, branch, PR, workflow or Earth Engine request.

Start the next session with a new cheap screen focused on public final construction surveys containing measured thickness, numerical uncertainty and georeferenced polygons. Keep the approved plan unchanged.
