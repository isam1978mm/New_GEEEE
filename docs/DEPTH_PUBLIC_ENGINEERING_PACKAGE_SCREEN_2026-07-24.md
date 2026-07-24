# Public Engineering Package Screen for Numerical Depth — 2026-07-24

**Branch:** `main`  
**Status:** bounded named-document review complete  
**Broad generic search:** stopped  
**Calibration-ready public packages:** 0

## Plain-English purpose

This screen checks a limited set of official engineering records that could become numerical-depth calibration evidence.

A site counts only when the records support:

1. an exact mapped physical area;
2. actual measured depth or installed thickness to the top of the reference material;
3. numerical survey accuracy, uncertainty, or a source-supported bounded interval;
4. construction and observation dates;
5. an independently confirmed no-target comparison area;
6. separation from the other train, validation, and holdout site groups.

## 1. Elk Plain County Shop

**Classification:** strongest near-complete public evidence hold; not calibration-ready.

Official records establish:

- contaminated soil was consolidated and capped in August 2023;
- the cap consists of six feet of compacted clean soil over an orange warning layer;
- an official as-built comparison map contains surveys of the contaminated-soil surface before capping and the clean-soil surface after capping;
- the map contains many measured thickness values spanning approximately 6.00 to 11.08 feet;
- Ecology accepted the submitted cap survey figure as addressing its request;
- the capped area is a separately identified approximately 5.31-acre parcel;
- a later progress report states that no further site-characterization work was performed or planned and no anticipated site changes were reported through December 2025;
- Pierce County Record of Survey `202502055001` was recorded for the capped parcel;
- the cap is protected by an environmental covenant and long-term inspection requirements;
- the official site index records No Further Action and a recorded environmental covenant in 2026.

Current evidence state:

```text
actual_as_built_thickness_values = yes
mapped_capped_parcel = yes
regulator_acceptance = yes
post_cap_no_reported_change_window_through_2025_12 = yes
numerical_survey_accuracy = no
confirmed_no_target_comparison = no
```

Still missing:

- a numerical vertical survey accuracy, closure tolerance, or source-supported uncertainty interval;
- an independently confirmed no-target comparison footprint with a similar surface setting;
- final Sentinel-1 date selection that excludes construction, grading, and early vegetation-establishment periods.

The cap map is labelled `REVIEW SET`. Ecology's acceptance and values displayed to hundredths of a foot do not by themselves establish measurement uncertainty.

**Decision:** first retrieval target. No calibration row may be created yet.

## 2. Sudbury Road Landfill

**Classification:** strongest independently checked constructed-minimum-depth hold; not calibration-ready.

Official construction and quality-assurance records establish:

- construction was completed in 2017;
- evapotranspiration covers were constructed over Areas 2 and 5;
- the completed covers used a minimum 4.8-foot-thick layer of native soil;
- the subgrade was surveyed by a Professional Land Surveyor;
- the finish grade was surveyed by a Professional Land Surveyor;
- digital terrain models of the subgrade and finish-grade surfaces were compared to confirm the minimum 4.8-foot cover;
- several test pits across Areas 2 and 5 visually checked that the cover was at least 4.8 feet thick over municipal solid waste;
- the construction-quality plan required grade control, cover-thickness verification, and a final as-built survey;
- the acceptance rule required the Area 2 and Area 5 cover to be 4.8 feet minimum;
- the final professional engineer reviewed and verified the as-built drawings before certification.

Current evidence state:

```text
actual_constructed_minimum_depth = yes
professional_subgrade_survey = yes
professional_finish_grade_survey = yes
surface_model_comparison = yes
test_pit_cross_check = yes
exact_per_area_depth_values_extracted = no
numerical_survey_accuracy = no
confirmed_no_target_comparison = no
```

This is stronger than a design specification. It proves that the completed cover was checked against a 4.8-foot minimum. It still does not supply a defensible exact depth value or error bound for each satellite-scale footprint.

Still missing:

- the numerical values or thickness surface from the certified as-built drawings;
- a site-specific numerical survey accuracy, vertical tolerance, or uncertainty interval;
- an independently confirmed no-target comparison area;
- a final unchanged Sentinel-1 observation window.

**Decision:** second retrieval target. Do not convert the 4.8-foot lower bound into a false exact depth label.

## 3. Go East Corp Landfill

**Classification:** strong completed-cover and record-drawing hold; not calibration-ready.

Official records establish:

- the landfill was consolidated, regraded, and closed from March 2021 through July 2022;
- the landfill footprint was reduced from about 9.6 acres to about 6 acres;
- closure was completed under current limited-purpose-landfill requirements;
- the applicable presumptive cover system includes a geomembrane and at least two feet of cover soil;
- the final cover was completed in 2022;
- a construction quality-assurance report, construction summary, and separate record drawings are publicly listed;
- a July 2022 drone flight documented construction of the final cover;
- post-closure monitoring and an environmental covenant are in place.

Still missing from the material successfully extracted:

- actual as-built thickness values or matched top-and-bottom elevations from the record drawings;
- numerical survey accuracy, vertical control, or accepted construction tolerance;
- an independently confirmed no-target comparison area;
- a clean Sentinel-1 period unaffected by surrounding residential development, stormwater works, access construction, and vegetation work.

**Decision:** retain as the third retrieval target. The two-foot value remains a regulatory minimum until the as-built measurements are extracted.

## 4. Recomp of Washington

**Classification:** documented installed-depth hold; not calibration-ready.

Official records establish:

- the ash landfill was closed by placing a two-foot-thick compacted clay cover over the incinerator ash;
- closure was approved by the November 27, 1989 regulatory deadline;
- an engineering report and temporary ash-storage as-built drawings G3 and G4 are listed;
- a later storage facility was constructed on the closed landfill;
- the later facility added an HDPE geomembrane, 18 inches of compacted native soil, and four inches of asphalt over the clay layer.

Current evidence state:

```text
actual_two_foot_clay_cover_documented = yes
survey_grade_thickness_measurement_verified = no
numerical_uncertainty_verified = no
```

Still missing:

- a mapped as-built boundary tied to the clay layer;
- numerical survey accuracy, construction tolerance, or a bounded uncertainty interval;
- an independently confirmed no-target comparison area;
- a clean Sentinel-1 period unaffected by later construction and operations.

**Decision:** retain, but heavy later construction makes it a weaker satellite-calibration case.

## 5. RAMCO / Recycled Aluminum Metals Co.

**Classification:** alternate as-built hold; not calibration-ready.

Official records establish:

- cleanup and removal occurred from 2007 through 2010;
- the excavation was filled and a final erosion-control cover was installed in September 2015;
- cap-project as-built drawings are listed;
- a no-further-action decision followed in 2016.

Still missing:

- actual measured cap thickness or elevations;
- numerical survey accuracy or accepted tolerance;
- an independently confirmed no-target comparison area;
- a demonstrated unchanged Sentinel-1 observation period.

**Decision:** retain as an alternate only.

## 6. Triune Mine

**Classification:** fallback hold; not calibration-ready.

Official records establish:

- cleanup was completed in 2018;
- tailings and waste rock were consolidated;
- the consolidated area was covered with a liner and clean soil and seeded;
- a completion/as-built report is listed.

Still missing:

- actual clean-soil thickness or depth-to-top measurements;
- numerical uncertainty;
- an independently confirmed no-target comparison area;
- a verified unchanged Sentinel-1 observation period.

**Decision:** fallback only.

## Current ranking

```text
1. Elk Plain — strongest measured as-built thickness map and timing support
2. Sudbury — strongest professionally surveyed and independently cross-checked constructed minimum
3. Go East — strongest recent completed-cover and record-drawing package
4. Recomp — documented installed depth but heavily confounded
5. RAMCO — alternate named as-built package
6. Triune — fallback
```

## Current readiness

None of the six sites currently provides the complete combination:

```text
actual measured depth or bounded thickness
+ numerical uncertainty
+ confirmed no-target comparison
+ clean observation timing
+ independent split eligibility
```

Therefore:

```text
calibration_records_created = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Do not restart generic searching.

The remaining retrieval order is:

1. Elk Plain Record of Survey `202502055001` and survey-control documentation;
2. Elk Plain evidence for a confirmed comparison footprint;
3. Sudbury certified as-built drawings and any project-specific survey tolerance;
4. Go East record drawings and construction summary;
5. Recomp G3/G4 drawings;
6. RAMCO cap as-built drawings;
7. Triune only if the stronger packages fail.

Stop each document path when it cannot supply actual measured values, numerical uncertainty, or independently supported comparison evidence.

The project owner does not need to contact anyone or search for records during this bounded public-document phase.
