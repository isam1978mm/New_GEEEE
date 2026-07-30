# Numerical Depth Estimation Session Handoff — 2026-07-29 V4

## Purpose

This is the controlling handoff for the next session.

It replaces the older assumption that the app must wait for a globally validated public calibration dataset before any numerical-depth feature can ship.

The current product path is now:

1. keep the honest radar anomaly output already shipped as Option 5;
2. use operator-calibrated local AOI depth when measured same-site anchors are available;
3. keep global or transferable automatic depth research in the background;
4. do not let the global research block the working local feature.

---

## Executive decision

### GOOD TO GO

**Operator-calibrated local AOI depth is implemented and merged.**

It can return a numerical metre range for a candidate inside one local AOI when the operator supplies:

- at least two reviewed polygons with locally measured depth ranges;
- at least one reviewed candidate polygon from the same site;
- a completed app run containing the required neutral radar raster;
- a usable run-quality result.

The mode interpolates only inside the measured anchor support. It abstains rather than extrapolating.

### NOT GOOD TO GO

The following remain unsupported:

- automatic Tyrone shallow/deep classification;
- continuous Tyrone depth interpolation;
- unknown-site depth without measured local anchors;
- cross-site transfer;
- a global radar-to-depth model;
- enabling numerical depth by default.

### Unchanged

- Option 5 remains active and must always be labelled **Radar anomaly review — NOT DEPTH**.
- Option 3 is inactive.
- Option 1 public-evidence research may continue as background research, but it is no longer the shipping blocker.
- Global validated calibration rows remain `0`.

---

## Current status matrix

| Item | Status | Plain-English meaning |
|---|---|---|
| Operator-calibrated local AOI depth engine | **GOOD TO GO** | Working for one site with measured local anchors |
| In-app local-depth panel | **GOOD TO GO** | Merged and available on completed runs when enabled |
| Blank first-AOI GeoJSON template | **GOOD TO GO** | Downloadable from the operator panel |
| Browser preflight | **GOOD TO GO** | Rejects common bad or unfinished files before submission |
| Automatic reviewed-polygon signal extraction | **GOOD TO GO** | Reads the neutral `logRatio_dB.tif` raster |
| Local interpolation | **GOOD TO GO** | Produces metre ranges only inside anchor signal support |
| No-extrapolation abstention | **GOOD TO GO** | Unsupported candidates receive no invented metre values |
| Known Tyrone zone lookup | **GOOD TO GO, local only** | Can return the documented Plot 5 and Plot 6 ranges when reviewed zone IDs are used |
| Automatic Tyrone transfer | **NOT GOOD TO GO** | Fresh holdout failed all four spatial splits |
| Continuous Tyrone interpolation | **NOT GOOD TO GO** | Spatial holdout failed all four splits |
| Global automatic depth | **NOT GOOD TO GO** | No validated transferable calibration dataset |
| Option 5 anomaly output | **ACTIVE — NOT DEPTH** | Unitless within-run anomaly review only |
| App depth enabled by default | **No** | The local operator feature remains explicitly gated |
| Global usable calibration rows | `0` | No global training was started |

---

## Exact point reached

The code work is complete for the first feasible product route.

The session stopped immediately after the user asked how to restart the closed app. The startup command was confirmed from the repository README.

No real first-AOI calibration has run yet.

The next real result depends on operator-owned site data. The app cannot invent these inputs:

- two or more measured same-site anchor polygons;
- the measured minimum, best and maximum depth for each anchor;
- one or more candidate polygons from the same AOI.

This is now the only immediate product blocker.

It is an input requirement, not an unfinished coding blocker.

---

## Latest merged implementation

### PR #57 — in-app operator local depth

Title:

`Operator local depth: private in-app calibration flow`

Merged to `main`:

`042a4fb0dec3b2c7ce1e78bac02f86a098f25f26`

What it added:

- `POST /runs/{run_id}/operator/local-depth`;
- private per-run authorization;
- dedicated backend feature gate;
- browser-side GeoJSON reading;
- automatic signal extraction from reviewed polygons;
- private checksummed calibration package creation;
- local metre-range output or abstention;
- no returned geometry, coordinates, local paths or download URLs;
- a completed-run panel named **Local depth calibration — operator only**.

Final validation passed:

- production frontend build;
- complete repository suite;
- focused safety tests;
- forbidden `ee.Authenticate()` check;
- direct file-streaming check;
- notebook safety check.

### PR #58 — first AOI template and preflight

Title:

`Operator local depth: first AOI template and strict preflight`

Merged to `main`:

`d68c5a8c7dda04a35101bdaed398570fc6512336`

What it added:

- **Download blank GeoJSON template** in the local-depth panel;
- safe non-runnable example template;
- strict browser preflight;
- `.env.example` entry for the local-depth app flag;
- a first-AOI preparation guide;
- regression tests and status record.

The preflight rejects:

- `template_only: true` files;
- placeholder IDs;
- duplicate IDs;
- unsupported roles;
- missing or malformed Polygon/MultiPolygon geometry;
- unclosed or degenerate rings;
- nonnumeric coordinates;
- missing, negative or incorrectly ordered anchor depths;
- fewer than two anchors;
- no candidates;
- anchor sets with no distinct best-depth values.

A passing file shows:

- feature count;
- measured anchor count;
- candidate count;
- anchor and candidate IDs;
- the measured anchor support range.

Final validation passed the same complete CI and safety gates.

---

## Scientific behavior of the working local mode

The local mode is intentionally narrow.

### Inputs

Each measured anchor requires:

```json
{
  "feature_id": "anchor-shallow",
  "role": "anchor",
  "depth_min_m": 0.90,
  "depth_best_m": 1.00,
  "depth_max_m": 1.10
}
```

Each candidate requires:

```json
{
  "feature_id": "candidate-01",
  "role": "candidate"
}
```

All features also need reviewed Polygon or MultiPolygon geometry.

### Signal

The automatic extractor uses the completed run's neutral corrected radar raster:

`<RUN_DIR>/logRatio_dB.tif`

This is the app's `VV_dB - VH_dB` measurement.

The workflow does not use any of the following as physical-depth evidence:

- classifier output;
- PCA anomaly score;
- detected-object mask;
- target probability;
- Option 5 score.

### Boundary controls

The extractor:

- converts input geometry into the raster CRS;
- erodes polygons before sampling;
- requires a minimum valid-pixel count;
- rejects overlapping eroded interiors;
- blocks unusable run quality;
- calculates within-polygon signal uncertainty;
- widens the candidate metre range using that uncertainty.

### Interpolation controls

The package requires the best measured anchor depths to be monotonic with the extracted signal.

The candidate must stay inside measured anchor signal support.

When the candidate value or its uncertainty interval leaves support, the app abstains.

### Correct label

The result is:

**Experimental local calibrated depth range**

It is not:

- a validated global range;
- transferable to a different site;
- proof of an underground target;
- a universal Sentinel-1 depth formula.

---

## Tyrone result and why it must not be reopened casually

Tyrone provided strong measured cover anchors:

### Test Plot 5

- measurements: 28, 26, 26, 28 and 26 inches;
- mean: 26.8 inches;
- local range: approximately 0.65532–0.70612 m;
- best local value: approximately 0.68072 m.

### Test Plot 6

- measurements: 40, 35, 42, 36 and 34 inches;
- mean: 37.4 inches;
- local range: approximately 0.85090–1.04902 m;
- best local value: approximately 0.94996 m.

Both plots were large and used the same general cover and reclamation system.

However, official coordinate-controlled Plot 5/6 polygons and plot-specific post-2014 repair/stability maps were not recovered.

### Public electronic-file recovery

The public Attachment I PDF was only a scanned cover page saying that an electronic copy had been supplied on CD.

The public record did not include:

- the CD;
- a file manifest;
- CAD/GIS plot files;
- survey coordinates;
- a mine-grid conversion.

That recovery route is closed.

### Geometry-sensitivity test

A public Sentinel-1 RTC sensitivity test used 36 plausible map placements.

Result:

- passing placements: 9;
- required passing placements: 29;
- positive-direction passing placements: 8;
- opposite-direction passing placements: 1.

Decision:

`ordering_inconsistent`

Approximate geometry cannot support automatic unknown-AOI depth.

### Provisional ordering result

One provisional exact-placement development test found a VH ordering signal:

- 177 acquisitions;
- 72 usable months;
- TP6 minus TP5 VH positive in 54 of 72 months;
- mean difference approximately +0.55 dB.

But the magnitude changed substantially between early and late periods. That prevented a permanent absolute VH-to-depth formula.

### Continuous interpolation holdout

Four directional spatial splits were preregistered.

Required passing splits: at least 3 of 4.

Actual passing splits: 0 of 4.

Decision:

**NOT GOOD TO GO.**

### Fresh 2024–June 2026 two-band holdout

The shallow/deep rule was frozen before reading the fresh period.

Execution:

- selected acquisitions: 73;
- successful reads: 73;
- failed reads: 0.

Required passing splits: at least 3 of 4.

Actual passing splits: 0 of 4.

Coverage was generally below 40%, and confident wrong classifications remained.

Final decision:

**Automatic Tyrone shallow/deep depth is NOT GOOD TO GO.**

Do not retry by changing thresholds after seeing the same data.

Tyrone should be reopened only if materially new evidence appears, such as:

- official surveyed plot polygons;
- an exact grid conversion;
- mapped post-2014 repairs and exclusions;
- new independent measured zones;
- a genuinely independent validation period or site.

---

## Historical public-evidence research status

The broad Option 1 search screened many landfill, mine-cover and soil-reconstruction candidates.

Examples include:

- Aurora;
- Aitik;
- Faro;
- NAS Alameda;
- Salzburg;
- River Road;
- Syncrude 1983, 1990 and SW30;
- Mount Whaleback;
- Battle River;
- Highvale;
- Judy Creek;
- North Antelope/Rochelle;
- Stanton;
- Norris/Sunspot;
- Detour Lake;
- John Sevier;
- Silver Bow;
- Mount Taylor;
- Continental;
- Tyrone USNR;
- multiple global landfill batches.

Recurring failure reasons were:

- design thickness instead of measured as-built thickness;
- no numerical construction uncertainty;
- no coordinate-controlled treatment polygons;
- only one repeated cover design;
- material, slope, vegetation or drainage changed with thickness;
- plots too narrow after boundary exclusions;
- no stable post-2014 period;
- point measurements that could not be assigned as a uniform polygon depth.

Current public-evidence result:

```text
usable_global_calibration_rows = 0
global_training_started = false
global_numerical_depth_ready = false
```

This research may continue, but it must not replace the first real local-AOI run as the immediate priority.

---

## Option 5 status

Option 5 is merged and remains active.

Its label is:

**Radar anomaly review — NOT DEPTH**

It may show:

- object count;
- total object area;
- median mean anomaly;
- strongest peak anomaly;
- ranked detected-object rows.

It is:

- unitless;
- valid only within the current run;
- not a probability;
- not physical confirmation;
- not a measured temporal change;
- not a depth estimate.

Never rename it or describe it as depth.

---

## How we worked

The next session should preserve this working method.

### 1. Plain-English status first

Every meaningful update should say:

- current status;
- **GOOD TO GO** or **NOT GOOD TO GO**;
- what is missing;
- exact next step;
- whether the user must do anything.

### 2. Cheap decisive screens before expensive tests

For evidence candidates, test these first:

- plot width and clean interior;
- same material and surface treatment;
- measured versus nominal depth;
- coordinate geometry;
- post-2014 stability.

Do not spend time on satellite extraction after a candidate already fails one of those decisive gates.

### 3. Do not silently change plans

The current plan is local operator calibration first.

Global evidence research is background work.

Option 5 remains active.

Option 3 remains inactive.

### 4. Freeze scientific rules before reading holdout data

For experiments:

- preregister periods, features, thresholds and pass/fail rules;
- commit the protocol first;
- read the untouched data second;
- do not tune after seeing failure.

### 5. Temporary experiment PRs stay temporary

Recovery and scientific-test branches are marked do-not-merge.

When a route fails:

- save the decisive Markdown and JSON result on `main`;
- close the temporary PR without merge;
- do not leave executable experimental workflows as production code.

### 6. Product code stays isolated and default-off

Local depth was merged only after it was:

- private;
- gated;
- disabled by default;
- non-transferable;
- abstention-first;
- protected against geometry/path leakage.

### 7. Merge only after all validation passes

Required validation pattern:

- focused safety tests;
- full repository test suite;
- production frontend build;
- synchronized `frontend-v2/dist`;
- forbidden `ee.Authenticate()` check;
- direct file-streaming check;
- notebook safety check.

### 8. Honest abstention

When the evidence is outside measured support, output no metre values.

Do not substitute an anomaly score, classifier probability or plausible-looking midpoint.

### 9. Continuous execution

When the user says `go`, continue the approved work.

Do not stop at a tool handoff.

Do not promise background work or ask the user to wait.

---

## How to restart the app

On the user's Windows machine, open PowerShell and run:

```powershell
cd C:\Dev\New_GEE
git pull origin main
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`

Keep the PowerShell window open while using the app.

Press `Ctrl+C` in that window to stop the app.

For the local-depth panel, `.env` must contain:

```text
OPERATOR_LOCAL_DEPTH_APP_ENABLED=true
```

Restart the app after changing `.env`.

---

## First real AOI workflow

### User action required

**Yes.**

The user or site operator must provide real same-site measurements and reviewed polygons.

The next session cannot complete a genuine local calibration without them.

### Steps

1. Pull the latest `main` and start the app.
2. Confirm `OPERATOR_LOCAL_DEPTH_APP_ENABLED=true` in `.env`.
3. Open **Settings**.
4. Show **Operator private tools**.
5. Open a completed run with usable run quality and `logRatio_dB.tif`.
6. Expand **Local depth calibration — operator only**.
7. Select **Download blank GeoJSON template**.
8. Replace the placeholder feature IDs.
9. Replace every `null` coordinate with reviewed real polygon coordinates.
10. Enter measured `depth_min_m`, `depth_best_m` and `depth_max_m` for at least two anchors.
11. Add at least one candidate polygon from the same AOI.
12. Remove `"template_only": true`.
13. Upload the file.
14. Require **Preflight passed**.
15. Confirm the site ID and calibration dataset version.
16. Confirm that the polygons and measurements were reviewed.
17. Run local depth calibration.
18. Record every candidate result, including abstentions and warnings.

### Do not proceed when

- anchors come from different sites;
- the surface construction is materially different;
- measured depths are only nominal plans;
- polygons overlap after erosion;
- the candidate lies outside anchor signal support;
- run quality is blocked;
- the file still contains placeholders or example coordinates.

---

## Short roadmap

### Immediate roadmap — next session

Goal: produce the first genuine operator-calibrated local AOI result.

1. Restart the app.
2. Confirm the backend flag.
3. Identify one completed run.
4. Obtain the real measured-anchor GeoJSON.
5. Pass preflight.
6. Execute the in-app calibration.
7. Save a concise result document with estimated, abstained and failed candidate counts.

Success condition:

At least one candidate receives a local calibrated metre range without violating support, geometry, privacy or run-quality rules.

If all candidates abstain, that is still a valid test result. Document why.

### Near-term roadmap

Goal: determine whether the first local AOI is practically useful.

- use three or more measured anchors when possible;
- include one measured polygon as a withheld candidate;
- compare predicted range with the withheld measurement;
- report range coverage and absolute error;
- repeat across different acquisition windows for the same site;
- map and exclude repairs, drainage, infrastructure and disturbed edges.

Do not call the result validated from the same anchors used to fit it.

### Medium-term roadmap

Goal: strengthen one-site validation.

- collect independent same-site measured zones;
- use train and holdout polygons with no geometry reuse;
- preregister error and coverage thresholds;
- test temporal stability;
- test sensitivity to erosion pixels and minimum valid pixels;
- preserve all abstentions;
- create a site-specific versioned calibration package only after passing holdout.

Possible status after success:

`validated_local_range`

This still would not be a global model.

### Long-term roadmap

Goal: consider transferability only after multiple sites pass independently.

- use multiple sites with measured as-built depth and uncertainty;
- keep sites separated between training, validation and holdout;
- include surface, slope, vegetation, moisture and incidence controls;
- preregister model form and thresholds;
- require independent site-level validation;
- compare against LiDAR/DEM or survey-derived elevation change where available.

Only after those steps should the project consider a transferable or global depth feature.

---

## Required reading for the next session

Read in this order.

### A. Controlling current handoff

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29_V4_FEASIBLE_LOCAL_AOI.md`

### B. Current operator workflow

2. `docs/DEPTH_OPERATOR_LOCAL_AOI_APP_GUIDE_2026-07-29.md`
3. `docs/DEPTH_FIRST_AOI_PREFLIGHT_GUIDE_2026-07-29.md`
4. `docs/examples/operator_local_depth_first_aoi_template.geojson`
5. `data/operator_local_depth_app_status_2026-07-29.json`
6. `data/operator_local_depth_first_aoi_preflight_status_2026-07-29.json`
7. `README.md`

### C. Local engine and extraction details

8. `docs/DEPTH_OPERATOR_SIGNAL_EXTRACTION_GUIDE_2026-07-29.md`
9. `docs/DEPTH_OPERATOR_CALIBRATED_LOCAL_MODE_GUIDE_2026-07-29.md`
10. `docs/DEPTH_LOCAL_MVP_OPERATOR_GUIDE_2026-07-29.md`
11. `docs/examples/operator_depth_polygons.example.geojson`
12. `docs/examples/operator_depth_config.example.json`
13. `docs/examples/operator_depth_candidates.example.json`

### D. Tyrone scientific boundary and failed automatic routes

14. `docs/DEPTH_OPTION1_TYRONE_3X_TEST_PLOTS_5_6_DECISIVE_RESULT_2026-07-29.md`
15. `docs/DEPTH_LOCAL_MVP_TYRONE_ELECTRONIC_FILES_RECOVERY_RESULT_2026-07-29.md`
16. `docs/DEPTH_LOCAL_MVP_TYRONE_MULTI_PLACEMENT_SENSITIVITY_RESULT_2026-07-29.md`
17. `docs/DEPTH_LOCAL_MVP_TYRONE_PUBLIC_RTC_SENSITIVITY_RESULT_2026-07-29.md`
18. `docs/DEPTH_LOCAL_MVP_TYRONE_TP56_PROVISIONAL_RTC_RESULT_2026-07-29.md`
19. `docs/DEPTH_LOCAL_MVP_TYRONE_VH_RELATIVE_HOLDOUT_RESULT_2026-07-29.md`
20. `docs/DEPTH_LOCAL_MVP_TYRONE_VH_DEPTH_BAND_FRESH_HOLDOUT_RESULT_2026-07-29.md`

Read the matching JSON records when exact counts or machine-readable decisions are needed.

### E. Strategy history — context only

21. `docs/DEPTH_FEASIBLE_LOCAL_MVP_PLAN_2026-07-29.md`
22. `docs/DEPTH_ACTIVE_STRATEGY_LOCK_2026-07-29.md`
23. `docs/OPTION1_OPTION5_COMBINED_PLAN_START_2026-07-28.md`
24. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-29_V3_STRATEGY_CORRECTION.md`

The older strategy files explain how the project arrived here. They do not override this V4 handoff.

### F. Historical candidate archive

Read individual candidate result files only when reopening that exact candidate or auditing the broad search.

Do not reread the full archive before the first local-AOI run.

---

## Do not do list

The next session must not:

- restart a broad worldwide candidate search as the immediate priority;
- describe Option 5 as depth;
- enable local depth globally by default;
- use classifier or PCA anomaly values as measured depth;
- reuse the failed Tyrone thresholds on the same holdout data;
- treat approximate Tyrone polygons as official survey geometry;
- extrapolate outside local anchor support;
- combine anchors from different sites without a new approved scientific plan;
- expose private geometry, coordinates or filesystem paths in public API responses;
- check Gmail or contact the agency without explicit user authorization;
- stop work without stating current status and exact next step.

---

## Exact next step for the next session

Start by asking for or locating the user's first real same-site anchor-and-candidate GeoJSON.

If the user already has the file:

1. restart the app;
2. upload it;
3. pass preflight;
4. run the local calibration;
5. document the result.

If the user does not have the file:

The next task is not another global web search. Help the user create the file from their own measured survey or construction records:

- identify at least two measured anchor areas;
- capture the minimum, best and maximum depth for each;
- draw reviewed conservative polygons;
- add the candidate area;
- pass the app preflight.

No genuine unknown-candidate depth result is possible until those same-site measured anchors exist.

---

## Final handoff status

```text
operator_calibrated_local_aoi_ready = true
in_app_local_depth_panel_ready = true
first_aoi_template_ready = true
strict_preflight_ready = true
automatic_signal_extraction_ready = true
local_no_extrapolation_ready = true
first_real_aoi_run_completed = false
real_anchor_geojson_available = false
tyrone_continuous_depth_ready = false
tyrone_automatic_depth_band_ready = false
global_depth_ready = false
global_calibration_rows = 0
option_5_active_not_depth = true
option_3_active = false
app_depth_enabled_by_default = false
```

**Current status:** GOOD TO GO for a real operator-calibrated local AOI run once the measured anchor GeoJSON is supplied.

**Missing item:** real same-site measured anchors and reviewed polygons.

**Exact next step:** prepare or upload that GeoJSON, require preflight to pass, and execute the first in-app local calibration.

**User action required:** yes — provide the measured local anchor depths and polygons, unless those records are already available in the project files.
