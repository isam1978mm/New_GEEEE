# Blocker 2 — Maxey Flats Records Request Package — 2026-07-21

Status: prepared for external records retrieval. Maxey Flats remains `strong_candidate_under_review`; Blocker 2 remains unresolved and depth calibration is not authorized.

## Public-search result

The publicly indexed archives expose annual reports, cap-design summaries, EPA five-year reviews, and EPA's approval letter for the Kentucky remedial-action report. They do not expose the full April 2018 Final Closure Period Remedial Action Construction Report or its native survey/as-built attachments.

The DOE Legacy Management index explicitly directs users to submit a FOIA request for documents not available through its website. Kentucky EEC also provides a formal records-request route, but its Open Records Act inspection route is limited to eligible Kentucky residents and other defined eligible requesters. Therefore use the courtesy request first, then the appropriate formal route without claiming Kentucky residency unless actually eligible.

## Exact records needed

Request electronic native files where they exist, not only flattened PDF copies:

1. Complete April 2018 `Final Closure Period Remedial Action Construction Report` for the Maxey Flats Disposal Site, including every volume, appendix, attachment, certification, drawing set, CQA record, and survey deliverable.
2. Certified final as-built topographic survey for the final cap completed in September 2017.
3. Pre-construction, interim-cap, grading, subgrade, top-of-leveling-fill, and top-of-protective-soil survey surfaces used for construction quantity and thickness verification.
4. Native survey/CAD/GIS deliverables, preferably CSV/TXT point files, LandXML, TIN/DEM, DWG/DXF, SHP/GPKG, or equivalent machine-readable files.
5. Survey-control report stating horizontal coordinate system, horizontal datum, vertical datum, units, geoid model, benchmark/control-point descriptions, instrument types, survey dates, adjustment method, and stated horizontal/vertical accuracy.
6. Coordinates, monument descriptions, baseline elevations, and raw observations for all 34 cap-subsidence monitoring points.
7. Native 2018, 2019, 2020, and any later monitoring-point survey files, including field books, raw GNSS/total-station observations, adjusted coordinates/elevations, QA/QC reports, and surveyor certifications.
8. Drawings or GIS layers locating the 2020 repaired depression and all roads, drainage channels, basins, wells, sumps, monuments, and other construction-disturbed areas that must be excluded from a clean interior test polygon.
9. CQA thickness-verification records for leveling fill, protective soil, vegetative soil, geomembrane, geosynthetic clay liner, drainage geocomposite, and geogrid.
10. Any elevation-difference, settlement, subsidence, or as-built-versus-design map generated for the 2017 final cap.

## Courtesy-request draft

Subject: Request for Maxey Flats 2017 final-cap as-built and survey files

Hello,

I am conducting non-commercial technical research on whether publicly documented landfill-cap construction and repeat ground surveys can support independent satellite-method validation.

Could you please provide electronic copies of the complete April 2018 Final Closure Period Remedial Action Construction Report for the Maxey Flats Disposal Site, including its appendices, certified as-built drawings, native survey files, survey-control and accuracy documentation, and CQA records?

I am specifically seeking:

- the pre-construction/subgrade and certified 2017 final as-built cap surfaces;
- coordinates and baseline elevations for the 34 cap-subsidence monitoring points;
- native 2018, 2019, 2020, and any later repeat-survey files;
- horizontal and vertical datum, control points, instruments, adjustment method, and stated survey accuracy;
- the location of the 2020 repaired depression and other disturbed infrastructure areas; and
- cap-layer thickness-verification records.

Machine-readable files such as CSV/TXT, LandXML, CAD, GIS, TIN, or DEM are preferred where available, but PDF records are also useful.

This request does not seek personal information or restricted security information. Redacted copies are acceptable where necessary.

Thank you.

## Request routes

### Route 1 — Maxey Flats courtesy request

Send the courtesy request to the Maxey Flats Section contact listed by Kentucky EEC:

- Scott Wilburn, Maxey Flats Section
- `scott.wilburn@ky.gov`
- 606-783-8680

### Route 2 — Kentucky EEC records request

Official submission address:

- `EEC.KORA@ky.gov`

Important: Kentucky's official page states that the statutory inspection route is limited to eligible Kentucky residents and other specifically defined eligible requesters. Do not claim eligibility unless it is true. The agency states that electronic records have no production fee and that it generally responds in writing within five business days.

### Route 3 — DOE Office of Legacy Management / FOIA

The DOE Legacy Management archive lists EPA's approval of the Maxey Flats remedial-action report but not the report itself. Submit a DOE FOIA request through FOIA.gov and identify the component as the Department of Energy Office of Legacy Management. Include the exact report title, site name, April 2018 date, and the native survey/as-built attachment list above.

DOE Office of Legacy Management general contact:

- `LM@hq.doe.gov`
- 202-586-7550

DOE Headquarters FOIA contact listed by DOE:

- `foia-central@hq.doe.gov`

## Acceptance test when files arrive

Do not promote Maxey Flats to calibration-ready until all of the following pass:

```text
certified_2017_final_surface = present
pre_cap_or_subgrade_surface = present
common_horizontal_datum = verified
common_vertical_datum = verified
explicit_vertical_accuracy = adequate_for_target_signal
34_point_coordinates = present
repeat_epochs_native = present
survey_method_continuity = verified_or_quantified
2020_repair_mask = present
infrastructure_exclusion_mask = present
interior_clean_polygon = verified
cap_layer_thickness_truth = spatially_resolved_or_bounded
```

## Waiting for

```text
external_response_with_2018_construction_report
+ native_as_built_and_pre_cap_surfaces
+ 34_point_coordinates_and_raw_repeat_surveys
+ datum_control_accuracy_and_qa
+ repair_and_infrastructure_masks
```

## Next step

Send the courtesy request. If the files are not supplied, submit the same scoped request through the eligible Kentucky records route or DOE FOIA. On receipt, inventory hashes and formats first, then perform datum/accuracy QA before any satellite comparison.

## Public references

- Kentucky EEC Maxey Flats site page: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/maxey-flats-project/Pages/MaxeyFlatsSection.aspx`
- Kentucky archived Maxey Flats documentation: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/maxey-flats-project/Pages/maxey-flats-documentation.aspx`
- Kentucky EEC Open Records: `https://eec.ky.gov/pages/Open-Records.aspx`
- Kentucky Superfund contacts: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/Pages/Contact-Us-SF.aspx`
- DOE Legacy Management public-search index: `https://lmpublicsearch.lm.doe.gov/`
- DOE Legacy Management FOIA information: `https://www.energy.gov/lm/freedom-information-act-foia-and-privacy-act-requests`
- DOE FOIA submission information: `https://www.energy.gov/gc/freedom-information-act`
