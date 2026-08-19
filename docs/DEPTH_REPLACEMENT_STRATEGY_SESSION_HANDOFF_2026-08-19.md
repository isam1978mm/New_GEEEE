# Depth Replacement Strategy — Session Handoff — 2026-08-19

## 1. Read this first

This is the controlling handoff for the numerical-depth replacement work after the Tyrone validation campaign.

The next session must **not** restart the old NB route, re-open the solved Tyrone transform problem, tune failed feature thresholds, or start another remote-sensing feature family without first completing the strategy decision described below.

Protected constraints remain:

- do not modify the classifier without explicit user permission;
- do not change the current NB formula to rescue numerical depth;
- do not change the UI for depth unless explicitly approved;
- do not silently alter geometry, thresholds, dates, or holdout rules after seeing results;
- do not use `NB_DEPTH`, classifier/PCA outputs, or other circular notebook-derived depth proxies as replacement-model predictors;
- reuse completed evidence and runs whenever possible;
- keep failed scientific routes closed unless genuinely new independent evidence justifies a new preregistered test.

## 2. True current status

### Tyrone ground truth

The project now has a strong Tyrone 3X reference set:

- six official AS-BUILT plot regions: TP1, TP2, TP3, TP5, TP6, TP7;
- official measured cover-depth samples and plot means;
- official drawing geometry;
- a validated Tyrone mine-grid -> global/WGS84 transform;
- 43 additional exact, independently mapped AS-BUILT test-pit depth measurements outside the development plots.

The old geometry blocker is **resolved**. Do not tell the user the local-grid -> global transform is still missing.

### Six plot measured means

- TP1: 27, 27, 26, 27, 32 in -> mean 0.70612 m
- TP2: 36, 34, 39, 42, 36 in -> mean 0.94996 m
- TP3: 50, 49, 54, 52, 47 in -> mean 1.28016 m
- TP5: 28, 26, 26, 28, 26 in -> mean 0.68072 m
- TP6: 40, 35, 42, 36, 34 in -> mean 0.94996 m
- TP7: 50, 50, 52, 51, 54 in -> mean 1.30556 m

Surface groups:

- outslope: TP1 / TP2 / TP3
- top surface: TP5 / TP6 / TP7

Matched nominal-depth pairs:

- TP1 <-> TP5 (~2 ft)
- TP2 <-> TP6 (~3 ft)
- TP3 <-> TP7 (~4 ft)

The official CQAR drawing identifies the six areas as AS-BUILT.

## 3. NB numerical-depth route is permanently closed

The existing NB notebook-derived numerical-depth route failed validation and must remain closed.

Key evidence already established:

- raw NB absolute values were badly wrong at TP5/TP6;
- TP5/TP6 two-anchor calibration failed the held-out TP7 plot;
- independent outslope TP1/TP2/TP3 ordering failed;
- same-depth top-vs-outslope NB offsets were large, showing strong surface/site dependence;
- individual NB component variables did not provide a consistent independent depth signal.

NB may remain only as an **uncalibrated notebook-derived proxy**, not measured/calibrated/validated metres.

Primary closure document:

- `docs/NB_NUMERICAL_DEPTH_ROUTE_CLOSED_2026-08-18.md`

## 4. Tyrone global transform is solved

Merged PR #81 resolved the Tyrone local-mine-grid -> global/raster gate using official coordinate pairs from the 2024 Emma Part 4 Exploration Permit Application.

Validation recorded in PR #81:

- 4 spatially distributed official control rows used for fitting;
- 30 official rows held out;
- maximum holdout residual: 0.002533 m;
- final 34-point fit maximum residual: 0.001657 m;
- no depth values or NB values were used to fit/select the transform.

Read:

- `docs/TYRONE_SIX_PLOT_GLOBAL_TRANSFORM_GATE_2026-08-18.md`
- `data/depth_reference/tyrone_mine_grid_to_global_transform_v1.json`
- `data/depth_reference/tyrone_mine_grid_wgs84_controls_v1.csv`
- `data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`
- `data/depth_reference/TYRONE_3X_SIX_PLOT_REFERENCE_V1_README.md`

Important limitation retained: the six plot boundaries are digitized from official AS-BUILT drawing centerlines, not original CAD/survey vertices.

## 5. Replacement feature families already tested

Do not repeat these tests or loosen their frozen gates after the failures.

### A. Sentinel-1 C-band raw amplitude — FAILED

Merged PR #83.

- 177/177 selected reads succeeded;
- 72 usable months;
- all six 10 m-eroded plot masks had sufficient pixels;
- VV, VH, and VV−VH/log-ratio all failed the frozen six-plot depth-responsive gate;
- same-depth top-surface vs outslope offsets remained large.

Read:

- `docs/TYRONE_SIX_PLOT_RAW_RTC_RESULT_2026-08-18.md`
- `data/tyrone_six_plot_raw_rtc_result_2026-08-18.json`

### B. Terrain variables — DIRECT ROUTE FAILED; northness candidate failed independent holdout

Merged PR #85 produced an exploratory northness candidate, but it was not accepted as depth.

Merged PR #88 independently tested northness on 43 exact mapped AS-BUILT test pits.

Frozen holdout result:

- 10 m: Spearman rho = 0.26355; one-sided permutation p = 0.04212;
- 20 m: rho = 0.27084; p = 0.03846;
- preregistered rule required rho >= 0.30 AND p <= 0.05 at both radii;
- both fail the effect-size requirement.

Northness is closed without rescue.

Read:

- `docs/TYRONE_SIX_PLOT_TERRAIN_RESULT_2026-08-18.md`
- `data/tyrone_six_plot_terrain_result_2026-08-18.json`
- `docs/TYRONE_TESTPIT_NORTHNESS_HOLDOUT_RESULT_2026-08-18.md`
- `data/tyrone_testpit_northness_holdout_result_2026-08-18.json`
- `data/depth_reference/tyrone_3x_testpit_northness_holdout_points_v1.csv`
- `data/tyrone_testpit_northness_holdout_point_results_2026-08-18.csv`

The 43 test pits are valuable ground truth. They span roughly 24–35 inches (about 0.61–0.89 m) and have mapped UTM/WGS84 positions. They are point measurements, so do not pretend one pit is an entire coarse satellite pixel.

### C. Landsat daytime thermal — FAILED

Merged PR #91.

Corrected frozen run:

- 173/173 candidate surface-temperature reads succeeded;
- 134 acquisitions satisfied the all-six-plots availability rule;
- increasing depth ordering in both surface groups: 14/134 (10.45%);
- decreasing ordering: 5/134;
- 115/134 showed neither;
- frozen global requirement was >=70%; all seasonal gates also failed;
- matched-depth top-surface vs outslope temperature offsets were large and persistent.

The first attempt was only a technical datatype bug before values were evaluated; it is not a scientific result.

Read:

- `docs/TYRONE_SIX_PLOT_THERMAL_SCREEN_RESULT_2026-08-18.md`
- `data/tyrone_six_plot_thermal_screen_result_2026-08-18.json`

### D. Sentinel-2 NDVI / NDMI — FAILED

Merged PR #94.

- 308 candidate Sentinel-2 L2A items processed;
- zero technical failures;
- NDVI and NDMI each had all 42 possible April–October 2018–2023 year-month composites usable;
- NDVI strongest direction: 12/42 = 28.57%; frozen threshold >=70%;
- NDMI strongest direction: 12/42 = 28.57%; frozen threshold >=70%;
- both failed their calendar-month consistency gates;
- NDMI showed strong matched-depth top-surface vs outslope offsets.

Read:

- `docs/TYRONE_SIX_PLOT_OPTICAL_SCREEN_RESULT_2026-08-18.md`
- `data/tyrone_six_plot_optical_screen_result_2026-08-18.json`

### E. NISAR L-band GCOV amplitude — FAILED

This was the last feature family tested in this session.

NISAR coverage feasibility was confirmed and recorded in merged PR #96:

- 7 PROVISIONAL L2 GCOV and 7 GSLC products over Tyrone;
- 4 ascending / 3 descending acquisitions from 2026-06-17 through 2026-07-23;
- all 40+5 mode with Frequency-A HH/HV;
- primary test used Frequency-A GCOV at 10 m posting.

The actual frozen test rules were preregistered and merged in PR #97 before backscatter values were inspected.

Authenticated execution occurred in temporary PR #98. The user configured the GitHub Actions repository secret `EARTHDATA_TOKEN`. Do not ask the user to paste or expose this token. It is a secret and should remain only in GitHub Actions settings.

The first authenticated attempt failed technically before backscatter inspection because `earthaccess.login()` tried to contact an optional Earthdata profile endpoint that was network-unreachable. Only the authentication implementation was changed; the scientific protocol was not changed.

The corrected frozen run completed successfully.

Merged permanent result: PR #99.

Result:

- all seven fixed GCOV acquisitions were usable;
- all six 10 m-eroded plots passed pixel support; minimum observed valid pixels = 48 (frozen minimum = 15);
- HH dB: same-direction decreasing in both surface groups on only 1/7 acquisitions; increasing 0/7;
- HV dB: 0/7 in either direction;
- HH−HV dB: 0/7 in either direction;
- frozen pass gate: >=5/7 overall, >=3/4 ascending, >=2/3 descending for one same direction;
- no feature passed;
- matched-depth surface offsets remained substantial, especially HH (mean about -2.99 dB).

Direct NISAR amplitude is closed without rescue.

Read:

- `docs/TYRONE_NISAR_COVERAGE_FEASIBILITY_RESULT_2026-08-18.md`
- `data/tyrone_nisar_coverage_feasibility_result_2026-08-18.json`
- `docs/TYRONE_NISAR_GCOV_PREREGISTRATION_2026-08-18.md`
- `data/tyrone_nisar_gcov_preregistration_2026-08-18.json`
- `docs/TYRONE_NISAR_GCOV_SCREEN_RESULT_2026-08-19.md`
- `data/tyrone_nisar_gcov_screen_result_2026-08-19.json`

Temporary experiment PR #98 is closed **without merge**. Do not merge its experimental code/workflow into production.

## 6. Independent-site audit performed this session

After the Sentinel-1 / terrain / thermal / optical failures, the project re-audited the strongest previously researched measured-depth sites instead of blindly adding features.

Conclusion: **no existing independent site in the project currently passes all locked gates for a clean second remote-sensing calibration site.**

Important near-misses:

### Tyrone Dam 1

- official records recovered again;
- record supports acreage with cover >3 ft, but does not provide two exact broad measured-depth zones suitable for the calibration gate;
- not a second calibration site.

### Sconondoa Phase 3

This is the strongest measurement/georeference near-miss:

- validated survey placement;
- shallow zone mean ~3.511 m;
- deep zone mean ~4.881 m;
- same restoration assembly;
- control residuals were excellent;
- but clean safe footprint sizes were only about 16.6 m and 18.8 m, below the locked 20 m analysis footprint requirement.

Therefore measurement + placement passed, spatial support failed.

### Hoosier #1 Landfill

- real coordinate-tied measured thickness points exist;
- 18 measurements in a 1.85-acre south-slope area;
- no two separate broad shallow/deep polygons;
- boundary-constrained geometry;
- missing numerical survey uncertainty / equivalence proof.

### Rocky Mountain Arsenal

- large mapped nominal 2 ft and 3 ft cover polygons exist;
- common vegetation management is documented;
- but public records did not provide coordinate-tied absolute final measured as-built depths for both depth conditions.

### Consolidated Iron and Metal

- exact measured cover depths approximately 3.0–6.2 ft;
- licensed surveyor and same final surface;
- but supported shallow cell is only 15.24 m wide, so it fails the 20 m clean-footprint gate.

### J.R. Whiting

- 107 final-cover control points on ~100 ft grid;
- measured depth range ~2.03–2.50 ft;
- candidate cells around 30.48 m nominal width;
- but no numerical survey accuracy was found and the clean depth contrast/pair was not strong enough for the locked gate.

### Plant Kraft AP-1

- confirmed removal and survey maps exist;
- exact WGS84 boundary / boundary uncertainty and stable post-removal timing were not established.

### Other previously screened candidates

McMaster Street, SLAPS, Ford River Raisin, Ona HI-3, RMA and other historical candidates remain closed/held for their documented blockers. Do not restart them without new official evidence that directly resolves the prior fatal blocker.

## 7. Project Sources currently relevant

Project Sources include:

- `3X_CQAR_010_R0.pdf`
- `3X_CQAR_004_R0.pdf`
- `3X_CQAR_006_007_R0.pdf`
- `geometry_sensitivity.csv`
- `geometry_sensitivity_summary.json`

The old `geometry_sensitivity` files refer to provisional historical 40 m cores and produced `GEOMETRY_SENSITIVE_INCONCLUSIVE`; they must not override the later validated PR #81 transform / WGS84 six-plot reference.

## 8. Current scientific conclusion

The project has now tested multiple independent free/public surface-response families against the same well-characterized Tyrone ground truth:

- existing NB heuristic: FAILED
- Sentinel-1 C-band amplitude/polarization: FAILED
- terrain/northness: FAILED independent holdout
- Landsat daytime thermal: FAILED
- Sentinel-2 vegetation/moisture: FAILED
- NISAR L-band amplitude/polarization: FAILED

Across multiple families, the recurring diagnostic is that **surface type / terrain / near-surface condition often produces stronger differences than the buried cover-depth contrast**.

This does not prove that numerical depth is impossible in every setting. It does mean the project should stop treating another ordinary surface-response feature as the likely solution for general numerical depth.

Numerical app depth remains **blocked**. No replacement model has been scientifically validated.

## 9. Exact stopping point

The last user instruction before this handoff was to continue after NISAR failed.

The session began a **strategy reset**, with the explicit rule:

> Do not test another random feature. Reassess all accumulated failures together and decide the most realistic remaining way to obtain numerical depth.

The strategy reset was interrupted by the user's request to hand the session off.

No new feature family has been approved or preregistered after NISAR.

## 10. Exact next action for the next session

The next session must **not start a new sensor experiment immediately**.

First produce a short decision memo comparing the remaining physically distinct routes, using the evidence above. At minimum evaluate:

1. **Elevation-difference / before-vs-after surface route**
   - historical LiDAR, photogrammetry, DEM, construction survey or pre-cover vs final-grade surfaces;
   - this measures actual vertical change where both surfaces exist, instead of trying to infer buried depth from current surface response;
   - determine whether it can produce useful depth for arbitrary AOIs or only selected sites.

2. **More independent measured-depth sites / supervised empirical model route**
   - determine whether additional sites would genuinely solve the surface-confounding problem or merely provide more examples of site-specific behavior;
   - do not fit a model just because Tyrone has 43 point measurements;
   - any model plan must specify site-level holdout and surface-type controls before fitting.

3. **Active/local subsurface measurement route**
   - GPR or other field/paid active sensing;
   - determine whether this can calibrate a reusable model or whether it would require per-AOI measurement;
   - include realistic cost/operational implications.

4. **Keep numerical depth unavailable while retaining non-depth outputs**
   - if no scientifically defensible low-cost route remains, state this plainly instead of inventing metres;
   - Option 5-style anomaly/surface-change outputs can remain clearly labelled as not depth.

The next session should rank these routes by:

- scientific defensibility;
- generalizability to new AOIs;
- cost;
- need for user/operator-supplied data;
- implementation effort;
- whether they can truly unblock app numerical depth.

Only after that decision should a new experiment or implementation be proposed.

## 11. How to work with the user

The user expects:

- very clear/simple English;
- one decision/question at a time;
- always say whether a result **passed, failed, or is blocked**;
- always state the exact next action and whether the user needs to do anything;
- do not make the user rediscover dependencies after days of work;
- do not imply new calibration sites are required unless the strategy decision actually reaches that conclusion;
- do not stop silently in the middle of a finite test;
- do not change classifier/UI/NB formulas without explicit permission.

Canonical local backend port remains **8007**, not 8000.

## 12. Recent PR chain to know

- PR #79 — add Tyrone six-plot reference and close NB numerical route — merged
- PR #80 — document then-unresolved global transform gate — merged; later superseded on transform status by PR #81
- PR #81 — resolve Tyrone global transform / WGS84 six-plot reference — merged
- PR #83 — raw Sentinel-1 screen failure — merged
- PR #85 — terrain screen / northness exploratory candidate — merged
- PR #86 — preregister independent northness holdout — merged
- PR #88 — northness holdout failure — merged
- PR #89 — preregister thermal — merged
- PR #91 — thermal failure — merged
- PR #92 — preregister Sentinel-2 optical — merged
- PR #94 — NDVI/NDMI failure — merged
- PR #96 — NISAR coverage feasibility — merged
- PR #97 — preregister NISAR GCOV screen — merged
- PR #98 — temporary NISAR experiment — CLOSED WITHOUT MERGE
- PR #99 — permanent NISAR failure result — merged; merge SHA `c0658e610f57cc8325dfe5ef316db8e7fb3cfc62`

## 13. One-sentence handoff

**We now have excellent Tyrone ground truth and solved georeferencing, but every preregistered free/public surface-response depth route tested so far has failed; the next session must choose a physically different numerical-depth strategy rather than run another feature screen.**
