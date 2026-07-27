# River Road Landfill Cover-Certification First Pass — 2026-07-27

## Decision

```text
PROMISING ACTIVE LEAD — NOT YET GOOD TO GO
```

River Road Landfill in Hermitage / South Pymatuning Township, Mercer County, Pennsylvania has substantially stronger positive-depth documentation than a normal design-only landfill record. It may provide a large, stable, vegetated calibration surface, but the exact final point depths and surveyed point geometry have not yet been extracted.

No Sentinel-1 or Earth Engine query is authorized yet.

## Official records reviewed

- EPA River Road Landfill Superfund site profile.
- EPA 1995 Record of Decision, including Appendix C: River Road Landfill Closure Certification and Post-Closure Plan.
- Closure certification dated September 30, 1987.

## Strong evidence found

The closure certification states that:

- closure activities were completed on September 30, 1987;
- a minimum of three feet of final cover was placed;
- 129 cover-certification pits were excavated;
- the pits were used to verify final cover thickness, soil classification, and nutrient requirements;
- Sheet 1 of 3 shows the surveyed pit locations;
- TGAI field reports detail the cover thickness at each pit;
- deficient areas were corrected and then re-certified by overlapping pits and/or inspection;
- Kurtanich Engineers and Associates supplied survey support;
- Todd Giddings and Associates supplied construction management, engineering inspection, QA/QC, and engineering certification;
- the cap was revegetated and placed under continuing inspection and maintenance.

The minimum constructed depth is:

```text
3.0 ft = 0.9144 m
```

The mapped work area is large: the landfill disposal area is approximately 37.5 acres within a 102-acre property.

The current EPA site profile states that the cap remains in place and maintained, the site remains fenced, and institutional controls protect the cap and prohibit residential construction.

## Why this is not yet a calibration row

The searchable public text does not yet provide the information needed to build defensible shallow and deep polygons:

1. The 129 individual final pit thicknesses have not been extracted from the scanned field reports.
2. Sheet 1 of 3, which maps the surveyed pit locations, has not been recovered as a readable georeferenceable drawing.
3. No numerical survey-position or depth-measurement accuracy has yet been found.
4. Initial deficient pit readings cannot be treated as final constructed depth unless the correction and re-certification record is linked to the same area.
5. No two large zones with non-overlapping final measured depth ranges have yet been demonstrated.
6. No 20 m pixel-support geometry has been tested.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
river_road_official_closure_confirmed = yes
river_road_minimum_cover_m = 0.9144
river_road_certification_pit_count = 129
river_road_surveyed_pit_map_reported = yes
river_road_individual_final_depths_extracted = no
river_road_survey_accuracy_found = no
river_road_clean_20m_pair_confirmed = no
river_road_candidate_status = promising_active_lead
```

## Next step

Recover the scanned final-cover certification Sheet 1 and the TGAI field-report pages, then:

1. extract final re-certified pit depths only;
2. tie pit identifiers to surveyed map locations;
3. search for numerical survey and test-pit measurement accuracy;
4. identify two same-surface zones with non-overlapping final depth ranges;
5. test each zone for at least one clean 20 m Sentinel-1 interior footprint;
6. only then consider an acquisition-coverage query.
