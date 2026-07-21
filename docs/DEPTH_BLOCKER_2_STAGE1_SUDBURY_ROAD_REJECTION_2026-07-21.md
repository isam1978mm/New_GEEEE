# Blocker 2 — Stage-1 Sudbury Road Rejection — 2026-07-21

Status: rejected for direct depth calibration. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, or app-depth enablement is authorized.

## Verified public facts

- Washington Ecology identifies Sudbury Road Landfill as a 125-acre municipal landfill with active lined disposal and older unlined disposal areas.
- Ecology states that a May 2015 Consent Decree led to remedial construction completed in 2017.
- The 2017 remedial action included landfill-gas controls in three distinct areas, improved cover over two areas, improved grading in one area, and stormwater controls along the northern edge.
- A separate Area 6 soil-cap closure and gas-control project had already been completed in 2010 and became operational in January 2011.
- Ecology publicly lists a 2017 Construction Quality Assurance Certification Report and a 2022 periodic review.
- The public index does not expose a later repeat topographic or settlement survey tied to the 2017 work. The 2022 review summary focuses on groundwater cleanup performance.

## Classification

```text
candidate_state = rejected_mixed_remedial_construction
sentinel_1_era_construction = pass
cqa_report_exists = pass
single_whole_cap_event = fail
waste_left_in_place = likely_but_not_sufficient
final_as_built_contours = unresolved
later_repeat_surface_survey = not_found
clean_s1_experiment_unit = fail
```

## Rejection basis

Sudbury Road is not a clean one-event cap experiment. The 2017 remedy combined multiple cover-improvement areas with gas controls, separate grading, and stormwater construction, while one major closure area had already been capped years earlier. A Sentinel-1 before/after signal would therefore mix several construction effects and different closure histories.

The presence of a CQA report and a five-year review is not enough. The required later measured surface survey was not found, and the public periodic-review summary does not provide repeat elevation data.

## Decision

Reject Sudbury Road for direct depth calibration. Retain only as a method/source-structure example showing that a CQA report and later periodic review can coexist without yielding a usable clean survey pair.

## Next step

Continue screening completed post-2015 single-unit closures with:

```text
one closure footprint
+ no earlier phased cap over the same analysis area
+ public final as-built contours or survey points
+ explicit datum and numerical survey accuracy
+ later repeat topographic or settlement survey
```

## Public references

- Washington Ecology site and document index: `https://apps.ecology.wa.gov/cleanupsearch/site/2485`
- 2017 CQA report listing: `https://apps.ecology.wa.gov/cleanupsearch/document/64264`
- 2022 periodic review listing: `https://apps.ecology.wa.gov/cleanupsearch/document/113837`
- City of Walla Walla records describing the 2010 Area 6 closure and later remedial work: `https://agendas.ci.walla-walla.wa.us/print_all.cfm?id=&reloaded=true&seq=211`
