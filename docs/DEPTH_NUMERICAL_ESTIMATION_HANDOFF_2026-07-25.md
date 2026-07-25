# Numerical Depth Estimation — Session Handoff — 2026-07-25

**Repository:** `max2026-lab/New_GEE`  
**Branch:** `main`  
**Status:** numerical-depth evidence acquisition in progress; no calibration row or depth model is approved  
**Read this file before continuing any depth work.**

## 1. Goal

Unlock a defensible numerical **depth range to the top of a buried reference feature**, with uncertainty and untouched-site validation.

The project must not output a guessed exact number. Numerical app output remains disabled until the evidence pack, relative-depth gate, and numerical holdout gates pass.

## 2. Current point reached

```text
Buto Sentinel-1 spatial method test = successful
repeatable radar difference = supported
depth measured by Sentinel-1 = no
eligible positive calibration rows = 0
eligible negative calibration rows = 0
relative-depth training ready = no
numerical depth-range training ready = no
app depth output enabled = no
```

The active public-record route has produced three strong evidence tracks:

1. **Elk Plain County Shop** — strongest measured positive-depth map.
2. **Sudbury Road Landfill** — strongest bounded minimum-depth evidence with public numerical construction controls.
3. **Go East Corp Landfill** — strongest independently confirmed no-target evidence.

None is yet a complete eligible calibration package.

## 3. What is already proven

### 3.1 Buto method test

The real Earth Engine query completed successfully for the published Sentinel-1 date.

```text
exact_date_acquisition_count = 1
same_orbit_support_count = 11
support_acquisition_count = 36
stable_signal_features = 4 of 4
spatial_agreement_decision = spatial_agreement_supported
status = method_screen_complete_spatial_comparison_only
```

Correct interpretation:

```text
repeatable spatial radar difference = yes
numerical depth relationship = not proven
calibration record = not created
```

The Buto geometry used for the method test was approximate and local. The comparison area was not independently confirmed empty. Coordinate-bearing files remain outside Git.

### 3.2 Elk Plain positive-depth evidence

Official records establish:

- contaminated soil was consolidated and capped in August 2023;
- the cap is six feet of compacted clean soil over a warning layer;
- an as-built comparison map contains measured top-to-top thickness values;
- mapped values are approximately `6.00` to `11.08 ft`;
- Ecology accepted the submitted thickness figure;
- the capped parcel is approximately `5.31 acres`;
- no further site-characterization work or anticipated site changes were reported through December 2025;
- Pierce County Record of Survey `202502055001` exists.

Still missing:

- numerical vertical survey accuracy or an accepted uncertainty bound;
- independently confirmed no-target comparison geometry;
- final Sentinel-1 observation dates that avoid construction and early surface change.

Do not infer uncertainty from values displayed to hundredths of a foot. The cap map is marked `REVIEW SET`.

### 3.3 Sudbury bounded minimum-depth evidence

Official records establish:

- completed covers over Areas 2 and 5 used at least `4.8 ft` (`1.46304 m`) of soil;
- both subgrade and finish grade were surveyed by a Professional Land Surveyor;
- digital terrain models were compared;
- test pits cross-checked the minimum cover;
- final surveys used at least a 50-foot grid;
- published stake-setting controls include values around `±0.025 ft` (`±0.00762 m`);
- the cover/finish-grade quality table lists a one-sided `-0.10 ft to 0 ft` requirement on a 100-foot grid.

Correct interpretation:

```text
actual constructed minimum depth = supported
numerical construction-control evidence = supported
final per-footprint depth uncertainty = not assigned
```

The stake tolerance is not the total final depth uncertainty. It does not include construction variability, surface-model interpolation, settlement, or satellite-footprint aggregation.

Still missing:

- certified as-built surface values mapped to Areas 2 and 5;
- confirmation of the exact meaning of the `-0.10 ft to 0 ft` table entry from the visual table;
- an independently confirmed no-target comparison footprint;
- a verified unchanged Sentinel-1 observation window.

### 3.4 Go East confirmed-negative evidence

The official quality-assurance and completion records support two physically checked no-target or cleared areas in one physical site group:

**Area A — southeast lot exploration**

- the approved plan required an investigation outside the landfill;
- its purpose was to determine whether buried landfill material was present;
- no buried landfill material was observed;
- government oversight agencies reviewed the confirmation.

**Area B — cleared wedge area**

- landfill material was excavated from around the former landfill edge;
- only native soil remained at the base and distal sidewalls;
- environmental professionals collected confirmation samples;
- 59 samples and 9 resamples were reported;
- initial exceedance areas were over-excavated and resampled.

These are stronger than analyst-selected background polygons. They belong to one Go East physical group and cannot be split between train, validation, and holdout.

Still missing:

- exact private geometry from plan sheet 4, the Lot Exploration Plan appendix, and record drawings;
- stable post-work Sentinel-1 timing;
- numerical positive-depth uncertainty and exact cover thickness values.

Go East may provide an eligible negative before it provides an eligible positive.

## 4. Other retained holds

- **Recomp of Washington:** an actual two-foot compacted clay cover is documented, but later geomembrane, soil, asphalt, and operations heavily confound Sentinel-1 timing.
- **RAMCO:** a final cover and named as-built drawings exist, but measured thickness, uncertainty, comparison evidence, and stable timing remain unverified.
- **Triune Mine:** completion/as-built records exist, but it is a fallback because measured clean-soil thickness and uncertainty remain missing.

Do not open a generic candidate search. Continue only with the named records below.

## 5. How this work was performed

The next session must keep the same method.

1. **Explain plainly.** Do not assume the project owner understands Git, Earth Engine, PDFs, survey terminology, or command-line tools.
2. **One bounded task at a time.** State what is being checked, why it matters, and what the next step is.
3. **Use named official records only.** Broad candidate searching is stopped.
4. **Reject false precision.** A design minimum, displayed decimal, survey stake tolerance, or radar anomaly is not automatically an exact depth label.
5. **Require independent evidence.** Notebook outputs, PCA anomaly scores, target masks, radar classifications, and satellite-selected quiet areas cannot become calibration truth.
6. **Keep geometry private.** Exact coordinates, survey surfaces, and coordinate-bearing GeoJSON files remain outside Git and should not be printed in chat.
7. **Do not perform outreach automatically.** The owner does not need to email anyone during the current bounded public-document phase.
8. **Use the first unrecoverable gate.** For each named file, stop that path when it cannot provide measured values, uncertainty, mapped comparison evidence, or usable timing.
9. **Repository writes:** fetch an existing file first, update it with its current blob SHA, and fetch again to verify. New files may be created directly on `main` under the established workflow.
10. **Testing claims:** never claim tests ran unless they actually ran. The Buto focused unit tests passed locally earlier; the full repository suite was not run for the public-record documentation updates.
11. **No numerical model fitting yet.** Do not create calibration rows merely to satisfy the validator.

## 6. Required reading order

The next session should read these files in order before doing any new work.

### Read first — authority and active plan

1. `docs/DEPTH_NUMERICAL_ESTIMATION_HANDOFF_2026-07-25.md`
2. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md`
3. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md`
4. `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
5. `templates/depth_calibration/README.md`

### Read next — current evidence state

6. `docs/DEPTH_PUBLIC_ENGINEERING_PACKAGE_SCREEN_2026-07-24.md`
7. `docs/DEPTH_GO_EAST_CONFIRMED_NEGATIVE_EVIDENCE_UPDATE_2026-07-25.md`
8. `docs/DEPTH_SUDBURY_NUMERICAL_CONTROL_EVIDENCE_UPDATE_2026-07-25.md`
9. `docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md`
10. `docs/DEPTH_BUTO_METHOD_TEST_EXECUTION_PLAN_2026-07-24.md`
11. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md`
12. `docs/DEPTH_BLOCKER_2_STAGE1_SCREENING_RESULTS_2026-07-23.md`
13. `docs/DEPTH_BLOCKER_2_PRIVATE_DIRECT_DATA_ROUTE_2026-07-23.md`

### Read before intake, validation, or app changes

14. `scripts/init_depth_calibration_pack.py`
15. `scripts/add_depth_calibration_record.py`
16. `scripts/validate_depth_calibration_pack.py`
17. `scripts/finalize_depth_calibration_manifest.py`
18. `scripts/run_buto_s1_method_screen.py`
19. `tests/unit/test_buto_s1_method_screen.py`
20. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`

## 7. Uploaded notebook context

Two uploaded files were available in the project session:

- `notebook phases.md`
- `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb`

The phase inventory describes a very large older notebook containing many radar, PCA, object-extraction, classifier, KMZ, and depth-named proxy stages. It is useful for locating legacy capability, but its treasure-, metal-, burial-, or depth-named outputs must not be treated as independent calibration truth.

The uploaded candidate-scout notebook is supplementary context and is not the Buto numerical-depth experiment. Do not replace the current evidence contract with notebook labels or predictions.

## 8. Immediate next steps

### Roadmap A — finish the three active document paths

1. **Go East:** retrieve approved plan sheet 4, the Lot Exploration Plan appendix, and record drawings. Extract the southeast negative boundary and cleared-wedge boundary into private geometry outside Git. Check record drawings for exact cover elevations and survey notes.
2. **Elk Plain:** retrieve Pierce County Record of Survey `202502055001`. Look only for vertical datum, control monuments, closure, survey class, stated accuracy, or another defensible numerical bound tied to the cap survey.
3. **Sudbury:** retrieve Construction Quality Assurance Certification Report `64264` and certified as-built drawings. Recover the mapped subgrade/finish-grade values or thickness surface for Areas 2 and 5. Inspect the original visual table in document `53360` to confirm what the `-0.10 ft to 0 ft` requirement controls.

Do not move to RAMCO, Recomp, or Triune until these three paths have reached a clear decision.

### Roadmap B — create private candidate records only after geometry is recovered

For each candidate record, determine:

```text
reference_status
known_depth_top_m or bounded minimum
depth_reference_uncertainty_m or supported interval
depth_reference_method
evidence references
observation dates
site_id, feature_id, group_id
include_for_relative_depth
include_for_numerical_depth
exclusion_reason
```

Coordinate-bearing source material and candidate rows must remain outside Git.

### Roadmap C — reach the minimum split structure

The technical floor is:

```text
train:      1 eligible positive + 1 eligible negative
validation: 1 eligible positive + 1 eligible negative
holdout:    1 eligible positive + 1 eligible negative
```

All three groups must be physically independent. Two Go East negative areas still count as one physical group.

The six-record floor proves only that the contract can run. It does not prove that a reliable depth model exists.

### Roadmap D — model gates after evidence exists

1. Populate the private pack.
2. Run the aggregate validator.
3. Freeze train, validation, and untouched holdout groups.
4. Extract neutral, non-circular Sentinel-1/context features only.
5. Pass relative-depth baselines first.
6. Fit numerical median, robust-linear, and quantile-range baselines only after the relative gate passes.
7. Preserve reference uncertainty and test interval coverage on untouched sites.
8. Return `insufficient_data` for unsupported cases.
9. Enable app depth output only after numerical holdout gates pass.

## 9. Stop rules

Do not:

- restart broad web searching;
- use Buto's repeatable anomaly as a depth label;
- use the approximate Buto polygon as survey truth;
- treat a minimum construction requirement as an exact measured value;
- treat stake-setting tolerance as total final depth uncertainty;
- select a nearby quiet radar area and call it confirmed negative;
- reuse one site across train, validation, and holdout;
- copy exact coordinates into Git or chat;
- train a numerical model before eligible records exist;
- enable app depth output prematurely.

## 10. Latest documentation commits

```text
704e4cc829d46829ffeb4c3dec64ee2152cab2fd  docs: record Sudbury numerical control evidence
65573b7761ae96d88fec202b52cf1e630fd129e5  docs: record Go East confirmed-negative evidence
376b4761e8254bb64b8bea2957e01b8c0c0e160e  docs: strengthen Sudbury constructed-depth evidence
eb9d297fed22ae8aaa8cb0fe5cd571f3317dfa37  docs: record Go East confirmed-no-target lead
```

Earlier Buto implementation/result commits are documented in the Buto plan and result files.

## 11. Exact next-session starting instruction

```text
Read docs/DEPTH_NUMERICAL_ESTIMATION_HANDOFF_2026-07-25.md and every file in its required reading order. Do not restart broad candidate search. Continue the bounded official-document retrieval in this order: Go East plan sheet 4 and record drawings, Elk Plain Record of Survey 202502055001, then Sudbury certified as-built report 64264 and the original visual tolerance table in document 53360. Keep coordinates outside Git. Report one plain-English decision after each document path: usable evidence found, hold missing one specific item, or reject at the first unrecoverable gate.
```

## 12. One-sentence handoff

The project now has a successful Buto radar-method result, a strong measured positive map at Elk Plain, a bounded minimum-depth and numerical-control lead at Sudbury, and two physically confirmed negative areas at Go East, but exact private geometry, final uncertainty, clean observation timing, and three independent split groups are still required before any numerical depth-range model can be trained or shown in the app.
