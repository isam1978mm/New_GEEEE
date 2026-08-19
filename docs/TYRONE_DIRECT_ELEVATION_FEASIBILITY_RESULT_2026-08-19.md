# Tyrone 3X Direct-Elevation Feasibility Result — 2026-08-19

## Result

**CONDITIONAL ROUTE REMAINS OPEN, BUT DEPTH CANNOT BE COMPUTED YET.**

The direct-elevation replacement strategy is physically different from the failed surface-signature routes:

`depth ~= final/current surface elevation - pre-cover/buried-interface elevation`

The review found a credible free modern elevation surface, but did not recover the required pre-cover/buried-interface surface.

## 1. Modern/current surface — found

USGS The National Map reports lidar and a 1 m DEM over Tailing Impoundment 3X from project `NM_SouthCentral_2018_D19`, work unit `NM_SouthCentral_B8_2018`.

Project quality documentation supports QL2 lidar and reports approximately:

- non-vegetated vertical accuracy at 95% confidence: **0.066 m**;
- vegetated vertical accuracy at the 95th percentile: **0.169 m**;
- horizontal reference: **NAD83(2011), UTM Zone 12N**;
- vertical reference: **NAVD88, GEOID12B**.

This is a credible **backup current/final surface**.

It is not automatically the ideal as-built surface because the lidar was acquired roughly thirteen years after 3X reclamation was completed in 2005. Settlement, erosion, drainage repair, or other surface evolution could therefore be included in a 2005-to-2018 difference.

## 2. Original 3X engineering surfaces — known to have existed, not recovered

The official 3X CQA/as-built report states that:

- subgrade grading used CAES complemented by conventional GPS surveys;
- final cover grade was confirmed using CAES and post-cover GPS surveys.

Therefore the original construction workflow had exactly the type of pre/final geometry needed for a direct elevation difference.

However, the actual CAES/GPS/CAD/TIN survey surfaces are not present in the public PDF package recovered by the project.

The historical `agent/tyrone-electronic-files-recovery-20260729` route already inspected the public Attachment I record for:

- PDF annotations and linked URIs;
- embedded attachments;
- filename references;
- same-domain downloadable files;
- DWG, DXF, ZIP/7Z/RAR, KML/KMZ, shapefile components, CSV/XLS/XLSX and related formats.

That recovery did **not** find actual electronic survey deliverables. The public electronic-file attachment behaved as a placeholder, not the data itself.

## 3. Public pre-construction alternatives

### 2004 engineering/design records

Official Tyrone records reference:

- M3, June 2004, `Basic Engineering Report, Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report`;
- Tetra Tech, June 2004, `Cover design report: 3X tailings impoundment`.

The searches confirmed these references but did not recover a usable electronic pre-cover/subgrade elevation surface.

### 2005 aerial imagery

Grant County 1 m orthophoto coverage exists for 2005, but 3X reclamation began in September 2004 and continued through 2005. A 2005 orthophoto is therefore not automatically a pre-cover image and, as an orthophoto, is not by itself an independent buried-surface DEM.

### Historical stereo aerial photography

Pre-September-2004 overlapping aerial frames remain a possible fallback for photogrammetric reconstruction. The metadata-only USGS M2M probe required separate authentication, and no imagery was downloaded or evaluated in this review.

This fallback should only be pursued if the original construction survey surfaces cannot be obtained.

## 4. Scientific decision

Do **not** calculate a Tyrone depth raster yet.

The missing item is specifically:

**a trustworthy pre-cover/subgrade/buried-interface elevation surface.**

Do not reconstruct that surface from the known TP1/2/3/5/6/7 or test-pit depths and then use those same values as independent validation.

Do not use the coarse CQAR post-construction contours as if they were a sub-meter pre-cover survey.

Do not choose a vertical-accuracy threshold after viewing derived depth errors.

## 5. Exact next action

Submit a narrow follow-up records request for the original electronic survey deliverables associated with Tailing Impoundment 3X, specifically:

> Please provide the original electronic CAES/GPS/CAD/GIS/TIN or survey-coordinate deliverables for Tailing Impoundment 3X reclamation, including the pre-cover/subgrade grading surface and final/post-cover as-built surface. Please include horizontal and vertical datum information, survey control/benchmarks, coordinate units, and any stated horizontal/vertical survey accuracy. Records may be associated with the June 2004 M3 Basic Engineering Report, the June 2004 Tetra Tech Cover Design Report, and the June/August 2008 Construction Quality Assurance/as-built report.

This is a targeted follow-up for electronic survey surfaces, not a new broad depth-record search.

If the agency confirms those files are unavailable, the next fallback is a separately preregistered historical stereo-aerial feasibility study.

## Production status

- NB numerical-depth route: **CLOSED / FAILED**.
- Generic surface-signature feature expansion: **CLOSED**.
- Direct-elevation route: **CONDITIONAL / WAITING FOR PRE-COVER SURFACE**.
- Numerical app depth: **BLOCKED**.
- Classifier, UI, NB formula, SAR constraints and production runtime: **UNCHANGED**.
