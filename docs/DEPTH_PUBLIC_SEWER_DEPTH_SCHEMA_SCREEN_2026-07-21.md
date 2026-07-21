# Public Sewer Depth Schema Screen — 2026-07-21

Status: public-only evidence search continued. No user research, author contact, survey, fieldwork, calibration import, model training, or app-depth enablement occurred.

## Candidate — Taipei rainwater/sewer pipeline open data

Public source:

- Taiwan Government Data Open Platform dataset `145829`
- publisher: Taipei City Government Public Works Bureau, Water Resources Engineering Department
- updated 2026-06-25
- Open Government Data License, version 1.0

Public schema includes:

```text
pipeline number
sewer type and category
material
width and height
length and slope
upstream soil-cover depth
downstream soil-cover depth
soil-cover depth
upstream pipe-top elevation
downstream pipe-top elevation
upstream pipe-bottom elevation
downstream pipe-bottom elevation
creation time
```

Qualification:

```text
public_numeric_cover_depth = yes
pipe_top_reference_available = yes
public_geometry = yes
licence = open
installation_date = not_verified
reference_uncertainty = not_reported
independent_empty_ground = no
matched_sentinel_1_contract = no
target_scale_support = no_individual_pipes_sub_resolution
```

Potential use:

- validate depth-field parsing and units;
- test provenance and vertical-reference handling;
- test whether a future method refuses unsupported target scales;
- provide context for mapped infrastructure exclusion zones.

Prohibited use:

- do not treat each pipe segment as an independent Sentinel-1 training sample;
- do not infer installation date from record creation time;
- do not treat map absence as confirmed empty ground;
- do not import without uncertainty and site-group policy;
- do not use cover-depth values to validate notebook depth proxies.

## Other public sewer schemas screened

### Chilliwack sanitary utilities

- public line geometry;
- upstream/downstream invert elevations in CGVD28;
- no confirmed public rim/ground elevation, diameter, uncertainty, or installation date combination sufficient for a source-defined depth-to-top record during this pass.

### Toronto pressurized sewer mains

- public geometry, diameter, material, and upstream/downstream invert elevation fields;
- exact surface-elevation and uncertainty contract not verified during this pass.

### Branson sanitary sewer manholes

- public fields include installation date, rim elevation, invert elevation, and pipe-diameter attributes;
- manhole depth can be computed where values are present, but a manhole is a surface-connected structure and is not equivalent to an isolated buried-object calibration target;
- record completeness, units, licence, uncertainty, and Sentinel-1 scale support require separate validation.

### INDOT water-conveyance manholes

- public schema includes rim elevation, high/low invert elevation, and rim-to-bottom depth;
- useful as a schema example and infrastructure context, not approved Sentinel-1 depth truth.

## Scientific boundary

Municipal sewer data can contain legitimate numerical engineering depths. That does not mean Sentinel-1 can resolve those individual assets or estimate their depth.

A record can enter the current depth calibration pack only if all applicable requirements pass, including:

```text
independent reference definition
numerical uncertainty or approved uncertainty policy
stable physical-site grouping
sensor-acquisition references
supportable spatial scale
positive/negative eligibility
train/validation/holdout site separation
```

## Current decision

```text
public_engineering_depth_sources_found = yes
approved_sentinel_1_known_depth_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

## Next public-only work

1. inspect downloadable Taipei attributes for completeness and units;
2. check whether installation or survey dates exist in companion datasets;
3. assess whether large corridor-level sections can be grouped without pretending individual pipes are satellite-resolvable;
4. continue searching for public uncertainty documentation;
5. keep engineering depth truth separate from Sentinel-1 support.
