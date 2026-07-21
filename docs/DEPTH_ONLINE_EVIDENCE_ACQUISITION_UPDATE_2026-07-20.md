# Depth Online Evidence Acquisition Update — 2026-07-20

Status: online evidence search advanced; no calibration record approved and app depth remains disabled.

This record supplements `docs/DEPTH_PUBLIC_EVIDENCE_CANDIDATE_REGISTER_2026-07-18.md`. It records newly verified source facts, corrections, candidate additions, and the exact information that still must be requested from source owners.

## Current decision

```text
online_search_status = useful_sources_found
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

The search found stronger physical-site evidence and practical contact routes. It did not find one public package that simultaneously supplies open raw data, independently measured depth-to-top values, numerical reference uncertainty, confirmed negative sites, acquisition dates, and multiple independent physical-site groups.

## Important correction — Sense-City negative interpretation

The Sense-City paper states that trench T1 contains no pipe. T1 is therefore a controlled **no-pipe trench**, not an undisturbed `confirmed_no_target` physical site.

T1 may be useful for separating pipe response from trench/backfill response within the same test site. It must not be imported as an independent confirmed-negative calibration site because:

1. the trench itself is a constructed subsurface disturbance;
2. it belongs to the same compact physical site as the positive pipe trenches;
3. it is not independent from the site's shared construction and soil context.

Reference measurements taken away from buried-object areas are useful ground-method background evidence, but they still belong to the same physical site and are not an independent negative holdout.

## Candidate P9 — Sense-City utility-mapping test site

Primary source:

- DOI `10.1016/j.measurement.2016.03.044`
- HAL identifier `hal-01592975`

Verified source facts:

- controlled utility-mapping facility inside the Sense-City demonstrator in France;
- facility scale approximately 25 m by 10 m, or 250 square metres;
- first Sense-City urban scenario entered service in January 2015;
- pipe zone includes six parallel trenches;
- T1 contains no pipe;
- T2 contains an air-filled PVC pipe reported at 14.4 cm depth;
- T3 contains an air-filled metallic pipe reported at 24.5 cm depth;
- T4 contains an air-filled PVC pipe reported at 34.5 cm depth;
- T5 contains an air- or water-filled pipe reported at 54.5 cm depth;
- T6 contains two air-filled pipes separated by 12 cm and reported at 24.5 cm depth;
- three GPR systems were used over the pipe area;
- reference GPR measurements were collected away from buried-object areas for soil characterization;
- no public machine-readable raw GPR archive was found during this search pass;
- no numerical installation, survey, or final depth-reference uncertainty was found;
- the reviewed online text does not resolve whether each reported pipe depth is depth to top, centre/axis, base, or another construction reference.

Current classification:

```text
physical_depth_provenance = installed_known_geometry
reference_definition = unresolved_top_vs_axis_vs_other
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
same_site_no_pipe_trench = yes_T1
independent_confirmed_negative_site = no
raw_public_dataset_confirmed = no
multiple_depth_levels = yes
site_scale = 25_m_by_10_m
multiple_physical_sites = no_single_compact_site
sentinel_1_target_level_support = no
source_evidence_usable = yes_for_ground_method_truth
method_research_usable = yes
private_pack_import_approved = no
priority = 1_request_data
```

Required next work:

1. request the construction drawing and exact depth-reference definition;
2. request installation or survey uncertainty;
3. request raw GPR files, acquisition metadata, and profile-to-trench mapping;
4. request the exact pipe/blade installation date or construction interval;
5. treat the entire site as one physical-site group;
6. retain T1 only as a same-site no-pipe trench control;
7. do not create target-level Sentinel-1 calibration rows from this compact site.

Official contact route found:

```text
Xavier Derobert
Université Gustave Eiffel geophysical test-site contact
xavier.derobert@univ-eiffel.fr
```

## Candidate P4 — Ahmadu Bello University exact actual-depth table recovered

Primary source:

- DOI `10.1016/j.envc.2024.100910`
- open access under CC BY 4.0

The paper's Table 2 explicitly labels the reference as `Depth to top (m)` and provides eight actual installed depths:

| Record | Target description | Depth to top (m) |
|---|---|---:|
| 1 | six empty plastic buckets | 0.80 |
| 2 | one horizontally buried empty steel drum | 0.80 |
| 3 | two horizontally buried empty steel drums | 1.00 |
| 4 | one vertically buried empty steel drum | 0.60 |
| 5 | six water-filled plastic buckets | 0.80 |
| 6 | car engine block | 1.20 |
| 7 | concrete block | 0.80 |
| 8 | two horizontally buried pipes | 0.50 |

Additional verified facts:

- the pre-burial investigation reported no major anomaly expected to interfere with the buried-target responses;
- post-burial ERT and VLF-EM data were collected;
- the underlying datasets are available from the authors on request;
- no numerical installation or final depth-reference uncertainty was reported in the reviewed source.

Qualification update:

```text
public_target_level_depth_table = extracted
reference_definition = ground_surface_to_target_top
verified_record_count = 8
pre_burial_ground_background = yes
raw_data_access = author_request
reference_uncertainty_m = not_reported
private_pack_import_approved = no_missing_uncertainty_and_source_package
```

Official request route from the article:

```text
Joseph Omeiza Alao
corresponding author
alaojosephomeiza@gmail.com
```

Request the construction sheet, installation uncertainty, pre- and post-burial raw ERT/VLF-EM files, acquisition dates, target dimensions, profile mapping, and permission/licence terms for research reuse.

## Candidate P10 — Teoloyucan Geophysical Test Site, Mexico

Primary source:

- DOI `10.1016/j.jappgeo.2021.104459`

Verified source facts:

- controlled site at the Teoloyucan Geomagnetic Observatory, UNAM;
- area 864 square metres, approximately 24 m by 36 m;
- 17 constructed subsurface structures buried at less than 2 m;
- regular and irregular geometries with horizontal and vertical elements;
- materials include adobe, wood, basalt, tezontle, concrete, reinforced concrete, plastic containers, and PVC;
- target geometry, dimensions, orientation, material properties, and site lithology are described as controlled and well characterized;
- the field was characterized before construction using magnetic gradiometry, electromagnetic induction, GPR, seismic refraction tomography, and ERT;
- holes were refilled and compacted with excavated material;
- datasets related to the article are available from the authors on request;
- no open machine-readable target table or raw-data archive was found during this pass;
- no numerical placement or depth-reference uncertainty was found in the reviewed online material.

Current classification:

```text
physical_depth_provenance = quantitatively_constructed_known_geometry
reference_definition = target_level_table_required
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
pre_construction_characterization = yes
raw_data_access = author_request
site_scale = 24_m_by_36_m
multiple_physical_sites = no_single_site
sentinel_1_target_level_support = no
source_evidence_usable = promising_pending_table
method_research_usable = yes
private_pack_import_approved = no
priority = 1_request_data
```

Required next work:

1. obtain the full target construction table or Figure 7 source data;
2. resolve depth-to-top versus centre/base reference for each structure;
3. obtain construction dates and pre/post acquisition dates;
4. obtain placement/survey uncertainty;
5. request the pre-construction and post-construction raw datasets;
6. retain the entire site as one physical-site group;
7. screen only whole-site or defensible large-section Sentinel-1 support, not target-level rows.

Official contact route found:

```text
Claudia Arango Galvan
Instituto de Geofisica, UNAM
claudiar@geofisica.unam.mx
```

## Existing candidate request routes

### P2 — IAG/USP

Official contact routes:

```text
Jorge Luis Porsani
porsani@iag.usp.br

IAG/USP Department of Geophysics
geofisica@iag.usp.br
```

Request:

- original target spreadsheet and construction drawings;
- numerical topographic/survey and placement uncertainty;
- raw GPR and other geophysical files;
- acquisition dates and profile-to-target mapping;
- reuse licence or written research permission.

### P3 — Texas A&M University–Corpus Christi

Official professional contact route found:

```text
Mohamed Ahmed
mohamed.ahmed@tamucc.edu
```

Request:

- target-level construction table with depth reference;
- target dimensions, orientation, line assignment, and location grid;
- survey/placement uncertainty;
- exact pre-installation and post-installation survey dates;
- raw GPR, magnetic, electrical, and other available files;
- construction drawings and as-built documentation;
- reuse licence or written research permission.

## Standard data-request fields

Every request should ask for the following without claiming that the source is already calibration-ready:

```text
1. target construction or installation table
2. exact depth-reference definition
3. numerical survey, placement, and final reference uncertainty
4. target dimensions, material, orientation, and host context
5. raw sensor files and file-format documentation
6. profile or acquisition mapping to targets
7. exact acquisition and installation dates
8. pre-installation or independently confirmed background data
9. licence or written permission for private research use
10. citation, version, and provenance information
```

## Import and scale rule

None of the newly reviewed sites is approved as a direct app calibration source yet.

A source may be useful for ground-method validation while remaining unusable for Sentinel-1 depth calibration. Compact targets inside one physical test site must not be treated as independent satellite-scale samples. The whole site must remain one leakage group, and no target-level Sentinel-1 row may be created when the sensor cannot spatially separate the targets.

## Next execution order

1. send or prepare the Sense-City request;
2. send or prepare the TAMUCC request;
3. send or prepare the Ahmadu Bello request;
4. send or prepare the IAG/USP request;
5. send or prepare the Teoloyucan request;
6. record every response and file version privately;
7. qualify uncertainty and depth-reference definitions before import;
8. continue searching for independent confirmed-negative physical sites;
9. import nothing until the dataset contract passes;
10. keep app depth disabled.

## Checklist

- [x] Re-check existing public candidates.
- [x] Verify Sense-City target depths and local no-pipe trench.
- [x] Correct the T1 interpretation: same-site no-pipe trench, not independent negative.
- [x] Extract the Ahmadu Bello eight-row depth-to-top table.
- [x] Add Teoloyucan as a new promising physical-site candidate.
- [x] Locate official contact routes for Sense-City, TAMUCC, Ahmadu Bello, IAG/USP, and Teoloyucan.
- [ ] Request source packages and uncertainty information.
- [ ] Receive and privately version the source packages.
- [ ] Find independent confirmed-negative physical sites.
- [ ] Approve only contract-complete records.
- [ ] Keep `app_depth_enabled = false`.
