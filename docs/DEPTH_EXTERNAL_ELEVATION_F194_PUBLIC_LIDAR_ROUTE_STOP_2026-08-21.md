# F194 — public-lidar cover route stop

Date: 2026-08-21

## Purpose

Apply the error-budget and stop rule that was frozen before any elevation values were opened.

The screening approximation is:

`RMSE_diff = sqrt(RMSE_pre^2 + RMSE_post^2)`

A candidate may proceed only if:

`nominal_target_thickness >= 5 * RMSE_diff`

This is only a screening rule. Any final execution would still require stable-ground co-registration outside the unit and would be judged using the measured residuals after co-registration, not merely the published acquisition RMSE values.

## Input from F193

F193 produced **zero valid lidar brackets**.

The candidate failures occurred before the F194 arithmetic gate:

- CWM Arlington L-12 — the 2018 lidar is already post-closure, so there is no valid pre-cover epoch.
- CWM Arlington L-13 — the 2018 lidar is before closure, but final waste placement before that flight was not proven and no valid post pair was established.
- Masonville Cove — final-fill/cap timing is unresolved and the strongest recovered 2020 lidar footprint stops south of the referenced site location.
- Tangerine Landfill — the March 2015 pre-cover lidar is excellent in timing and reports RMSEz 0.0976 m, but same-footprint post-closure 2021 lidar coverage could not be proven under the three-fingerprint rule.
- Yolo WMU 4/5 reserve — official closure documents prove survey-controlled cover construction, but the recovered public lidar epochs do not prove the required final-grade -> pre-lidar -> cover -> post-lidar sequence.

## F194 arithmetic result

There are no valid pre/post lidar pairs to enter into the error-budget calculation.

Therefore:

- candidates entering F194: **0**
- candidates passing F194: **0**
- required minimum survivors to continue: **2**

## Stop-rule decision

**STOP.**

The breadth-first public-lidar permanent-cover route is closed on current free public evidence.

Do not start another generic landfill/cap candidate search to rescue this route. The dominant failure is not nominal cover thickness or lidar precision; it is the very narrow timing requirement for a pre-cover surface acquired after final waste placement and before cap placement, plus same-footprint post-cover coverage.

## What this does and does not prove

This does prove:

- the current free public-lidar route did not produce two executable independent cover-thickness validation sites under the frozen rules;
- relaxing the final-waste-placement timing condition would create a serious risk of measuring waste/grading plus cover instead of cover;
- the search is now bounded and reproducible rather than open-ended.

This does **not** prove that numerical depth is physically impossible or that no private/agency survey records exist.

It also does not invalidate the separately recovered direct survey evidence at Bremo or Yolo. Those records are different evidence routes and must not be silently converted into a public-lidar validation claim.

## Ground-truth wording remains frozen

Published 2-ft, 3-ft, or similar cover requirements are **nominal regulatory/design thicknesses**, not measured mean thicknesses. Even if a future lidar pair is recovered, it can initially test only whether elevation differencing recovers approximately the specified cover unless independent as-built thickness measurements are also available.

## Current next paths

The closed public-lidar route should not consume more research time.

The remaining honest paths are separate:

1. **Route A / recorded measurements:** expose existing reviewed Tyrone measured-zone depths as recorded measurements only, with no predictive extrapolation.
2. **Option 5:** retain useful non-depth sensor outputs without relabeling them as depth.
3. **Existing direct-survey artifacts:** Bremo/Yolo can be revisited only when a directly executable public survey surface/file is already available; do not depend on outbound replies to continue the project.

No classifier, UI, or NB formula change is authorized by this closure result.
