# Public Engineering Package Screen for Numerical Depth — 2026-07-24

**Branch:** `main`  
**Status:** bounded named-document review ongoing  
**Broad generic search:** stopped  
**Calibration-ready public packages:** 0

## Plain-English purpose

This screen checked a small set of official engineering and remediation records for evidence that could become real numerical-depth calibration data.

A site is not ready merely because a design specifies a cover thickness. To count, the public record must provide:

1. an exact mapped physical area;
2. actual measured depth or installed thickness to the top of the reference material;
3. numerical survey accuracy, uncertainty, or a bounded accepted tolerance;
4. construction, completion, and observation dates;
5. an independently confirmed no-target comparison area;
6. enough separation from other sites to preserve train, validation, and holdout groups.

## Screened official packages

### 1. Elk Plain County Shop

**Current classification:** strongest near-complete public evidence hold; not calibration-ready.

Official records now establish:

- contaminated soil was consolidated and capped in August 2023;
- the cap consists of six feet of compacted clean soil over an orange warning layer;
- an official as-built comparison map contains survey data for the top of the contaminated soil and the top of the clean-soil cap;
- the map contains many measured cover-thickness values spanning approximately 6.00 to 11.08 feet;
- Ecology explicitly accepted the submitted cap survey figure as addressing its request;
- the capped area is a separately identified approximately 5.31-acre parcel;
- a later official progress report states that no additional site-characterization work was performed or planned and no anticipated site changes were reported through December 2025;
- a Pierce County Record of Survey was recorded under number `202502055001` for the capped parcel;
- the cap is subject to an environmental covenant, annual inspection, and long-term maintenance;
- the official site index now records a No Further Action status and a recorded environmental covenant in 2026.

This resolves most of the earlier timing concern:

```text
actual_as_built_thickness_values = yes
mapped_capped_parcel = yes
regulator_acceptance = yes
post_cap_no_reported_change_window_through_2025_12 = yes
numerical_survey_accuracy = no
confirmed_no_target_comparison = no
```

Still missing:

- a numerical vertical survey accuracy, control bound, closure tolerance, or source-supported uncertainty interval;
- an independently confirmed no-target comparison area of adequate size and similar surface setting;
- final Sentinel-1 date selection that avoids construction, grading, vegetation-establishment, and other surface-change periods.

The as-built map is labelled `REVIEW SET`; Ecology accepted it as the requested cap-thickness map, but neither that acceptance nor the displayed hundredths of a foot supplies a defensible numerical measurement uncertainty.

**Decision:** promote Elk Plain to the first public document-retrieval target. It is closest to a usable positive depth record, but no calibration row may be created until the uncertainty and confirmed-comparison requirements are satisfied.

### 2. Sudbury Road Landfill

**Current classification:** strongest engineering-process hold; not calibration-ready.

Official records establish:

- cleanup construction completed in 2017;
- improved cover was installed over Areas 2 and 5;
- the construction quality-assurance manual required subgrade elevations approximately five feet below finished grade;
- the installed cover had to meet a minimum thickness of 4.8 feet;
- grade control and thickness verification were required;
- a final as-built survey was required;
- the official construction quality-assurance certification report states that as-built drawings are included.

Still missing from the material successfully extracted:

- the actual surveyed per-area thickness or elevation values from the final as-built package;
- a numerical survey accuracy or vertical control statement;
- an independently confirmed no-target comparison area.

**Decision:** keep as the second document-retrieval target. Do not enter a calibration record yet.

### 3. Go East Corp Landfill

**Current classification:** strong recent record-drawing hold; not calibration-ready.

Official records establish:

- the landfill was consolidated, regraded, and closed between March 2021 and July 2022;
- closure was completed under current limited-purpose-landfill requirements;
- a construction quality-assurance report is publicly listed;
- a separate construction summary report is publicly listed;
- separate as-built/record drawings are publicly listed as Appendix O;
- the official record states that a July 2022 drone flight documented construction of the final cover;
- post-closure monitoring and an environmental covenant are in place.

Still missing from the material successfully extracted:

- actual surveyed cover-thickness or top-and-bottom elevation values from the record drawings;
- numerical survey accuracy, vertical control, or accepted construction tolerance;
- an independently confirmed no-target comparison area;
- a clean Sentinel-1 observation window not confused by the surrounding residential development and other post-closure work.

**Decision:** retain as a high-priority document-retrieval target. The named record drawings and construction summary make it promising, but no calibration record may be created yet.

### 4. Recomp of Washington

**Current classification:** documented installed-depth hold; not calibration-ready.

Official records now establish more strongly than the earlier screen:

- the ash landfill **was closed by placing a two-foot-thick compacted clay cover** over the incinerator ash;
- Whatcom County Health Department approved the landfill closure by the November 27, 1989 regulatory deadline;
- the official cleanup record lists an engineering report for landfill closure and temporary ash-storage construction;
- the official cleanup record also lists temporary ash-storage as-built drawings G3 and G4;
- a temporary ash-storage facility was later constructed on top of the closed landfill;
- the later storage facility included an 80-mil HDPE geomembrane over the two-foot clay layer, then 18 inches of compacted native soil and four inches of asphalt.

This changes the earlier interpretation:

```text
actual_two_foot_clay_cover_documented = yes
survey_grade_thickness_measurement_verified = no
numerical_uncertainty_verified = no
```

Still missing:

- a mapped as-built boundary that can be tied safely to the two-foot clay layer;
- numerical survey accuracy, vertical control, construction tolerance, or a bounded accepted interval;
- an independently confirmed no-target comparison area;
- a clean Sentinel-1 observation period unaffected by the later storage facility, paving, grading, and continuing site operations.

The 1989 engineering-report PDF was reachable, but it is image-based and did not expose searchable measurement text in this review. The G3/G4 as-built drawing file remained unavailable through the document server.

**Decision:** retain as a documented installed-depth hold. It still cannot enter the calibration pack because uncertainty, clean timing, and confirmed comparison evidence are missing.

### 5. RAMCO / Recycled Aluminum Metals Co.

**Current classification:** promising alternate hold; not calibration-ready.

Official records establish:

- cleanup and removal work occurred from 2007 through 2010;
- the excavation was filled and a final erosion-control cover was installed in September 2015;
- official cap-project as-built drawings are listed;
- a no-further-action decision followed in 2016.

Still missing:

- actual measured cap-thickness or elevation values from the as-built drawings;
- numerical survey accuracy or accepted tolerance;
- an independently confirmed no-target comparison area;
- a demonstrated unchanged observation period for Sentinel-1 matching.

**Decision:** retain as an alternate physical-site lead and inspect only the named as-built package.

### 6. Triune Mine

**Current classification:** weaker hold; not calibration-ready.

Official records establish:

- cleanup was completed in 2018;
- approximately 5,500 cubic yards of tailings and waste rock were consolidated;
- the consolidated area was covered with a liner and clean soil and then seeded;
- an official completion/as-built report is listed.

Still missing:

- actual clean-soil thickness or depth-to-top measurements;
- numerical survey accuracy or uncertainty;
- an independently confirmed no-target comparison area;
- a verified unchanged Sentinel-1 observation period.

**Decision:** keep only as a fallback. It is currently weaker than the other five packages.

## Current ranking

```text
1. Elk Plain County Shop — strongest measured as-built thickness evidence and improved timing support
2. Sudbury Road Landfill — strongest complete engineering-process lead
3. Go East Corp Landfill — strongest recent record-drawing package
4. Recomp of Washington — strongest installed-depth statement, but heavily confounded
5. RAMCO — promising named cap as-built package
6. Triune Mine — fallback only
```

## What this screen did not prove

None of the six sites currently provides all of the following in the successfully reviewed public material:

```text
actual measured depth or thickness
+ numerical uncertainty
+ confirmed no-target comparison
+ clean observation timing
+ independent site split eligibility
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

The next work is limited to retrieving and reading these named official documents:

1. Elk Plain Pierce County Record of Survey `202502055001` and any survey-control or vertical-accuracy documentation tied to the cap survey;
2. Elk Plain site records that can independently establish a suitable no-target comparison footprint;
3. Sudbury final construction quality-assurance certification report and its as-built drawings;
4. Go East record drawings, construction summary, and construction quality-assurance report;
5. Recomp temporary ash-storage as-built drawings G3 and G4, specifically for mapped elevations, survey notes, and layer boundaries;
6. RAMCO cap-project as-built drawings;
7. Triune completion/as-built report only if the stronger packages fail.

For each document, stop immediately if it does not supply actual measured values, numerical uncertainty, or usable comparison evidence.

The project owner does not need to contact anyone or search for records during this bounded public-document phase.
