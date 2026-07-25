# Numerical Depth Estimation — Session Handoff — 2026-07-25

**Branch:** `main`  
**Goal:** unlock honest numerical depth estimation using real independent calibration evidence  
**Current result:** important progress, but numerical training is still blocked  
**Broad generic search:** stopped  
**Calibration records created:** 0  
**App numerical depth enabled:** no

---

## 1. Read these documents first — in this order

The next session must read these before searching, coding, or proposing a new plan:

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-25.md` — this handoff.
2. `docs/DEPTH_NUMERICAL_UNLOCK_EXECUTION_PLAN_2026-07-24.md` — required evidence and overall unlock path.
3. `docs/DEPTH_PUBLIC_ENGINEERING_PACKAGE_SCREEN_2026-07-24.md` — current ranked site screen and missing evidence.
4. `docs/DEPTH_SUDBURY_NUMERICAL_CONTROL_EVIDENCE_UPDATE_2026-07-25.md` — Sudbury numerical tolerance evidence and limits.
5. `docs/DEPTH_GO_EAST_CONFIRMED_NEGATIVE_EVIDENCE_2026-07-25.md` — Go East physically checked empty-area evidence.
6. `docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md` — successful Buto spatial method test and its limits.
7. `docs/DEPTH_BUTO_METHOD_TEST_EXECUTION_PLAN_2026-07-24.md` — completed Buto execution record.
8. `docs/DEPTH_BLOCKER_2_KNOWN_DATA_SOURCE_SCREENING_2026-07-24.md` — previously screened and rejected sources.
9. `docs/DEPTH_CURRENT_BLOCKER_AND_EVIDENCE_NEEDED_2026-07-23.md` — blocker definition.
10. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md` — depth-output architecture and gating.
11. `scripts/validate_depth_calibration_pack.py` — exact validator rules.
12. `scripts/run_buto_s1_method_screen.py` and `tests/unit/test_buto_s1_method_screen.py` — completed method-screen implementation.
13. The notebook phase inventory supplied for the original notebook — especially the Sentinel-1 pipeline, PCA anomaly/object extraction, classifier, training, and depth-related cells. Treat notebook depth and target labels as unvalidated until supported by independent calibration evidence.

Do not rely on chat memory instead of reading these files.

---

## 2. Plain-English goal

The user wants the app to output a numerical depth.

To do that honestly, the project needs real examples where all of the following are independently known:

- exact mapped target area;
- measured depth or installed thickness;
- numerical accuracy, tolerance, or uncertainty;
- construction and observation dates;
- independently confirmed no-target comparison area;
- independent train, validation, and holdout site groups.

The project cannot infer metres from a radar anomaly alone. Sentinel-1 differences may support spatial discrimination, but depth requires calibration against real measured sites.

---

## 3. How this session worked

The working method was intentionally narrow and evidence-first:

1. **No broad generic searching.**
2. Start from named official engineering packages already identified.
3. Search only for the exact missing document or missing field.
4. Prefer regulator, government, certified engineering, survey, construction-quality, and as-built records.
5. Separate facts into:
   - actual measured/installed evidence;
   - design minimums;
   - construction tolerances;
   - final measurement uncertainty;
   - confirmed negative evidence;
   - analyst-selected background areas.
6. Never treat a design value as an as-built measurement.
7. Never treat displayed decimal precision as measurement accuracy.
8. Never treat a construction-control tolerance as automatically equal to full final depth uncertainty.
9. Never create a calibration row until all validator-required evidence exists.
10. Document each meaningful upgrade in `main` immediately.
11. Keep the user’s role minimal; the user was not asked to email authors or manually search records.
12. Use simple status language:
   - good lead;
   - not ready;
   - exact missing item;
   - next bounded action.

This method must continue.

---

## 4. Work completed

### 4.1 Buto method test completed successfully

The local Earth Engine execution completed with:

```text
query_executed = true
exact_date_acquisition_count = 1
same_orbit_support_count = 11
signal_feature_count = 4
stable_feature_count = 4
spatial_agreement_decision = spatial_agreement_supported
status = method_screen_complete_spatial_comparison_only
```

Correct interpretation:

```text
spatial radar anomaly supported = yes
repeatable on supporting acquisitions = yes
numerical depth measured = no
training started = no
app depth enabled = no
```

Buto remains method evidence only because its polygon is approximate, its comparison area is not independently confirmed empty, and it lacks complete numerical uncertainty and multi-site split evidence.

### 4.2 Public engineering search narrowed to six serious leads

Current ranking:

```text
1. Elk Plain — strongest measured as-built positive-depth map
2. Sudbury — strongest professionally surveyed and cross-checked constructed minimum
3. Go East — strongest independently confirmed no-target lead
4. Recomp — documented installed depth but heavily confounded
5. RAMCO — alternate named as-built package
6. Triune — fallback
```

No other generic candidates should be opened unless all stronger named paths are exhausted and documented as dead.

---

## 5. Exact point reached

### 5.1 Elk Plain County Shop

Strongest positive-depth map.

Established:

- capped in August 2023;
- six feet of compacted clean soil over an orange warning layer;
- official before/after survey comparison map;
- many mapped thickness values, approximately 6.00 to 11.08 feet;
- Ecology accepted the cap survey figure;
- capped parcel is separately mapped, approximately 5.31 acres;
- no reported site changes through December 2025;
- Pierce County Record of Survey `202502055001` exists;
- environmental covenant and long-term inspection controls exist.

Still missing:

- numerical vertical survey accuracy or defensible uncertainty;
- independently confirmed no-target comparison footprint;
- final Sentinel-1 observation window outside construction and early vegetation establishment.

Current decision:

```text
positive depth evidence = strong
survey uncertainty = missing
confirmed negative = missing
calibration row = not allowed
```

### 5.2 Sudbury Road Landfill

Strongest bounded minimum-depth evidence.

Established:

- construction completed in 2017;
- Areas 2 and 5 received evapotranspiration covers;
- completed cover checked against a 4.8-foot minimum;
- subgrade and finish grade surveyed by a Professional Land Surveyor;
- digital terrain models compared;
- test pits checked cover thickness over waste;
- final engineer reviewed and verified as-built drawings;
- final survey requirement on at least a 50-foot grid;
- stake-setting vertical control approximately `±0.025 ft` (`±0.00762 m`);
- cover/finish-grade requirement checked on a 100-foot grid with a listed `-0.10 to 0 ft` control range.

Critical interpretation:

- `4.8 ft` is a verified constructed minimum, not a defensible exact value for every satellite footprint.
- `±0.025 ft` is survey staking/control evidence, not automatically the full final depth uncertainty.
- the `-0.10 to 0 ft` requirement is a construction acceptance bound, not automatically a complete statistical uncertainty model.

Still missing:

- certified final mapped thickness surface or per-area values;
- defensible final uncertainty assignment;
- independently confirmed no-target comparison area;
- unchanged Sentinel-1 observation window.

Current decision:

```text
measured minimum depth = yes
numerical control evidence = yes
exact mapped depth surface = missing
confirmed negative = missing
calibration row = not allowed
```

### 5.3 Go East Corp Landfill

Strongest confirmed-negative route.

Established:

- closure construction ran March 2021 through July 2022;
- landfill footprint reduced from about 10 acres to about 6 acres;
- licensed surveyors produced layout, limit, and as-built survey records;
- final cover required a geomembrane with at least two feet of soil;
- engineers and geotechnical staff observed, tested, and certified construction;
- official record drawings and construction summary exist;
- government-reviewed lot exploration outside the landfill specifically checked for buried landfill material and found none;
- a second excavated wedge area was also described as containing native soil after landfill material removal.

Important distinction:

- Go East contains one site group with two physically checked empty-area leads.
- These are not two independent train/validation/holdout groups.

Still missing:

- exact mapped footprint from approved plan sheet 4 / Lot Exploration Plan appendix;
- exact mapped footprint for the wedge/native-soil area;
- actual as-built positive cover-thickness surface;
- numerical survey accuracy;
- clean Sentinel-1 timing unaffected by roads, drainage, recreation, residential work, vegetation, or other later surface changes.

Current decision:

```text
confirmed no-target evidence = yes
confirmed no-target footprint extracted = no
positive exact depth = no
negative calibration row = not allowed yet
```

### 5.4 Recomp

Established actual two-foot compacted clay cover, approved by the 1989 deadline.

Later construction added an HDPE geomembrane, 18 inches of compacted native soil, and four inches of asphalt.

Still missing:

- mapped clay-layer as-built boundary;
- uncertainty/tolerance;
- confirmed negative;
- clean observation period unaffected by later construction.

Keep only as a weaker hold.

### 5.5 RAMCO

Official as-built drawings exist and cleanup/cover work was completed.

Still missing actual measured thickness, uncertainty, confirmed negative, and clean observation timing.

Keep only as alternate.

### 5.6 Triune Mine

Completion/as-built report exists, but actual cover thickness, uncertainty, confirmed negative, and observation timing remain missing.

Fallback only.

---

## 6. Current blocker

No site package yet contains all of the following together:

```text
mapped positive depth evidence
+ numerical uncertainty
+ mapped confirmed no-target evidence
+ clean observation timing
+ independent split eligibility
```

Current readiness:

```text
calibration_records_created = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

Do not start training. Do not enable depth in the app. Do not create placeholder or approximate calibration rows.

---

## 7. Immediate next steps

Continue only with these exact records, in this order:

### Step 1 — Go East mapped negative footprint

Retrieve and inspect:

- approved plan sheet 4;
- Lot Exploration Plan Report / appendix;
- record drawings;
- construction summary.

Goal:

- extract the exact government-checked no-target polygon;
- identify observation/exploration dates;
- confirm later surface changes;
- determine whether the negative area is usable for Sentinel-1.

Stop condition:

- if the footprint cannot be mapped or the area was materially altered before usable Sentinel-1 dates, retain as evidence-only and do not create a row.

### Step 2 — Elk Plain numerical uncertainty

Retrieve and inspect:

- Pierce County Record of Survey `202502055001`;
- survey-control notes;
- title block, basis of bearing, vertical datum, equipment, closure statement, or accuracy certification;
- Ecology feedback on the cap-thickness map;
- cap inspection records.

Goal:

- obtain a source-supported vertical accuracy or bounded uncertainty;
- determine whether the mapped 6.00–11.08-foot values can become depth labels;
- identify a physically confirmed comparison area.

### Step 3 — Sudbury certified as-built surface

Retrieve and inspect:

- certified as-built drawings;
- final construction-quality certification report;
- subgrade and finish-grade surfaces;
- thickness map/table;
- surveyor certification and final tolerance statement.

Goal:

- recover exact mapped thickness values for Areas 2 and 5;
- assign a defensible bounded uncertainty without misusing the staking tolerance;
- locate any independently verified waste-free or native-soil comparison area.

### Step 4 — Only after one complete site package

When one site has complete positive and negative records:

1. create candidate calibration rows privately;
2. run `scripts/validate_depth_calibration_pack.py`;
3. record every validator failure;
4. do not weaken validator requirements;
5. continue until three independent site groups can fill train, validation, and holdout.

---

## 8. Short roadmap

### Roadmap A — Evidence completion

```text
Go East mapped negative
→ Elk Plain uncertainty
→ Sudbury exact mapped depth
→ complete first site package
```

### Roadmap B — Dataset readiness

```text
complete site group 1
→ complete site group 2
→ complete site group 3
→ assign train / validation / holdout with no group reuse
```

### Roadmap C — Numerical research

```text
validator passes
→ extract matched Sentinel-1 features
→ test whether radar features correlate with known depth
→ validate on separate site
→ test on untouched holdout
```

### Roadmap D — App output

```text
only after successful holdout
→ define depth ranges and uncertainty
→ add guarded research output
→ keep exact-metre claims blocked unless supported
```

The first numerical output should probably be a bounded depth interval or depth class, not a falsely precise single metre value.

---

## 9. Rules for the next session

1. Read all listed documents first.
2. Do not restart broad candidate search.
3. Do not repeat Buto method testing.
4. Do not ask the user to email authors unless all public-record paths are exhausted and the user explicitly agrees.
5. Do not send email.
6. Do not claim depth is unlocked until the validator and independent holdout support it.
7. Do not use approximate polygons as calibration truth.
8. Do not treat a nearby area as negative unless independent physical or authoritative records confirm it.
9. Do not count multiple areas from one site as independent split groups.
10. Keep responses plain, brief, and explicit:
    - what was found;
    - whether it is good to go;
    - what is missing;
    - what happens next.
11. Commit every meaningful evidence upgrade to `main`.
12. State clearly when a document server or portal blocks retrieval; then try official mirrors, indexed text, county recording systems, or exact named-document searches before abandoning the path.
13. Never expose private credentials, private paths, exact sensitive coordinates, or secret material.
14. Never ask the user to paste Earth Engine credentials.

---

## 10. Important repository commits from this work

Known commits created during this sequence include:

```text
ccc23ab docs: record successful Buto Sentinel-1 method result
f93814f docs: close Buto method test execution
bab10b4 docs: define numerical depth unlock execution plan
b324b626 docs: add Go East engineering package hold
b1b2f990 docs: strengthen Recomp engineering evidence
376b476 docs: strengthen Sudbury constructed-depth evidence
704e4cc docs: record Sudbury numerical control evidence
```

The next session should verify current `main` before relying on commit IDs.

---

## 11. One-sentence handoff

Continue the bounded official-document retrieval with Go East plan sheet 4 first, then Elk Plain survey `202502055001`, then Sudbury certified as-builts; create no calibration rows and start no training until mapped depth, uncertainty, confirmed negative evidence, clean timing, and independent site splits are all supported.