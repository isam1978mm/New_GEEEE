# Depth Blocker 2 - Known Data Source Screening

**Date:** 2026-07-24  
**Branch:** `main`  
**Scope:** established datasets, registries, and controlled test facilities only  
**General candidate-site search:** remains closed

## Decision summary

| Source | Decision | Direct Sentinel-1 calibration status |
|---|---|---|
| Colorado School of Mines Geophysical Discovery Lab at Kafadar Commons | `method_research_only` | Not good to go |
| USACE Formerly Used Defense Sites GIS | `rejected_registry_only_and_out_of_family` | Not usable |
| National Pipeline Mapping System public data | `rejected_missing_depth_and_precision` | Not usable |

None of these three sources supplies a ready multi-site Sentinel-1 depth-calibration dataset.

## 1. Colorado School of Mines Geophysical Discovery Lab

### What is real and useful

The facility is a genuine controlled geophysical test site built beneath Kafadar Commons. Public Colorado School of Mines material documents benign engineered targets with construction-known dimensions and depths, including buried walls, pipes, a dipping concrete slab, mixed-material structures, boreholes, and a buried fiber-optic array.

The public record confirms, among other examples:

- a mixed-material structure about 25 ft by 25 ft with its top about 2 ft below the surface;
- archaeological-style walls beginning about 2 ft below the surface;
- a dipping concrete slab whose top varies from about 2 ft to about 7.2 ft;
- a buried fiber-optic array covering roughly 30 m by 90 m;
- an overall field reported in later Mines research as roughly 40 m by 100 m.

These are independent construction-known references and are valuable for ground-geophysics research and controlled-method testing.

### Why it does not clear the current Sentinel-1 gate

1. **The useful buried targets are small relative to Sentinel-1 resolution.** Sentinel-1 Interferometric Wide Swath imagery has approximately 5 m by 20 m ground resolution before later GRD processing effects. A roughly 7.6 m by 7.6 m target does not provide a clean isolated satellite-scale depth sample.
2. **The site contains many different nearby buried targets and utilities.** A Sentinel-1 pixel or analysis window would mix several structures and surface influences rather than represent one known depth.
3. **The entire site is one physical group.** It cannot provide independent train, validation, and holdout groups.
4. **No public numerical placement or survey uncertainty was found.** The public descriptions give nominal or approximate construction depths, but not a defensible numerical accuracy bound for calibration intake.
5. **No documented Sentinel-1-scale confirmed-negative area was found.** Ordinary nearby grass cannot be assumed target-free because the field contains many buried structures and services.
6. **The construction period is strongly confounded.** The lab was created during major campus construction, staging, trenching, and reconstruction of the field, so a pre/post satellite change would be dominated by surface works rather than depth alone.

### Decision

```text
source_evidence_usable = yes
method_research_usable = yes
direct_app_calibration_usable = no
classification = method_research_only
```

Kafadar Commons is the strongest of the three leads, but only as a controlled ground-geophysics benchmark or research-method site. It is not a direct Sentinel-1 depth-calibration site under the current contract.

Do not count it toward the three required independent Sentinel-1 site groups.

## 2. USACE Formerly Used Defense Sites GIS

### What the source contains

The public GIS is a national inventory of properties, projects, and program boundaries. It is useful for program-level indexing and site status.

### Why it is not usable here

- The GIS is a boundary and project registry, not a measured depth-to-target dataset.
- Site-level depth would still require separate administrative, engineering, or investigation records.
- The relevant munitions-related records are outside the project's approved benign finding family and must not enter the active calibration pack.
- It does not provide ready confirmed negatives, uncertainty, or independent split groups.

### Decision

```text
source_evidence_usable = registry_only
method_research_usable = no_for_active_pack
direct_app_calibration_usable = no
classification = rejected_registry_only_and_out_of_family
```

Do not continue site-by-site FUDS depth searching for this project.

## 3. National Pipeline Mapping System public data

### What the public source provides

The public viewer gives general information about transmission pipelines and related facilities.

### Why it is not usable here

- The public map is not intended to identify exact pipeline locations.
- The published minimum geospatial accuracy is approximately plus or minus 500 ft, far too coarse for the required site matching.
- The public attribute set does not provide a usable depth-of-cover calibration field.
- More detailed access is restricted to eligible government and pipeline-operator users and remains limited to their jurisdiction or operations.
- Therefore it cannot provide public measured depth, uncertainty, mapped target geometry, confirmed negatives, and independent splits.

### Decision

```text
source_evidence_usable = no_for_depth
method_research_usable = no
direct_app_calibration_usable = no
classification = rejected_missing_depth_and_precision
```

## Final result

```text
known_source_screening_completed = 3
new_direct_calibration_sources = 0
method_research_sources = 1
rejected_sources = 2
public_candidate_site_search = still_closed
depth_blocker_2 = still_blocked
```

## What remains worth looking for

The useful source class is now narrower:

> an established **multi-site benign controlled-test or engineering dataset** containing measured depth to the top of buried features, numerical uncertainty, mapped geometry, dates, and independently documented no-target areas.

This is evidence-source discovery, not a restart of broad site-by-site candidate searching.

## Sources reviewed

- Colorado School of Mines Department of Geophysics facility pages and the Geophysical Discovery Lab project page.
- Colorado School of Mines research material describing the buried fiber array and field dimensions.
- ESA Sentinel-1 instrument documentation.
- USACE official FUDS GIS and program documentation.
- PHMSA official NPMS public-viewer and access documentation.
