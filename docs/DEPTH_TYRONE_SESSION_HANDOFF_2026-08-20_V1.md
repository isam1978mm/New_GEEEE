# Tyrone numerical-depth session handoff — 2026-08-20

## Purpose

This handoff records the exact state of the Tyrone numerical-depth work at the end of the 2026-08-20 session so the next session can continue without repeating closed searches or weakening the scientific safeguards.

## User constraints that must be preserved

- Do not change the classifier.
- Do not change unrelated UI.
- Do not change the NB formula.
- Do not enable `operator_scalar_interpolation_v1`.
- Do not fit/tune to known Tyrone depth answers.
- Always distinguish:
  - recorded measured depth;
  - calibrated/estimated depth;
  - raw proxy / surface-change output.
- Main local backend remains port `8007`; do not use port `8000`.
- Current user instruction for this route: **no more email requests and no payment unless the user explicitly approves it.**
- Do not spend money, submit an order, or move toward payment without explicit approval.
- Do not restart random satellite-feature hunting for metres.

## Big-picture status

There are now two very different depth capabilities:

1. **Recorded-depth lookup for reviewed zones:** implemented and safe. It reports existing measurements only for exact reviewed zone IDs and does not predict unknown depth.
2. **General numerical depth estimation for unknown zones:** still blocked. No tested free physical route currently meets the frozen accuracy gate.

This distinction must remain explicit in all UI/docs/operator language.

---

# What this session did

## Step 0 — inspect existing 3X plates for direct subgrade + final-grade profiles

Files inspected included the available 3X CQAR/as-built plates such as:

- `3X_CQAR_010_R0.pdf`
- `3X_CQAR_004_R0.pdf`
- `3X_CQAR_006_007_R0.pdf`

Goal: find a section/profile containing both pre-cover/subgrade and final surface on the same section so cover thickness could be read directly.

Result: **no decisive direct pre-cover + final profile was found.** The plates remain useful for as-built geometry, plot locations, test pits, contours and final/as-built information, but they did not solve pre-cover thickness directly.

## Step 1 — establish the historical timing gate

Evidence established:

- tailings deposition at 3X had stopped long before reclamation;
- an official February 2004 Tyrone aerial image exists;
- 3X reclamation began in September 2004;
- however, reclamation included substantial top-surface/outslope grading, drainage work and cover-subbase placement.

Important correction to the simple formula:

`final ground - old historical terrain` is **not automatically cover depth**.

The historical surface must represent the verified immediate pre-cover/post-grading substrate, or grading/excavation/fill confounds must be controlled.

This is why the 1996 NAPP surface cannot simply be called the pre-cover surface.

## Step 2 — 2008 as-built vs 2018 lidar final-surface QA

Temporary research PR #109 was used and closed without merge.

Result:

- the official 2018 USGS 1 m DEM/lidar product covering 3X was downloaded and cropped;
- approximate 2018 top-surface medians:
  - TP5 ~5530.12 ft
  - TP6 ~5528.12 ft
  - TP7 ~5529.04 ft
- registered 2008 as-built contours and 2018 DEM showed the same major 5520/5530 ft terrain pattern;
- clear spot checks were roughly 0.2–0.7 m apart, with PDF digitization/datum/real change all mixed together.

Decision:

- **2018 lidar/DEM remains the preferred final/current surface candidate.**
- This comparison is sufficient to reject a large multi-metre post-2008 shift.
- It is **not** accurate enough to claim precise settlement.

## Step 3 — historical stereo inventory

USGS EarthExplorer/USDA NAPP search identified a real 1996 stereo triplet over Tyrone:

- `NP0NAPP009519108`
- `NP0NAPP009519109`
- `NP0NAPP009519110`
- acquisition: 1996-09-28
- roll: 9519
- camera: 124257
- lens: 124308
- calibrated focal length: 152.773 mm

Camera calibration report `R2104.PDF` was downloaded and verified as the correct calibration for the triplet.

The user uploaded the three free medium-resolution TIFFs into:

- `data/research/tyrone_napp_1996/Desktop.7z.001`
- `data/research/tyrone_napp_1996/Desktop.7z.002`
- `data/research/tyrone_napp_1996/Desktop.7z.003`

The split archive passed integrity checking and contained all three TIFFs.

Also checked:

- free 2004 NAIP over Tyrone before September 2004: **zero scenes found**;
- public 2007 Appendix A design drawings: **3X not present in that drawing set**.

EarthExplorer on-demand scan option:

- 14 micron scan is available;
- price shown was $30/frame;
- **not approved by user**;
- do not order/pay unless the user explicitly approves later.

## Step 4 — freeze the scientific accuracy gate before reconstruction

PR #111 merged the frozen rules.

Historical-surface gate includes:

- `RMSEz <= 0.15 m`
- `abs(median vertical residual) <= 0.05 m`
- 95th percentile absolute vertical residual `<= 0.30 m`
- residual-plane drift across 3X `<= 0.10 m`

Independent depth-validation gate includes:

- `MAE <= 0.10 m`
- `RMSE <= 0.15 m`

Do not relax these thresholds after seeing results.

Do not co-register on the Tyrone depth plots/test pits used as validation truth.

## Step 5 — desk scan-resolution screen

PR #111 also documented the desk error budget.

Initial rule:

- 63 micron: rejected as too coarse for numerical-depth production;
- 25 micron: first desirable free target;
- 14 micron: stronger paid fallback, but purchase requires explicit approval.

EarthExplorer only provided the existing free **Medium Resolution** product for these frames, corresponding to the coarse scan, plus the paid 14 micron on-demand option.

## Free medium-resolution stereo pre-depth experiment

Even though the desk screen already said the medium scan was too coarse for depth, it was tested only as a **free pre-depth feasibility check**, with all known Tyrone depth answers kept out of the process.

Temporary PRs used only for research and closed without merge:

- #114 archive integrity check
- #115 TIFF/stereo preflight
- #116 R2104/fiducial/interior-orientation work

Results:

- the three photos are genuine overlapping stereo imagery;
- adjacent frames produced thousands of geometrically consistent matches;
- after R2104-based normalization, held-out epipolar error was about:
  - median `0.246 px`
  - 95th percentile `0.977 px`
- dense sub-pixel disparity agreement was about:
  - median `~0.21–0.23 px`
  - 95th percentile `~0.77–0.80 px`

So image matching itself worked.

Fatal test:

Two independent 1996 terrain surfaces were reconstructed from:

1. frames 108+109
2. frames 109+110

After aligning on independent historical terrain/control logic, held-out vertical repeatability was approximately:

| Patch size | Median absolute disagreement | Held-out RMSE |
|---:|---:|---:|
| 40 m | 1.96 m | 3.55 m |
| 60 m | 1.66 m | 4.04 m |
| 80 m | 1.56 m | 3.81 m |
| 100 m | 1.79 m | 3.17 m |
| 120 m | 2.15 m | 2.73 m |
| 200 m | 1.44 m | 3.44 m |

This is metres, while the frozen gate is 0.15 m RMSE.

Decision:

**Free medium-resolution 1996 NAPP stereo is CLOSED for numerical depth.**

This closure happened before using TP5/TP6/TP7 or the 43 test-pit depth answers.

PR #117 permanently documents this result.

## Free public search for the actual 2004 engineering/pre-cover surface

The public-web search then focused only on exact relevant documents and native survey/grade-control outputs.

Confirmed to exist historically:

1. **M3, June 2004 Basic Engineering Report — Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report.**
2. **Tetra Tech, June 2004 — Cover design report: 3X tailings impoundment.**
3. **M3 2008 3X Construction Quality Assurance Report / facility CQAR.**

Strong construction evidence also shows:

- D8R dozers used for major regrading;
- 14H motor grader used for final grading;
- **Computer Aided Earthmoving System (CAES)** used for grade control/equipment operations;
- CAES complemented by **conventional GPS surveys**.

Therefore a precise digital grading/survey data trail almost certainly existed during construction.

However, the public search did **not** find a downloadable copy of:

- the June 2004 M3 BER itself;
- the June 2004 Tetra Tech cover-design report itself;
- the facility-wide 2008 3X CQAR itself;
- native CAES terrain/model;
- pre-cover/post-grading CAD/TIN/grid;
- GPS/CAES point/surface export suitable for reconstructing the immediate pre-cover substrate.

Decision:

**Under the current free / no-email / no-payment constraint, the public-web 2004 pre-cover-surface search is exhausted for now.**

PR #118 documents the closure.

Do not repeat the same BER/CQAR title searches unless a genuinely new archive/source appears.

---

# Important parallel result — Route A is now implemented

PR #119 — `Add reviewed recorded-depth lookup without prediction` — is merged to `main`.

Merge commit:

- `b18cc11980cbf72c91c2153935eee6c67f360cac`

What it does:

- introduces a safe additive **recorded-depth lookup** path;
- exact reviewed zone IDs only;
- output status is `recorded_measurement`;
- dedicated recorded/provenance fields carry the known measurement;
- `estimated_depth_*` remains blank for recorded rows;
- unknown zones abstain and emit no metres;
- no interpolation or extrapolation;
- recorded measurements do not depend on satellite run-quality status;
- existing calibrated/interpolation paths remain separate;
- classifier untouched;
- UI untouched.

Main files added/changed by PR #119:

- `app/pipeline/depth/recorded.py`
- `app/pipeline/depth/loader.py`
- `app/pipeline/depth/schema.py`
- `app/pipeline/stages/depth_estimation.py`
- `scripts/build_tyrone_recorded_depth_package.py`
- `scripts/run_recorded_depth_lookup_for_existing_run.py`
- `tests/unit/test_recorded_depth_lookup.py`

The current Tyrone package builder is specifically for the reviewed TP5/TP6 recorded-depth package.

This means:

> The app/backend can now honestly output numerical metres for reviewed recorded zones without pretending to estimate unknown depth.

It does **not** mean general numerical depth estimation is solved.

---

# Ground-truth values and evidence discipline

Known official measurement means already established in project records include:

- TP5 samples: 28, 26, 26, 28, 26 in -> mean 26.8 in = `0.68072 m`
- TP6 samples: 40, 35, 42, 36, 34 in -> mean 37.4 in = `0.94996 m`
- TP7 samples: 50, 52, 52, 50, 53 in -> mean 51.4 in = `1.30556 m`
- true TP6-TP5 mean contrast = `0.26924 m`

The 2 ft / 3 ft / 4 ft labels on TP5/TP6/TP7 drawings are nominal/design/as-built plot cover designations and must not be silently treated as measured min/max values.

For any future predictive/physical validation route, the above measured depths and the mapped test-pit depths must remain holdout truth and must not be used to align, tune, scale or rescue a method.

For Route A recorded lookup, reporting those measurements is the product itself, so this holdout restriction is about **prediction development**, not about suppressing the recorded values from the lookup output.

---

# Current route table

| Route | Current status |
|---|---|
| Reviewed recorded-depth lookup | **IMPLEMENTED / AVAILABLE as lookup** |
| General unknown-zone numerical depth estimate | **BLOCKED** |
| Raw NB proxy -> metres | **NOT VALIDATED** |
| `operator_scalar_interpolation_v1` | **DO NOT ENABLE** |
| Free 1996 NAPP medium stereo | **CLOSED** |
| Free 2004 pre-cover public web surface | **SEARCH EXHAUSTED / FILE NOT FOUND** |
| Free pre-Sept-2004 NAIP at Tyrone | **CLOSED — no scenes** |
| Public Appendix A 3X grades | **CLOSED — 3X absent** |
| 14 micron NAPP on-demand scan | **HELD / NOT APPROVED / PAID** |
| Option 5 surface-change outputs | **USEFUL, but NOT DEPTH** |

---

# What is still not solved

The project still lacks a scientifically defensible way to calculate depth in metres for an arbitrary unknown AOI.

The missing physical input is a sufficiently accurate surface representing the immediate pre-cover/post-grading substrate, or another independent method that can meet the frozen error gate without using the known answers for tuning.

Under the present constraints of:

- no new emails;
- no payment;
- no threshold relaxation;
- no random satellite feature hunting;

the currently known direct-elevation route has no active free data source left.

Do not hide this from the user.

---

# Exact next steps for the next session

## Next Step 1 — verify Route A end to end on a real existing Tyrone run

This should be the immediate practical task because Route A is now merged but the UI was intentionally untouched.

Do this in order:

1. Read PR #119 files and `tests/unit/test_recorded_depth_lookup.py`.
2. Build the reviewed Tyrone TP5/TP6 recorded package using:
   - `scripts/build_tyrone_recorded_depth_package.py`
3. Pick an existing Tyrone run directory that is safe to test without changing classifier output.
4. Prepare/verify candidate input containing exact reviewed TP5/TP6 zone IDs.
5. Run:
   - `scripts/run_recorded_depth_lookup_for_existing_run.py`
6. Inspect:
   - depth estimates CSV;
   - depth summary JSON;
   - method manifest JSON.
7. Verify these invariants:
   - TP5/TP6 return `recorded_measurement`;
   - provenance is present;
   - `estimated_depth_*` is blank for recorded rows;
   - an unknown zone returns no metres / abstains;
   - classifier artifacts are unchanged;
   - satellite run-quality does not suppress a valid recorded measurement.
8. Report the result to the user in simple English.

Do **not** change the UI during this verification unless the user explicitly asks for the recorded values to be surfaced there.

## Next Step 2 — decide product presentation only after backend verification

If Route A passes end-to-end:

- explain clearly that this gives **recorded measured depth for reviewed zones**, not an estimate;
- if the user wants it visible in the app, propose the smallest additive UI change and ask before changing existing results/UI behavior.

Suggested wording:

`Recorded depth — available for this reviewed zone`

Never label it `estimated depth`.

## Next Step 3 — possible free expansion of Route A

After TP5/TP6 verification, it may be possible to add more reviewed Tyrone recorded zones such as TP7, TP1/TP2/TP3 and selected mapped test pits, **only after exact spatial/provenance review**.

This would increase the number of places where the app can show honest metres, but it still would not estimate unknown zones.

Do not mass-import nominal plot labels as measurements.

## Next Step 4 — general estimation only reopens on new evidence

Reopen the direct-elevation route only if a genuinely new file/source appears containing one of:

- pre-cover/post-grading CAD/TIN/grid/LandXML;
- CAES design/as-built terrain export;
- GPS point cloud/point list tied to the 3X control system;
- sufficiently dense and tied pre-cover contours that can pass the frozen accuracy gate;
- another independently verifiable pre-placement surface.

Do not repeat the already-exhausted exact public BER/CQAR searches unless a new archive/source becomes available.

Paid 14 micron scans remain a possible experiment only if the user explicitly changes the current no-payment constraint.

---

# Must-read documents for the next session

Read these before doing new work:

1. `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V1.md` — this handoff.
2. `docs/TYRONE_PRE_COVER_SURFACE_RECOVERY_CLOSED_FALLBACK_B_ACTIVE_2026-08-19.md` — direct-elevation strategy, grading confound, frozen route logic.
3. `docs/TYRONE_NAPP_STEP5_DESK_ERROR_BUDGET_2026-08-19.md` — scan-resolution/error-budget decision.
4. `docs/TYRONE_NAPP_FREE_MEDIUM_STEREO_PREDEPTH_FAILURE_2026-08-20.md` — decisive free-scan failure before depth was revealed.
5. `docs/TYRONE_3X_2004_PRECOVER_PUBLIC_WEB_SEARCH_2026-08-20.md` — exact public document search and closure.
6. `docs/DEPTH_OPTION1_TYRONE_3X_TEST_PLOTS_5_6_DECISIVE_RESULT_2026-07-29.md` — official TP5/TP6 measurement evidence and interpretation.
7. `docs/DEPTH_LOCAL_MVP_OPERATOR_GUIDE_2026-07-29.md` — earlier operator-depth framing and recorded measurement rows.
8. PR #119 implementation files/tests listed above.

Useful source files already available in the project/session:

- `3X_CQAR_010_R0.pdf`
- `3X_CQAR_004_R0.pdf`
- `3X_CQAR_006_007_R0.pdf`
- `R2104.PDF` camera calibration report
- `data/research/tyrone_napp_1996/Desktop.7z.001`
- `data/research/tyrone_napp_1996/Desktop.7z.002`
- `data/research/tyrone_napp_1996/Desktop.7z.003`

---

# How to work with the user in the next session

- Use short, simple English.
- Always state **current result** and **next action**.
- Work one step at a time but continue automatically when the next step is safe and already authorized.
- Do not create search loops.
- If a dependency requires the user to provide/pay/request something, say so immediately and clearly.
- Never imply the user approved payment when they did not.
- Do not stop after a failure without saying what remains and what the next feasible path is.
- Protect the classifier and unrelated UI.

## One-sentence starting point for the next session

> Route A recorded-depth lookup is now merged and safe for reviewed zones; the free unknown-depth elevation route is scientifically closed for now, so the next action is to verify Route A end-to-end on an existing Tyrone run without touching the classifier or UI.
