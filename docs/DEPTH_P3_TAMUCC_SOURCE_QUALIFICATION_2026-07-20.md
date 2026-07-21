# Depth P3 TAMUCC Source Qualification — 2026-07-20

Status: partial source qualification for the private local depth-research workflow. This document records verified public facts and unresolved evidence gaps for Candidate P3. It does not approve private-pack import, model fitting, or app depth output.

## Candidate

```text
candidate_id = P3
authoritative_name = Texas A&M University-Corpus Christi Geophysical Test Site
primary_article_doi = 10.1190/tle40030208.1
official_project_page_date = 2020-11-24
```

## Verified facts

The reviewed official university page and article metadata support the following:

- the controlled site measures approximately 50 m by 50 m;
- construction occurred from February through March 2020;
- the field laboratory was completed on 2020-03-04;
- construction included a survey for existing subsurface objects before excavation and target placement;
- installed targets include steel drums, plastic drums, plastic buckets, steel pipes, and well covers;
- targets are distributed along seven lines and grouped by material type;
- published descriptions state a known-depth range of approximately 0.5 m to 3.0 m;
- the article states that target types, locations, orientations, and depths are documented;
- the site is one compact physical-site group, not seven independent sites;
- the construction occurred during the Sentinel-1 mission era, allowing a possible whole-site pre/post experiment after coverage and geometry checks.

## Evidence not recovered in this pass

The following were not available in the public sources reviewed:

- the target-by-target construction table;
- exact target-level orientation and depth values;
- an explicit statement for every record that depth means depth to target top rather than centre, base, or excavation depth;
- numerical placement, survey, surface-reference, or final depth uncertainty;
- a public machine-readable target spreadsheet;
- a public raw geophysical dataset with acquisition metadata.

The primary article is discoverable, but the full target table was not publicly accessible through the reviewed pages. The current route for those materials is an author or institutional source request.

## Existing event-window decision

The existing conservative whole-site policy remains:

```text
construction_start = 2020-02
construction_complete_date = 2020-03-04
pre_event_window_end_exclusive = 2020-02-01
construction_transition_end_exclusive = 2020-04-01
post_event_window_start = 2020-04-01
```

February and March 2020 remain excluded from the first comparison because excavation, placement, grading, and surface restoration may contaminate the signal.

## Scale decision

The completed scale screen remains binding:

```text
sentinel_1_target_level_separation = not_supported
whole_site_pre_post_screen = high_priority_candidate
approved_experiment_unit = physical_site_or_large_isolated_section
```

The individual targets must not be treated as independent Sentinel-1 depth rows.

## Current classification

```text
physical_depth_provenance = installed_known_depth_reported
reference_definition = unresolved_target_level
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
pre_installation_survey_documented = yes
construction_event_date = verified
sentinel_1_mission_era = yes
source_evidence_usable = yes_as_controlled_site_lead
method_research_usable = yes
direct_app_calibration_usable = no_target_level_scale_not_supported
private_pack_import_approved = no_missing_target_table_reference_definition_and_uncertainty
candidate_state = evidence_verified_pending_source_materials
```

## Qualification decision

P3 remains the highest-priority current candidate for a whole-site Sentinel-1 pre/post experiment because its physical installation event occurred during the mission era and a pre-installation survey is documented.

It is not ready for private calibration-pack import. Import remains blocked until the target table, target-level depth reference, source-backed uncertainty, and required record metadata are recovered.

A successful whole-site pre/post change experiment would not by itself create target-level numerical depth labels. It would establish whether the controlled installation produces a measurable approved-feature change at Sentinel-1 scale.

## Next actions

1. Request the target construction table and any supplementary site plan from the article authors or university custodian.
2. Request the definition used for each target depth and any placement or survey tolerance.
3. Request available raw geophysical data and acquisition dates.
4. Create private site and background polygons outside Git.
5. Run the existing aggregate Sentinel-1 coverage checker for the frozen pre/post windows.
6. Confirm comparable orbit direction, relative-orbit group, mode, polarisation, season, and valid-pixel support.
7. Keep the full site in one leakage group.
8. Update the main candidate register only with newly verified source facts; never invent target values or uncertainty.

## Current decision

```text
P3_source_review = partially_completed
P3_target_table = blocked_requires_source_request
P3_reference_uncertainty = blocked_requires_source_request
P3_sentinel_1_coverage = not_yet_run
P3_private_pack_import = not_approved
P3_whole_site_pre_post_research = active_next_step
app_depth_enabled = false
```
