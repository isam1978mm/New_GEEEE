# Depth Public Controlled-Site Timeline Update — 2026-07-21

Status: public-only evidence screening continued. No people were contacted, no user research or survey was requested, no calibration row was approved, and app depth remains disabled.

## Current decision

```text
public_only_search = active
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

This note consolidates the strongest public timing and scale evidence for Ahmadu Bello, Teoloyucan, University of Twente, and Western Michigan. Publication dates are not treated as installation dates. When an exact field date is absent, only a defensible public interval is recorded.

## Site T1 — Ahmadu Bello University Geophysics Test Site

Primary public sources:

- proposed-site characterization published in 2019;
- VLF-EM controlled-site study, DOI `10.1007/s42452-024-05650-6`;
- depth-comparison study, DOI `10.1016/j.envc.2024.100910`;
- construction article, DOI `10.1007/s12517-024-12039-7`.

Verified timeline:

1. The 2019 work described the area as a proposed test site and stated that targets would be installed after pre-construction characterization.
2. The VLF-EM preprint was publicly posted on 2023-09-05 and already contained both natural-ground and post-installation measurements.
3. The journal version was received on 2023-09-13.
4. Therefore, the added-target installation and those pre/post measurements occurred before September 2023.
5. The exact burial day or narrow construction campaign was not recovered from the public material.

Verified site facts:

- controlled area approximately 55 m by 55 m;
- known benign civil and environmental target materials installed at multiple depths and orientations;
- public studies report depth-to-top values and a broader site depth range of approximately 0.6 m to 3 m;
- public pre-installation and post-installation ground-method comparisons exist;
- the public studies report that target size, host-soil variability, and excavation disturbance affect the measured response;
- source datasets remain available by request rather than as an open archive;
- numerical installation or final depth-reference uncertainty is not public.

Classification:

```text
post_sentinel_construction = yes
public_installation_interval = after_2019_and_before_2023_09_05
exact_installation_date = not_recovered
pre_post_ground_measurements = yes
open_raw_package = no
numerical_reference_uncertainty = not_reported
whole_site_group_only = yes
sentinel_1_depth_calibration_approved = no
```

## Site T2 — Teoloyucan Geophysical Test Site

Primary public sources:

- 2017 conference abstract, `Site characterization and construction of a controlled shallow test site in central Mexico for archaeological and engineering applications`;
- construction article, DOI `10.1016/j.jappgeo.2021.104459`;
- 2023 international test-site review;
- 2023 mapping article, DOI `10.1016/j.jappgeo.2023.105123`.

Verified timeline:

1. A December 2017 conference abstract states that an initial controlled shallow test site had been constructed at the UNAM Teoloyucan observatory.
2. The 2023 international review lists Teoloyucan with an establishment year of 2020.
3. The 2021 primary paper describes the completed 17-structure facility and its pre-construction characterization.
4. The public record therefore supports phased development: an initial controlled site existed by December 2017, while the later fully documented facility may have been completed afterward and is listed as 2020 by the review.
5. The public sources do not map the construction phases or exact campaign dates well enough to assign a single installation date.

Verified site facts:

- controlled area approximately 24 m by 36 m, or 864 square metres;
- 17 constructed structures buried below approximately 2 m;
- five methods characterized the field before construction;
- structures contain mixed materials, geometries, and depths;
- the entire compact site must remain one physical-site group;
- source datasets are available by request rather than through an open archive;
- numerical placement or depth-reference uncertainty is not public.

Classification:

```text
post_sentinel_construction = yes
initial_public_site_bound = by_2017_12
review_listed_establishment_year = 2020
final_phase_mapping = unresolved
exact_installation_date = not_recovered
pre_construction_characterization = yes
open_raw_package = no
numerical_reference_uncertainty = not_reported
whole_site_group_only = yes
sentinel_1_depth_calibration_approved = no
```

## Site T3 — University of Twente Utility Mapping Site

Primary public sources:

- University of Twente construction notice dated 2023-10-04;
- UT FieldLab public experiment and opening pages;
- public Utility Mapping Site description.

Verified timeline and scale:

- wider FieldLab construction started in the last week of September 2023;
- the project occupies approximately 1.7 hectares;
- the utility test volume is publicly described as approximately 50 m by 30 m by 2 m;
- the utility area contains ten strips, each approximately 30 m by 5 m;
- the site includes multiple soil and surface conditions;
- public pages confirm that utility measurements were underway before the October 2025 opening;
- the detailed as-built utility design and individual utility depths are not public.

Scientific limitation:

The utility installation occurred as part of a much larger continuing FieldLab construction. A whole-site Sentinel-1 before/after difference would mix the utility test bed with grading, infrastructure installation, paving, landscaping, and other construction. Individual strips are narrow and internally mixed, so they cannot become independent target-level Sentinel-1 depth rows.

Classification:

```text
post_sentinel_construction = yes_2023_onward
large_public_event_area = yes
clean_isolated_buried_installation = no
public_as_built_depth_table = no
surface_redevelopment_confounder = yes
sentinel_1_depth_calibration_approved = no
useful_as_confounder_case = yes
```

## Site T4 — Western Michigan University Asylum Lake Geophysical Test Site

Primary public source:

- Western Michigan University Near Surface Geophysics Lab page.

Verified facts:

- the public university page states that installations began in 1995;
- the site is large and has been used extensively for training and ground-method research;
- public target layouts and depth information exist in teaching material;
- no public evidence of a separate, isolated, satellite-scale post-2014 installation event was recovered during this pass.

Classification:

```text
original_installation = 1995
clean_sentinel_1_pre_installation_period = no
public_later_isolated_event = not_recovered
method_research_usable = yes
stable_site_or_falsification_research = possible
sentinel_1_depth_calibration_approved = no
```

## Cross-site conclusion

The four sites improve the evidence map but do not populate the calibration pack:

```text
Ahmadu_Bello = post_Sentinel_but_exact_date_and_open_package_missing
Teoloyucan = phased_2017_to_2020_public_record_exact_dates_unresolved
Twente = dated_large_event_but_surface_construction_confounder
Western_Michigan = large_known_site_but_pre_Sentinel_installation
```

No site currently supplies all required elements:

1. independently documented depth-to-top truth;
2. numerical uncertainty;
3. open or locally available source package;
4. clean Sentinel-1-scale positive unit;
5. independent confirmed negative unit;
6. multiple physical sites suitable for train, validation, and holdout splits.

## Next public-only work

1. search public university, construction, and project archives for an exact Ahmadu Bello installation date;
2. search public UNAM project and conference archives for the Teoloyucan construction phases;
3. search for post-2014 open-air controlled sites with isolated large installations and public as-built depths;
4. search public civil-project as-built records for large buried structures whose surface work is independently separable;
5. reject direct transfer from small ground-method targets to Sentinel-1 depth labels;
6. do not contact authors or ask the user to conduct research.
