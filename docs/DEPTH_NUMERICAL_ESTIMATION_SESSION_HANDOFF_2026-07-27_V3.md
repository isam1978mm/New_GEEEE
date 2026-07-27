# Numerical Depth Estimation Session Handoff — 2026-07-27 V3

## Goal

Unblock an honest numerical depth estimate by finding public calibration evidence that can support a real Sentinel-1 test.

A site is only usable when it provides all of the following:

1. actual measured depth or a confirmed removed/empty condition;
2. exact final survey geometry;
3. numerical depth or boundary uncertainty;
4. the same final radar-facing surface in the comparison areas;
5. at least one clean 20 m Sentinel-1 footprint in each condition after margins;
6. a stable post-construction observation period;
7. no building, road, drainage, solar-panel, liner-surface, or redevelopment confounder.

Do not run Earth Engine until these gates pass.

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
training_started = false
```

The project is still blocked, but the search method is now much better bounded.

## How this session worked

Use the cheapest fatal gates first:

1. Check whether the final surfaces are comparable.
2. Check whether final measured depths or confirmed removal are public.
3. Check survey uncertainty.
4. Check whether the shallow and deep/negative zones are physically wider than 20 m after margins.
5. Check long-term surface stability.
6. Only then create WGS84 polygons and query Sentinel-1.

Large public PDFs were recovered with temporary GitHub Actions branches. Only reports, JSON decisions, and handoff documentation were written to `main`. Temporary extractor code was not merged.

Never replace an unavailable as-built boundary with a parcel, approximate aerial outline, planning drawing, or analyst-drawn polygon.

## Strongest completed near-miss

### Consolidated Iron and Metal — Newburgh, New York

This is the strongest same-surface measured-depth candidate recovered so far.

Evidence recovered:

```text
2012 Final Engineering Report = yes
2014 Final Site Management Plan = yes
final as-built drawings = yes
depth-of-excavation map = yes
post-excavation cross section = yes
licensed surveyor = yes
survey tolerance = +/- 0.5 ft
measured cover depths = 3.0 to 6.2 ft
same final surface = clean fill + minimum 6 in topsoil + hydroseed
```

Fatal blocker:

```text
only robust shallow cell width = 50 ft = 15.24 m
required clean interior width = 20 m
pixel-support decision = HOLD_PIXEL_SUPPORT_FAILED
```

Do not retry by interpolating beyond the surveyed cell.

Read:

- `docs/DEPTH_CONSOLIDATED_IRON_ASBUILT_AND_PIXEL_SUPPORT_RESULT_2026-07-27.md`
- `data/consolidated_iron_depth_pair_pixel_support_result.json`

Commits:

```text
7fd76cf222e7c042bb99b6ee13068036b1f130d7
5d8afe6e0129a793500a8e461f7800b4f0842d2f
```

## Latest completed candidate

### Berks Landfill — Pennsylvania

The site has large vegetated landfill areas and completed cap repairs, but the public EPA record does not publish final point measurements, a final thickness-zone map, or numerical survey accuracy.

Decision:

```text
HOLD_FINAL_DEPTH_SURVEY_NOT_PUBLIC
```

Read:

- `docs/DEPTH_BERKS_LANDFILL_FINAL_CAP_EVIDENCE_RESULT_2026-07-27.md`
- `data/berks_landfill_final_cap_evidence_screen_result.json`

Commits:

```text
910720a4e0f36a7c6d038910b109da45ca38ab05
5d013a76d6399203716212e6c97b38d3b5b660f4
```

## Active candidate for the next session

### Dixie Auto Salvage Site — Danville, Illinois

This is the exact point where work should continue.

Temporary PR:

```text
PR #11
branch = agent/final-report-313667-scout-20260727
state = open draft
merge = do not merge
```

Official source:

```text
EPA SEMS document = 313667
source = https://semspub.epa.gov/work/05/313667.pdf
report = Final Engineering Report
site = Dixie Auto Salvage Site, Danville, Illinois
report date = October 1999 / EPA metadata 2000-04-01
page count = 205
```

GitHub Actions result:

```text
workflow run = 30291134615
status = success
artifact = final-report-313667-scout
artifact id = 8662817931
```

The artifact contains:

```text
extraction_report.json
page_index.json
contact_sheet.jpg
80 rendered evidence pages
```

Important evidence already confirmed:

- remediation excavated the former residential yard/driveway, North Branch Ravine, and river materials;
- excavated materials were consolidated in the uplands area;
- the consolidation area received a geosynthetic final cover;
- cover design includes 30 inches protective soil plus 6 inches topsoil, then seeding/mulch;
- Exhibit E contains final site survey drawings;
- PDF page 204 is an as-built top-of-HDPE survey drawing based on a June 1999 field survey;
- PDF page 205 is an as-built top-of-topsoil survey drawing based on a July 1999 field survey.

Potential calibration structure to test:

```text
positive = vegetated uplands consolidation cap
nominal surface-to-HDPE depth = 36 in = 3.0 ft = 0.9144 m
possible negative = fully excavated and restored former residential yard/driveway
```

This pair is not yet approved.

## Exact next actions

1. Download and inspect artifact `8662817931` from PR #11.
2. Review report pages 1–13 for completed construction details.
3. Review drawing pages 18–32 for excavation, consolidation, final grading, utilities, roads, drainage and restoration.
4. Review pages 204–205 at full resolution.
5. Determine whether the former residential yard/driveway is a confirmed empty/restored area and whether its final topsoil/vegetation assembly is sufficiently comparable to the uplands cap.
6. Measure whether both the capped area and the possible negative area contain clean interiors wider than 20 m after all boundary and infrastructure margins.
7. Search the report specifications/CQA sections for a numerical survey or construction tolerance. The surveyor name alone is not enough.
8. Determine the drawing coordinate system or obtain a defensible georeference. Do not use an approximate property boundary.
9. Check post-1999 aerial history for a stable observation interval before redevelopment or major surface change.
10. If any gate fails, record the exact reason on `main`, close PR #11 unmerged, and continue to the next candidate.
11. Only if every gate passes, create conservative WGS84 execution polygons and then run the Sentinel-1 catalogue/pixel-support screen.

## Candidate outcomes from this session — do not repeat the same searches

### Sconondoa Street former MGP

- professional depth survey and corrected georeference;
- depth ordering supported;
- current polygons cannot contain clean 20 m footprints;
- nearby buildings contaminate the deep area;
- closed for the current 20 m test.

Read:

- `docs/DEPTH_SCONONDOA_PIXEL_SUPPORT_DRY_RUN_2026-07-26.md`
- `docs/DEPTH_SCONONDOA_OFFICIAL_ORTHO_VALIDATION_RESULT_2026-07-26.md`
- `data/sconondoa_phase3_pixel_support_dry_run_result.json`

### River Road Landfill

- 129 certification pits and minimum 3-ft cover are referenced;
- pit-location sheet and final field measurements are absent from the public electronic package;
- evidence-only lead.

### Auburn

- Auburn Road, New Hampshire: no measured depth contrast;
- Auburn Landfill No. 2, New York: recent final-cover project, but final certification/as-built thickness survey is not public;
- closed as public evidence only.

### John Sevier Bottom Ash Pond

- eastern capped area and western excavated area are physically large;
- nominal 24-in soil cover documented;
- exact as-built boundary and numerical uncertainty are not public;
- referenced cover-integrity studies are not published;
- evidence strong, geometry blocked.

### J.R. Whiting

- 107 actual mapped final cover thickness measurements recovered;
- best robust depth contrast is only 0.07 ft / 0.021 m;
- survey accuracy is unstated;
- deep area is crossed by drainage infrastructure;
- not usable.

### Plant Kraft AP-1

- confirmed removal and professional survey maps recovered;
- area is large enough in principle;
- verified excavation limit is embedded in a raster aerial;
- automated NAIP georeference was rejected;
- stable post-removal period not confirmed;
- evidence only.

Read:

- `docs/DEPTH_PLANT_KRAFT_AP1_MAP_AND_GEOREFERENCE_RESULT_2026-07-27.md`
- `data/plant_kraft_ap1_map_georeference_screen_result.json`

### Bremo Bluff

- East and West Pond removals accepted by Virginia DEQ;
- final record drawings are reported;
- all six official attachments returned HTTP 403;
- exact geometry unavailable.

Read:

- `docs/DEPTH_BREMO_BLUFF_CLOSURE_REPORT_RECOVERY_RESULT_2026-07-27.md`
- `data/bremo_bluff_closure_report_recovery_result.json`

### Meredosia

- 1,336-page CQA report and final as-built survey recovered;
- large areas and strong removal evidence;
- fatal surface mismatch: synthetic turf/HDPE/sand versus soil/vegetation;
- closed.

Read:

- `docs/DEPTH_MEREDOSIA_CQA_ASBUILT_AND_SURFACE_COMPARABILITY_RESULT_2026-07-27.md`
- `data/meredosia_cqa_asbuilt_screen_result.json`

### Fletcher's Paint Works

- Elm Street cap and Mill Street restoration have comparable vegetated soil-facing surfaces;
- Mill Street restored strip is too narrow and infrastructure-heavy for a clean 20 m negative footprint;
- exact omitted as-built appendices were not separately published;
- closed.

### Elizabeth Mine

- large final completion-report package exists;
- engineered cap is occupied by a utility-scale solar array;
- fatal radar confounder;
- closed.

### Possum Point

- older ponds were emptied into Pond D;
- Pond D is not yet a completed closed positive area;
- no completed same-surface pair.

## Temporary PR status

Closed without merging:

```text
PR #7  Fletcher's Paint Works
PR #8  Consolidated Iron
PR #9  Elizabeth Mine
PR #10 Berks Landfill
```

Leave open for the next session:

```text
PR #11 Dixie Auto Salvage / EPA 313667
```

## Notebook context

The attached notebook `lawful_gee_candidate_scout_FINAL_v6_request_zones_quality.ipynb` is a large processing pipeline with a 10 m master grid, Sentinel-1 GRD processing, many derived feature stacks, PCA anomaly extraction, rule-based classifiers, and later 17 m focus-mask / super-resolution-style outputs.

Important boundary:

```text
notebook processing output != measured depth calibration evidence
```

The notebook also contains an `ee.Authenticate()` fallback in its Earth Engine initialization cell. Do not use that fallback in this evidence-search workflow. Keep Earth Engine untouched until a site passes the documentary, surface, uncertainty, geometry and timing gates.

## Plain-English handoff

We are still blocked because no site has passed every gate.

The next session should not restart broad candidate searching immediately. It should finish the already successful Dixie Auto Salvage extraction in PR #11 and decide whether the vegetated 3-ft cap versus the excavated/restored yard can provide one clean 20 m positive/negative pair with exact survey support.

If Dixie fails, close it with the exact fatal reason and continue only to large same-surface projects with final as-built depth grids wider than 20 m.