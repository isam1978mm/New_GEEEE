# Depth International Test-Site Inventory Screen — 2026-07-21

Status: a finite international inventory of major geophysical test sites was screened using public sources. No people were contacted, no user research was requested, no calibration row was approved, and app depth remains disabled.

## Purpose

The goal was to determine whether the project had missed an established, large, post-Sentinel-1 controlled site with public known-depth evidence.

Screening rules:

1. open-air physical site;
2. construction after Sentinel-1 became available in 2014, or a separately dated later installation;
3. area large enough for a defensible whole-site or large-section Sentinel-1 unit;
4. independently documented installed depth;
5. no direct transfer of compact target rows to satellite-scale samples;
6. public source package or traceable public metadata;
7. no simultaneous major surface redevelopment that prevents attribution.

## Inventory source

The 2023 review `Development of geophysical test sites and its impacts on research and education activities` compares eleven major international controlled sites.

The review table includes these establishment years:

| Site | Review-listed year | Sentinel-era classification |
|---|---:|---|
| Cavendish Laboratory | 1967 | pre-Sentinel |
| Western Michigan University | 1995 | pre-Sentinel |
| University of Leicester | 1995 | pre-Sentinel |
| Nantes / IFSTTAR | 1996 | pre-Sentinel |
| IAG/USP | 1998 | pre-Sentinel |
| Devine Test Site | 1998 | pre-Sentinel |
| Asian Institute of Technology | 2005 | pre-Sentinel |
| Kansas State University | 2007 | pre-Sentinel |
| 2016 Brazilian review entry | 2016 | post-Sentinel but compact |
| TAMUCC | 2020 | post-Sentinel and already screened |
| Teoloyucan | 2020 | post-Sentinel, phased date record unresolved |

## Elimination result

### Eight pre-Sentinel sites

Eight of the eleven reviewed sites were established before 2014. They may support ground-method research, stable-site testing, or historical method comparison, but they cannot provide a clean Sentinel-1 before-installation period unless a separately documented later installation exists.

No publicly traceable, isolated, satellite-scale post-2014 addition was recovered for these eight sites during this pass.

### 2016 Brazilian review entry

The review lists a Brazilian site established in 2016 with approximate dimensions of 10 m by 24 m and target depths around 0.3 m to 0.5 m.

Classification:

```text
post_sentinel_construction = yes
approximate_area = 240_square_metres
satellite_scale_support = insufficient
whole_site_mixed_target_risk = high
direct_sentinel_depth_calibration = no
```

The site is too compact to create an independent Sentinel-1 calibration unit. The institution and coordinate details in secondary summaries are not sufficiently consistent to support stronger claims, so this screen retains only the review-listed size, year, and depth range.

### TAMUCC

TAMUCC is the only reviewed modern site for which the project has already completed a full public construction-date qualification, Sentinel-1 coverage check, exact acquisition match, private feature extraction, and controlled site-background screen.

Result:

```text
site_status = unexplained_radar_anomaly_research_case
known_depth_calibration_status = not_approved
reason = whole_site_mixed_targets_and_missing_reference_uncertainty
```

Repeating the same site analysis will not create independent depth ground truth.

### Teoloyucan

The review lists Teoloyucan as established in 2020. A 2017 conference abstract states that an initial controlled shallow site had already been constructed, while the 2021 primary paper describes the completed 17-structure facility.

Safe classification:

```text
initial_controlled_site_public_by = 2017_12
review_listed_establishment_year = 2020
final_construction_phase_mapping = unresolved
exact_installation_date = not_recovered
site_area = 864_square_metres
whole_site_group_only = yes
open_raw_package = no
numerical_uncertainty = not_reported
direct_sentinel_depth_calibration = no
```

The conflicting years are treated as evidence of phased development, not as permission to choose a convenient event date.

## Inventory conclusion

The finite review inventory does not reveal a missed large modern calibration site:

```text
reviewed_site_count = 11
pre_sentinel_site_count = 8
post_sentinel_compact_site_count = 1
post_sentinel_already_screened_site_count = 1
post_sentinel_phase_unresolved_site_count = 1
new_approved_calibration_sites = 0
```

This closes the main international-review branch. Continuing to cycle through the same established university test sites is unlikely to produce the missing calibration pack.

## What remains scientifically missing

No reviewed site supplies all of:

1. a clean satellite-scale positive unit;
2. independently documented depth-to-top truth;
3. numerical installation or survey uncertainty;
4. an exact construction event or matched acquisition interval;
5. an independent confirmed-negative physical site;
6. enough physical-site groups for training, validation, and holdout;
7. public or locally available source data suitable for the frozen feature contract.

## Next public-only branch

The search should now move outside the standard university test-site inventory and focus on:

1. large civil-engineering installations built after 2014 with public as-built depth records;
2. isolated utility corridors or buried tanks whose construction is separable from wider surface redevelopment;
3. excavated archaeological features with independently surveyed geometry and repeatable Sentinel-1 observations;
4. public before/after construction records that include stable adjacent negative areas;
5. sites large enough for whole-site or large-section Sentinel-1 windows.

The project must continue to reject compact pits, covered laboratories, mixed target fields treated as multiple rows, and studies that infer depth from the same radar signal used as a feature.
