# Blocker 2 — Stage-1 Palo Alto Candidate — 2026-07-21

Status: Stage 1 screened. Palo Alto Landfill / Byxbee Park, California, is classified as `rejected_for_direct_calibration_method_only`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The former Palo Alto municipal landfill occupies approximately 126–137 acres and stopped accepting waste in 2011.
- Final landfill closure and cap construction were completed in 2015.
- Closure occurred incrementally in four phases rather than as one new whole-landfill cap event.
- California rules require an as-closed topographic baseline and may require five-year iso-settlement mapping against that baseline.
- Public City material confirms that landfill management includes monitoring settlement and importing soil or regrading areas of excessive settlement to prevent ponding and seepage.
- No publicly extractable 2020 iso-settlement map, numerical survey-accuracy statement, or clean before/after surface table was located in the indexed City, Water Board, or CIWQS records reviewed.

## Classification

```text
candidate_id = N1-17
candidate_state = rejected_for_direct_calibration_method_only
sentinel_1_era_cap_event = pass_2015_completion
whole_landfill_cap = fail_incremental_multi_phase_closure
large_analysis_footprint = pass
post_closure_review = pass
as_built_depth_to_top = expected_by_rule_but_not_publicly_extracted
numerical_survey_uncertainty = unresolved
observation_date_settlement = required_framework_but_public_map_not_found
clean_s1_experiment_unit = fail
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject Palo Alto for direct depth calibration.

The site is valuable as a method reference because California requires baseline topography and periodic settlement mapping. It is not a clean third calibration site because the landfill was capped in multiple phases over decades, final closure was integrated with park conversion, and later maintenance includes soil import and regrading of settlement areas. These overlapping changes prevent a single unambiguous cap-depth event from being isolated from Sentinel-1 observations.

Do not infer settlement values or survey accuracy from the regulatory requirement alone. The actual baseline and five-year settlement products must be obtained before any method-only analysis can proceed.

## Waiting for

```text
public_as_closed_topographic_baseline
+ 2020_or_later_iso_settlement_map
+ survey_method_and_accuracy_metadata
+ phase_IIC_exact_footprint_and_completion_dates
```

These records would support a method study only unless a clean, unchanged sub-area can be demonstrated.

## Next step

Continue screening recent single-unit landfill or CCR closures where the cap was constructed in one bounded event, with no waste relocation or later development, and where both as-built and repeat topographic surveys are directly accessible.

## Public references

- City of Palo Alto Byxbee Park Master Plan: `https://www.cityofpaloalto.org/files/assets/public/v/1/community-services/parks-and-open-space/baylands/bccp_finalbyxbeeparkmasterplan_20190307.pdf`
- California CEQAnet Phase IIC closure record: `https://ceqanet.lci.ca.gov/2013082019`
- San Francisco Bay Regional Water Board draft updated requirements: `https://www.waterboards.ca.gov/rwqcb2/board_info/agendas/2016/June/PaloAlto/Draft_T_O.pdf`
- California Title 27 settlement-mapping rule summary: `https://www.law.cornell.edu/regulations/california/27-CCR-21090`
- California CIWQS Palo Alto Landfill facility record: `https://ciwqs.waterboards.ca.gov/ciwqs/readOnly/CiwqsReportServlet?placeID=257681&reportName=facilityAtAGlance`
