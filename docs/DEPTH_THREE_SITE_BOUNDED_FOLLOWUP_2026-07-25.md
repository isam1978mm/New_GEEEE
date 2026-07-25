# Depth Calibration — Three-Site Bounded Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** targeted public-record follow-up completed; no calibration row is eligible  
**Sites:** Go East, Elk Plain, Sudbury Road Landfill

## Plain-English result

The three strongest public leads were checked again for their exact missing evidence.

None is ready for calibration.

```text
usable_calibration_rows = 0
training_ready = no
app_depth_output_ready = no
```

## 1. Go East

### What is now confirmed

- Two areas were physically checked and support real no-target or cleared-area evidence.
- The completed cover has a documented minimum soil thickness of `0.762 m`.
- Public official figures show the former landfill edge and the cleared wedge area.

### Why it is still blocked

- The accessible public figures state that locations are approximate or for informational use.
- The exact plan-sheet or record-drawing boundary for either checked empty area was not recovered.
- Residential, road, driveway, utility, and ground-surface work continued after closure.
- A clean and unchanged Sentinel-1 period is not verified.

### Decision

```text
exact_negative_boundary = missing
clean_sentinel1_timing = no
eligible_rows = 0
```

Go East remains evidence-only. An approximate figure must not be converted into a calibration polygon.

## 2. Elk Plain County Shop

### What is now confirmed

- The public cap-thickness drawing contains many actual mapped thickness values, approximately `6.00` to `11.08 ft`.
- Ecology accepted the drawing as answering its cap-thickness request.
- Ecology has issued No Further Action and the environmental covenant is recorded.
- Pierce County Record of Survey `202502055001` remains the named official source most likely to contain survey-control information.

### Why it is still blocked

- The public cap drawing is marked `REVIEW SET`.
- It does not state numerical vertical accuracy, equipment accuracy, survey closure, or a final depth uncertainty.
- The county image portal requires an interactive session, and the recorded survey image was not recovered through a separately indexed official source.
- No independently confirmed empty comparison footprint has been found.

### Decision

```text
mapped_depth_values = yes
survey_uncertainty = missing
confirmed_negative = missing
eligible_rows = 0
```

The mapped values must not become depth labels until a source-supported uncertainty is recovered.

## 3. Sudbury Road Landfill

### New useful confirmation

The official Construction Plans and Specifications, Volume III CQA, confirms that:

- the project surveyor was required to document as-built conditions and installed quantities;
- as-built information was required to be collected throughout construction;
- the final construction report was required to contain as-built record drawings;
- the record drawings were required to be prepared from project-surveyor work and reviewed by the signing professional engineer;
- Areas 2 and 5 were required to receive an as-built survey of final grade;
- soil-cover thickness was required to be verified;
- acceptance required at least `4.8 ft` (`1.46304 m`) of cover.

Volume I also requires conventional as-built surveys, at least a 50-foot final survey grid for Areas 2 and 5, and electronic survey points and digital terrain-model surfaces.

This proves that useful final survey data was created. It does not expose the actual mapped values.

### Why it is still blocked

- Official Construction Quality Assurance Certification Report document `64264` is listed but did not load from the public document endpoint.
- No alternate official indexed copy of its record drawings or survey-point tables was found.
- The public CQA plan states requirements, not the final mapped depth at each location.
- The full final uncertainty remains unassigned.
- No independently confirmed no-target comparison footprint has been found.
- The landfill remains active in a separate lined area, and a 2026 proposal concerns vertical expansion of Area 7. A clean observation period for capped Areas 2 and 5 therefore needs an area-specific check and cannot be assumed from site-level completion alone.

### Decision

```text
verified_minimum_depth_m = 1.46304
proof_final_survey_existed = yes
actual_as_built_surface_values = missing
final_uncertainty = missing
confirmed_negative = missing
clean_sentinel1_timing = not_verified
eligible_rows = 0
```

Sudbury remains the strongest bounded-minimum positive-depth lead, but it is not calibration-ready.

## Overall decision

```text
Go_East_eligible_rows = 0
Elk_Plain_eligible_rows = 0
Sudbury_eligible_rows = 0
total_eligible_rows = 0
```

Do not start training. Do not enable numerical depth in the app. Do not convert approximate maps, design requirements, or construction-control tolerances into final depth labels.

## Next bounded action

Continue with the exact missing official record only:

1. recover Sudbury Construction Quality Assurance Certification Report `64264`, especially its as-built record drawings, final survey-point tables, and Area 2/Area 5 surfaces;
2. if no public official copy can be recovered, mark the Sudbury public-web path exhausted and return to Pierce County Record of Survey `202502055001` for Elk Plain;
3. create no calibration row unless the validator-required geometry, uncertainty, timing, and confirmed comparison evidence are all supported.

## Official source locations

- Washington Department of Ecology Go East Corp Landfill site, Cleanup Site ID 4294.
- Washington Department of Ecology Elk Plain County Shop site, Cleanup Site ID 5764.
- Washington Department of Ecology Sudbury Road Landfill site, Cleanup Site ID 2485.
- Sudbury Construction Plans and Specifications, Volume I, document 53360.
- Sudbury Construction Plans and Specifications, Volume III CQA, document 53362.
- Sudbury Construction Quality Assurance Certification Report, document 64264.
- Washington Ecology SEPA record 202602324, Area 7 vertical expansion.

Coordinate-bearing geometry remains outside Git.
