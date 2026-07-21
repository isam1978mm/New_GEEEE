# Depth Post-Sentinel Construction-Date Screen — 2026-07-21

Status: public-only evidence screening continued. No author contact, user survey, private review, or calibration import occurred. App depth remains disabled.

## Purpose

This screen asks one narrow question:

```text
Was a controlled physical site constructed after Sentinel-1 became available,
and is there a public, independently traceable before/after interval?
```

A publication year is not treated as a construction date. A site passes only when the public record supports a real construction interval and does not confound the buried installation with unrelated major surface reconstruction.

## Current result

```text
exact_post_sentinel_construction_dates_confirmed = 2
clean_new_candidate_pre_post_windows_approved = 0
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
app_depth_enabled = false
```

The two exact post-Sentinel construction cases currently documented are:

1. TAMUCC, completed on 2020-03-04, already screened in the private matched Sentinel-1 workflow;
2. Colorado School of Mines Geophysical Discovery Lab, constructed during 2017, but rejected as a clean buried-target pre/post case because construction coincided with major building work, field staging, trenching, and full surface rebuilding.

## Site D1 — Ahmadu Bello University Geophysics Test Site

Public sequence:

- a 2019 paper describes the area as a proposed geophysical test site and states that objects would be buried after pre-construction characterization;
- a February 2023 paper describes the 55 m by 55 m site as developed and reports pre- and post-burial geophysical results;
- later 2024 papers provide installed depth-to-top records and additional post-burial surveys.

Qualification:

```text
sentinel_1_era_construction = yes
public_construction_interval = after_2019_proposed_site_before_2023_completed_report
exact_burial_date = not_publicly_recovered
pre_construction_ground_characterization = yes
post_construction_ground_surveys = yes
site_scale = 55_m_by_55_m
clean_sentinel_pre_post_window = not_yet_approved
```

Reason not approved yet:

- the exact burial date or narrow construction interval is absent from the public searchable sources;
- public data packages and numerical installation uncertainty remain unavailable;
- the full site mixes several materials and depths, so it can only be screened as one whole physical-site group.

## Site D2 — Teoloyucan Geophysical Test Site

Public sequence:

- the site was supported by UNAM DGAPA-PAPIIT projects beginning with project IN105716 and later IN108219;
- five non-invasive methods characterized the field before construction;
- 17 structures were then constructed, buried, levelled, and compacted;
- the completed construction was reported in a 2021 article;
- later 2023 surveys mapped the completed structures.

Qualification:

```text
sentinel_1_era_construction = likely_yes
public_construction_interval = project_period_after_2016_before_2021_publication
exact_burial_date = not_publicly_recovered
pre_construction_ground_characterization = yes
post_construction_ground_surveys = yes
site_scale = 24_m_by_36_m
clean_sentinel_pre_post_window = not_yet_approved
```

Reason not approved yet:

- the public full text describes construction but does not state an exact date;
- the area is compact and contains 17 mixed structures;
- data are listed as available by request, not as an open archive;
- numerical placement uncertainty is not public.

## Site D3 — Sense-City utility test bed

Public sequence:

- the design of the utility test bed was already published in 2010;
- the test bed was integrated into the Sense-City demonstrator before the 2016 measurement paper;
- the first demonstrator scenario was in service by January 2015.

Qualification:

```text
sentinel_1_clean_pre_period = no_reliable_public_interval
construction_event_suitable_for_sentinel_pre_post = no
same_site_no_pipe_trench = yes_but_constructed_disturbance
site_scale = 25_m_by_10_m
```

Decision:

Sense-City remains useful for ground-method validation but is rejected as a clean Sentinel-1 construction experiment.

## Site D4 — Colorado School of Mines Geophysical Discovery Lab

Public facts:

- the laboratory was installed during the 2017 construction and redevelopment of Kafadar Commons;
- a public university page states that installation occurred during the CoorsTek construction window;
- public benign civil and archaeological targets include a long dipping pipe, buried wall segments, a large dipping concrete slab, a mixed-material structure, a sand bed, a granite block, boreholes, and buried sensing cable;
- several target dimensions and depth ranges are publicly documented;
- a 27 m by 90 m buried sensing grid was later used for open seismic research.

Qualification:

```text
sentinel_1_era_construction = yes_2017
large_documented_targets = yes
public_target_descriptions = yes
major_surface_reconstruction_concurrent = yes
clean_buried_target_pre_post = no
```

Decision:

The site is retained only as a confounder and method-research case. Its pre/post satellite change cannot be assigned to buried targets because the field was simultaneously used for building staging, trenching, grading, and full landscaping.

## Archive-query boundary

Copernicus Data Space publicly documents STAC and catalogue APIs for Sentinel-1 metadata searches. In this environment, direct authenticated catalogue execution was not available. No acquisition count, orbit, or matched-image claim is therefore made for the new candidate sites.

A site must first recover an independently sourced construction interval before archive matching is scientifically useful. Archive availability alone cannot substitute for the missing event date.

## Current priority

```text
priority_1 = recover_public_exact_Ahmadu_Bello_construction_date
priority_2 = recover_public_exact_Teoloyucan_construction_date
priority_3 = continue_search_for_post_2014_large_controlled_sites
priority_4 = reject_surface_reconstruction_confounders
```

## Checklist

- [x] Preserve TAMUCC as the only exact clean post-Sentinel event screened so far.
- [x] Establish Ahmadu Bello public construction interval without guessing an exact date.
- [x] Establish Teoloyucan public construction interval without guessing an exact date.
- [x] Reject Sense-City as a clean Sentinel-1 construction case.
- [x] Classify Colorado Mines as a surface-reconstruction confounder.
- [ ] Recover exact public construction dates for Ahmadu Bello and Teoloyucan.
- [ ] Confirm open Sentinel-1 metadata only after event dates are traceable.
- [ ] Approve no calibration row until uncertainty, scale, and grouping gates pass.
