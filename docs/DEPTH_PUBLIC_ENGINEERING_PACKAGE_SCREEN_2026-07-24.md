# Public Engineering Package Screen for Numerical Depth — 2026-07-24

**Branch:** `main`  
**Status:** bounded official-record review complete  
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

### 1. Sudbury Road Landfill

**Current classification:** strongest engineering hold; not calibration-ready.

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

**Decision:** keep as the first document-retrieval target. Do not enter a calibration record yet.

### 2. Elk Plain County Shop

**Current classification:** strongest actual-thickness-map hold; not calibration-ready.

Official records establish:

- contaminated soil was consolidated in August 2023;
- the site was capped with six feet of compacted clean soil;
- an official post-cap survey map contains many measured cover-thickness values;
- the mapped values span approximately 6.00 to 11.08 feet;
- the submitted cap survey figure was accepted as addressing Ecology's request;
- long-term cap inspection is required.

Still missing:

- a numerical survey accuracy or control bound;
- an independently confirmed no-target comparison area;
- a clear unchanged-condition window that can be matched safely to Sentinel-1 observations;
- resolution of later grading, settlement, and other surface-change confounders.

**Decision:** retain as the best public actual-thickness example, but do not use it as numerical truth until uncertainty and comparison evidence are found.

### 3. Recomp of Washington

**Current classification:** promising alternate hold; not calibration-ready.

Official records establish:

- the ash landfill was closed with a stated two-foot compacted clay cover;
- closure was approved in 1989;
- a temporary ash storage facility was later constructed on top;
- official as-built drawings and an engineering report are listed in the cleanup record.

Still missing:

- proof that the two-foot value is an actual measured as-built thickness rather than a design or closure specification;
- numerical survey accuracy or construction tolerance suitable as depth uncertainty;
- an independently confirmed no-target comparison area;
- a clean Sentinel-1 observation period unaffected by later construction.

**Decision:** retain as an alternate physical-site lead. The later construction is a major timing and confounding risk.

### 4. RAMCO / Recycled Aluminum Metals Co.

**Current classification:** promising alternate hold; not calibration-ready.

Official records establish:

- cleanup and removal work occurred from 2007 through 2010;
- the excavation was filled and a final cover was installed in September 2015;
- official cap-project as-built drawings are listed;
- a no-further-action decision followed in 2016.

Still missing:

- actual measured cap-thickness or elevation values from the as-built drawings;
- numerical survey accuracy or accepted tolerance;
- an independently confirmed no-target comparison area;
- a demonstrated unchanged observation period for Sentinel-1 matching.

**Decision:** retain as an alternate physical-site lead and inspect only the named as-built package.

### 5. Triune Mine

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

**Decision:** keep only as a fallback. It is currently weaker than Sudbury, Elk Plain, Recomp, and RAMCO.

## Current ranking

```text
1. Sudbury Road Landfill — strongest complete engineering-process lead
2. Elk Plain County Shop — strongest actual measured thickness-map lead
3. RAMCO — promising named cap as-built package
4. Recomp of Washington — promising but later construction creates risk
5. Triune Mine — fallback only
```

## What this screen did not prove

None of the five sites currently provides all of the following in the successfully reviewed public material:

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

1. Sudbury final construction quality-assurance certification report and its as-built drawings;
2. RAMCO cap-project as-built drawings;
3. Recomp temporary ash-storage as-built drawings and engineering report;
4. Triune completion/as-built report only if the stronger three fail;
5. Elk Plain survey-control or accuracy documentation.

For each document, stop immediately if it does not supply actual measured values, numerical uncertainty, or usable comparison evidence.

The project owner does not need to contact anyone or search for records during this bounded public-document phase.
