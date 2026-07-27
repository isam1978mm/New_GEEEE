# Bremo Bluff Closure-Report Recovery Result — 2026-07-27

## Decision

```text
CONFIRMED REMOVAL EVIDENCE = STRONG
FINAL RECORD DRAWINGS = REPORTED BUT NOT RECOVERED
EXACT EXECUTION GEOMETRY = NOT AVAILABLE
STABLE SENTINEL-1 PERIOD = NOT CONFIRMED
CALIBRATION ROW = NOT CREATED
EARTH ENGINE QUERY = NOT RUN
```

Virginia DEQ's current Bremo Bluff page publicly lists three East Ash Pond closure-by-removal construction-report parts, two West Ash Pond report parts, and a visual-inspection acceptance memorandum.

The public text supports completed and accepted removal from both ponds, but the report attachments are blocked by HTTP 403. The exact Appendix A record drawings therefore remain unavailable for geometry extraction.

No parcel, approximate pond outline, or analyst-drawn replacement was used.

## Removal evidence established

### East Ash Pond

The official DEQ review record supports:

- the East Ash Pond construction report was dated May 23, 2019;
- a professional-engineer construction-quality certification accompanied the report;
- DEQ's visual site inspection and the submitted documentation supported removal and over-excavation;
- DEQ accepted the documentation on October 1, 2019;
- the original delineated pond area was approximately 26.5 acres;
- the reported removal area was approximately 27.2 acres because CCR outside the original delineated limits was also removed and undercut;
- the additional areas were identified as appearing in Appendix A record drawings.

This makes the record drawings especially important. The broader original pond boundary cannot replace the verified final removal footprint.

### West Ash Pond

The official DEQ review record supports:

- the West Ash Pond construction report was dated March 25, 2020;
- a professional-engineer construction-quality certification accompanied the report;
- the submitted documentation supported visual removal and over-excavation;
- DEQ accepted the documentation on April 17, 2020.

Virginia DEQ's facility page states that ash had been removed from both the East and West ponds by April 2020.

## Public-file recovery attempted

The following official Virginia DEQ files were targeted:

```text
East Ash Pond report — Part 1 of 3
East Ash Pond report — Part 2 of 3
East Ash Pond report — Part 3 of 3
West Ash Pond report — Part 1 of 2
West Ash Pond report — Part 2 of 2
Visual Inspection and Acceptance Memorandum
```

The normal document viewer returned cache or access failures. A temporary GitHub Actions extractor then attempted direct downloads from all six official `showpublisheddocument` endpoints.

Every endpoint returned:

```text
HTTP 403 Forbidden
```

No source PDF was recovered, no page was rendered, and no record-drawing coordinate was extracted.

The failed temporary extractor is not merged.

## Geometry decision

The available public text confirms that record drawings exist and that final removal extended beyond the original East Pond delineation.

However, the following remain unavailable:

```text
final accepted East removal polygon
final accepted West removal polygon
record-drawing coordinate system and vertices
survey-position accuracy
boundary-position uncertainty
restored-surface exclusions
```

Therefore:

```text
exact WGS84 geometry = no
execution GeoJSON = no
20 m pixel-support test = not run
```

## Timing and surface stability

A possible post-removal period exists after East acceptance in 2019 and West acceptance in 2020.

The broader site later experienced substantial demolition, and Virginia DEQ now reports a separate adjacent CCR landfill development for North Pond removal. The exact East and West restored footprints may still have had a usable interval, but no reviewed record establishes that they remained materially unchanged for a specific Sentinel-1 window.

Therefore:

```text
possible quiet period = identified
stable exact-footprint period = unverified
clean Sentinel-1 window = not confirmed
```

## What remains valid

```text
East Pond removal confirmed = yes
West Pond removal confirmed = yes
professional engineering certification = yes
DEQ acceptance = yes
record drawings reported = yes
```

## What is not approved

```text
record drawings recovered = no
exact confirmed-empty polygons = no
boundary uncertainty = no
stable observation window = no
Earth Engine query = no
confirmed-negative calibration row = no
```

## Machine-readable result

```text
data/bremo_bluff_closure_report_recovery_result.json
```

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
bremo_confirmed_removal = yes
bremo_DEQ_acceptance = yes
bremo_record_drawings_reported = yes
bremo_record_drawings_recovered = no
bremo_exact_geometry = no
bremo_stable_timing = unverified
bremo_calibration_row_ready = no
```

## Next step

Retain Bremo as strong confirmed-removal evidence only. Continue to a completed removal or cover site whose final record drawings are directly retrievable, whose boundary uncertainty is supported, and whose restored surface remained stable for a clean observation period.
