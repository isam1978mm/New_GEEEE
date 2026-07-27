# Numerical depth evidence search — session handoff — 2026-07-27 V4

## Plain-English goal

Unlock a defensible **numerical depth output in the New_GEEEE app**.

This project is about the app. Do not introduce or discuss the uploaded notebook unless the user specifically asks about it.

The app cannot produce numerical depth yet because no public candidate has passed every calibration-evidence gate.

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
training_started = false
plan_changed = no
```

## User-approved plan — locked

Continue only with **full-scale vegetated cover zones** that:

- remain at least **30–40 m wide after excluding boundaries, slopes, drainage and infrastructure**;
- contain **final measured as-built depths**, not only design specifications;
- provide an exact second measured depth zone or confirmed negative zone;
- use matching radar-facing vegetation and near-surface construction;
- have coordinate-tied geometry;
- include numerical depth or survey uncertainty;
- remained physically stable during a usable Sentinel-1 period.

Do not change this plan without the user's approval.

Do not advance:

- small test plots;
- scattered points that require interpolation into invented polygons;
- design-only depths;
- average thickness inferred only from total volume;
- historical measured zones removed or rebuilt before Sentinel-1;
- repaired, subsided, ponded, wooded or redeveloped surfaces;
- pairs with different topsoil, sand, slag, asphalt, gravel or other radar-facing assemblies;
- narrow strips that cannot hold two independent clean radar footprints.

Do not run Earth Engine until every documentary gate passes.

## How we worked

Use this exact working pattern:

1. **Cheap screen first.** Check size, final surface, construction date and likely stability before recovering large records.
2. **Use official sources.** Prioritize regulator closure certifications, CQA reports, as-built drawings, survey tables, five-year reviews and post-closure licenses.
3. **Recover blocked files through a temporary GitHub branch and draft PR.** The temporary branch may contain a narrowly scoped downloader or browser extractor.
4. **Keep recovery branches isolated.** Do not merge temporary scraping/recovery tools.
5. **Inspect decisive PDF pages only.** Read searchable text first, then render pages containing cap profiles, thickness tables, survey coordinates, maps and certifications. Avoid OCR unless absolutely necessary.
6. **Stop at the first fatal scientific blocker.** Do not spend time on radar if the documentary pair fails.
7. **Record completed decisions on `main`.** Create one JSON result in `data/` and one plain-English result document in `docs/`.
8. **Close temporary PRs without merging.** Keep the final evidence decision on `main` only.
9. **Report clearly.** Always state: good to go or not, fatal blocker, current app status and one next action.

## Exact stopping point — active Ford River Raisin candidate

### Candidate

**Ford River Raisin Warehouse**, Michigan.

### Active temporary work

```text
PR: #19
branch: agent/ford-river-raisin-cap-review-20260727
PR state: open draft
merge: do not merge
workflow run: 30313823075
workflow conclusion: success
artifact: ford-river-raisin-cap-records
artifact ID: 8671398026
artifact expiry: 2026-08-03
```

The artifact contains the official post-closure license and supporting public records. In the completed session it was downloaded as:

```text
/mnt/data/ford-river-raisin-cap-records.zip
```

The next session may not retain that local path. Re-download artifact `8671398026` from workflow run `30313823075` when necessary.

### What has been established

- The site has two large closed containment cells: east and west.
- The combined capped area is approximately **54 acres**.
- The cells have been under controlled post-closure maintenance since approximately 1999.
- The official license contains long-term inspection and monitoring requirements.
- A **2017 coordinate-controlled topographic survey** is referenced in the recovered official record.
- Size is sufficient in principle for 30–40 m clean interiors.
- Long-term controlled management makes a stable Sentinel-1 period plausible.

### What remains unresolved

The session stopped while extracting the exact east-cell and west-cell cap construction.

The next session must determine:

1. Do the east and west cells have **different final cover depths**, or do they repeat one identical design?
2. Are the depths **actual measured as-built values** or only design requirements?
3. Are the depth values tied to exact survey coordinates, final contours or certified polygons?
4. Do both cells use the same upper soil and vegetation assembly?
5. Is numerical horizontal or vertical survey uncertainty stated?
6. Does each measured condition retain a 30–40 m clean interior after excluding roads, drainage, monitoring infrastructure and cell edges?

No Ford decision document or calibration row has been created yet.

## Immediate next steps for Ford

### Step 1 — reopen the recovered package

Use PR #19 and workflow artifact `8671398026`.

Read the recovery report/inventory first. Search the recovered license text and PDFs for:

```text
east cell
west cell
containment cell
final cover
cap
vegetative soil
topsoil
protective soil
barrier soil
clay
geomembrane
as-built
survey
certification
thickness
elevation
1999
2017
```

### Step 2 — locate decisive pages

Render only pages containing:

- east/west cell cross-sections;
- cap layer tables;
- final-cover drawings;
- construction completion or closure certification;
- as-built surveys;
- topographic survey notes;
- numerical survey tolerances or accuracy statements.

### Step 3 — make one of two decisions

#### Ford passes the documentary gate only if all are true

```text
two large measured depth conditions = yes
coordinate-tied final measured depths = yes
matching upper soil/vegetation = yes
numerical uncertainty = yes
30-40 m clean interior in each = yes
stable Sentinel-1 period = yes
```

Then:

- create exact candidate polygons from official survey geometry;
- calculate conservative edge/infrastructure exclusions;
- create provisional evidence records;
- run the calibration-pack validator;
- still do not run Earth Engine until the evidence record passes validation.

#### Ford fails if any required item is missing

Then create:

```text
data/ford_river_raisin_cap_depth_pair_screen_result.json
docs/DEPTH_FORD_RIVER_RAISIN_CAP_DEPTH_PAIR_RESULT_2026-07-27.md
```

Record the exact fatal blocker, close PR #19 without merging and continue the approved search unchanged.

## Short roadmap after Ford

### Roadmap A — if Ford is good

1. Extract exact survey polygons and measured depths.
2. Confirm a numerical uncertainty for every depth value.
3. Verify matching near-surface construction.
4. Confirm two clean 30–40 m interiors.
5. Establish the unchanged Sentinel-1 date window.
6. Create calibration evidence rows and run the validator.
7. Only after the validator passes, perform the first bounded Earth Engine radar comparison.

### Roadmap B — if Ford is not good

1. Record and close Ford cleanly.
2. Search state closure-certification packages containing matched **subgrade and final-grade survey grids**.
3. Prioritize full-scale closures with intentional deck/slope or cell-to-cell thickness differences under one common topsoil/vegetation specification.
4. Reject immediately when the second zone is design-only, too narrow or materially different at the surface.

## Important completed candidates from this session

All remain **not good to go**.

### Hoosier #1 Landfill

Strongest measured-point evidence recovered:

- 18 coordinate-tied points;
- actual subgrade, barrier-top and cover-top elevations;
- soil-barrier thickness 2.00–3.07 ft;
- protective-soil thickness 2.80–4.33 ft.

Fatal blocker: measurements are irregular points in a 1.85-acre strip, not two broad measured polygons. The older 39-acre cap has no public final measured thickness grid.

### Rocky Mountain Arsenal Integrated Cover System

Very strong geometry/stability near-miss:

- large mapped 2-ft and 3-ft vegetated polygons;
- shared vegetation assessment group;
- long-term monitoring and stable management.

Fatal blocker: public records do not provide coordinate-tied absolute final as-built depths for the 2-ft polygons, a pointwise grid across both conditions or numerical survey uncertainty.

### Onondaga Lake Sediment Consolidation Area

Large and stable vegetated cover, but one uniform upland profile. Other measured depth variations belong to underwater caps and are outside the locked plan.

### Keystone Sanitation Landfill

Historical grid-based thickness concept, but the Sentinel-1-era surface experienced ponding, subsidence, woody vegetation and repeated repairs. Historical zones are no longer stable.

### Plattsburgh AFB LF-022 and LF-023

Large, stable vegetated caps. Public records do not publish coordinate-tied measured thickness grids or numerical uncertainty, and the upper cap assemblies are not proven equivalent.

### McLaren Tailings

Strong historical 100-ft cover grid with 35 borings. The measured zones were removed during reclamation and did not survive into the Sentinel-1 period.

### Vista Pointe Areas B and C

Large 3-ft versus 2-ft vegetated closures. Fatal blocker: different near-surface materials—soil/sand/compost over sand versus vegetative soil over slag fines.

### BDM Warren Steel

Pond #5 has a professionally surveyed closure and an inferred area-average thickness. The comparison lagoon lacks exact final survey geometry, near-surface materials differ and the site was unstable during demolition/redevelopment.

### Iron Valley C&DD Landfill

Large vegetated closure, but one uniform 24-inch final cover. No measured second depth condition.

## Previously closed candidates — do not repeat without new evidence

Do not restart these routes unless a genuinely new final as-built survey or stable exact polygon is found:

- Consolidated Iron;
- Berks Landfill;
- McMaster Street;
- Plant Kraft AP-1;
- Bremo Bluff;
- Meredosia;
- Kiefer Landfill;
- Sandia ALCD;
- Sconondoa Street former MGP;
- River Road;
- Auburn;
- John Sevier;
- J.R. Whiting;
- Fletcher's Paint;
- Elizabeth Mine;
- Possum Point;
- Dixie Auto Salvage;
- Omaha ACAP;
- Altamont ACAP;
- Coal Creek Station;
- Huron River Properties;
- Vista Pointe Area C alone;
- Grainger Ponds;
- Go East;
- TAMUCC;
- Maxey Flats routes already documented as closed.

## Documents the next session should read

Read in this order.

### Required foundation

1. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-27_V4.md`
2. `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`
3. PR #19 body and branch files:
   - `scripts/recover_ford_river_raisin_cap_records.py`
   - `.github/workflows/ford-river-raisin-cap-recovery.yml`

### Latest completed evidence decisions

4. `docs/DEPTH_HOOSIER1_LANDFILL_MEASURED_COVER_PAIR_RESULT_2026-07-27.md`
5. `data/hoosier1_landfill_measured_cover_pair_screen_result.json`
6. `docs/DEPTH_RMA_INTEGRATED_COVER_2FT_3FT_RESULT_2026-07-27.md`
7. `data/rma_integrated_cover_2ft_3ft_screen_result.json`
8. `docs/DEPTH_ONONDAGA_SCA_FINAL_COVER_RESULT_2026-07-27.md`
9. `data/onondaga_sca_final_cover_screen_result.json`
10. `docs/DEPTH_KEYSTONE_SANITATION_COVER_GRID_RESULT_2026-07-27.md`
11. `data/keystone_sanitation_cover_grid_screen_result.json`
12. `docs/DEPTH_PLATTSBURGH_LF022_LF023_RESULT_2026-07-27.md`
13. `data/plattsburgh_lf022_lf023_depth_pair_screen_result.json`
14. `docs/DEPTH_MCLAREN_TAILINGS_PRE_REMEDIATION_COVER_GRID_RESULT_2026-07-27.md`
15. `data/mclaren_tailings_pre_remediation_cover_grid_screen_result.json`
16. `docs/DEPTH_VISTA_POINTE_AREA_B_AREA_C_CROSS_CLOSURE_RESULT_2026-07-27.md`
17. `data/vista_pointe_area_b_area_c_depth_pair_screen_result.json`
18. `docs/DEPTH_BDM_WARREN_STEEL_POND_CLOSURE_RESULT_2026-07-27.md`
19. `data/bdm_warren_steel_pond_closure_depth_pair_screen_result.json`
20. `docs/DEPTH_IRON_VALLEY_CDD_FINAL_CLOSURE_RESULT_2026-07-27.md`
21. `data/iron_valley_cdd_final_closure_screen_result.json`
22. `docs/DEPTH_NUMERICAL_ESTIMATION_SESSION_HANDOFF_2026-07-27_V3.md` for the earlier historical checkpoint and candidate trail.

These documents capture the repeated failure patterns and prevent duplicated work.

## Repository state at handoff

```text
main latest completed evidence commit = 48b316710c413fd6a6aa1996fea44b3bfd687061
active temporary PR = #19
active branch = agent/ford-river-raisin-cap-review-20260727
PR #19 merged = no
PR #19 should remain open until Ford decision = yes
usable calibration rows = 0
numerical depth ready = no
app depth enabled = no
Earth Engine query executed = no
plan changed = no
```

## Required communication style

The user wants brief, plain English.

Every progress message should say:

```text
Current status
What was found
Good to go or not
Fatal blocker, if any
Exact next step
```

Do not use deep technical language unless needed. Do not imply that processing is happening in the background. Continue the work in the current session and make a best-effort decision with the available evidence.