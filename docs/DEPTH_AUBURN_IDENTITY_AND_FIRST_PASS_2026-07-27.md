# Auburn Candidate Identity and First Pass — 2026-07-27

## Decision

```text
AUBURN ROAD LANDFILL, NEW HAMPSHIRE = EVIDENCE ONLY / REJECT FOR DEPTH ORDERING
CITY OF AUBURN LANDFILL NO. 2, NEW YORK = PROMISING ACTIVE LEAD / NOT YET GOOD TO GO
```

The ordered candidate list named only “Auburn.” Because multiple official landfill sites use that name, both plausible facilities were checked rather than silently assuming an identity.

No Sentinel-1 or Earth Engine query was run.

## Auburn Road Landfill — Londonderry, New Hampshire

Official EPA records describe three disposal areas totaling roughly 12–13 acres. Each area received the same modified RCRA Subtitle C-style cap, approximately four feet thick, including an impermeable membrane/clay component and vegetated surface.

This is useful closure evidence, but the public record recovered in this pass does not provide:

- point-by-point final measured cover thicknesses;
- a readable as-built survey tied to final thickness measurements;
- two named zones with non-overlapping measured final depths;
- numerical survey-position or depth-measurement accuracy.

Because the three capped areas were built to the same nominal cover system, the available evidence does not establish a defensible shallow-versus-deep pair.

Decision:

```text
auburn_road_nh_depth_ordering = rejected_no_measured_depth_contrast
```

## City of Auburn Landfill No. 2 — Auburn, New York

The City of Auburn’s official bid record identifies a 2021 project titled “City of Auburn Landfill No. 2 Final Closure and Leachate System Modifications.” The awarded base scope included:

- preparation of approximately 14.4 acres of intermediate cover for geomembrane placement;
- construction of approximately 14.4 acres of final cover system;
- six new vertical gas-extraction wells;
- gas-collection piping;
- leachate-sump modifications;
- drainage improvements.

The work was awarded to Marcy Excavation Services on April 8, 2021. Barton & Loguidice was identified with the project documentation/design route.

This is a stronger current lead because the construction is recent, large enough in principle for multiple 20 m Sentinel-1 footprints, and likely generated construction-quality and as-built records.

However, the public material recovered so far is only the bid/award record. It does not yet establish:

1. the actual construction-completion date;
2. final construction certification;
3. an as-built final-cover survey;
4. mapped point-by-point installed thicknesses;
5. numerical construction or survey accuracy;
6. two zones with non-overlapping final measured depths;
7. a clean stable post-construction period unaffected by transfer-station activity, gas infrastructure, drainage work, or other operations.

Therefore no calibration geometry or radar query is authorized.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
auburn_identity_ambiguity_resolved = yes
auburn_road_nh_status = rejected_no_measured_depth_contrast
auburn_landfill_no2_ny_status = promising_active_lead_not_good_to_go
auburn_ny_final_construction_report_recovered = no
auburn_ny_as_built_survey_recovered = no
auburn_ny_mapped_final_depths_recovered = no
auburn_ny_clean_20m_pair_confirmed = no
```

## Next step

Recover the City of Auburn Landfill No. 2 final construction report, closure certification, as-built survey, and construction-quality records. Only if those records contain mapped final thickness measurements and numerical accuracy should shallow/deep polygons be designed and tested for 20 m pixel support.