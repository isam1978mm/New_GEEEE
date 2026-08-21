# F175 — John Sevier Bottom Ash Pond elevation-only re-score

Date: 2026-08-21

## Decision

**PRE-SURFACE PASS / AS-BUILT SUBGRADE SURVEY EXISTENCE PROVEN / NUMERICAL POST-SURFACE ACCESS BLOCKED.**

John Sevier remains scientifically promising, but it is not directly executable from the public numerical data recovered in this step.

## What is proven

1. TVA has a site-specific pre-work aerial/LiDAR/topographic surface from November 2014, before the 2016 closure excavation/regrading work.
2. TVA's December 2017 closure plan states that the maximum CCR inventory estimate (~660,000 CY) was based on comparison of:
   - a native surface established from geotechnical boring data, and
   - a subgrade surface established by the unit's as-built survey.
   This proves that a quantitative as-built subgrade surface existed and was used.
3. TVA's 2018 History of Construction states that Appendix D contains:
   - record drawings from the Bottom Ash Pond Pre-Closure Project, and
   - record drawings from the Bottom Ash Pond Final Closure Project.
4. The History references exact construction reports including the Bottom Ash Pond Pre-Closure Construction Certification Report and the Bottom Ash Pond Final Closure Construction Certification Report.
5. TVA's 2017 annual inspection says an updated volume study used TVA Drawing `10W522-04` dated 2016-11-04 and a Phillips & Jordan Survey of Stacking Area dated 2016-09-23.

## What is NOT recovered

- The numerical as-built subgrade surface itself.
- The Pre-Closure/Final Closure record drawings in a directly extractable numerical form.
- TVA Drawing `10W522-04` as a standalone public artifact.
- A public DEM/TIN/XYZ/LandXML/DWG/DXF representing the post-excavation subgrade.

The ~98 MB History of Construction PDF times out when direct retrieval is attempted. Public search indexing proves the record drawings exist but does not expose their geometry safely enough to reconstruct a surface.

## Important rejection of apparent depth truth

TVA annual inspections publish an approximate CCR depth range of 0–38 ft and approximate CCR volume of 421,085 CY.

These values are **not accepted as measured validation truth** because TVA explicitly states that the ash depth is based on available aerial-survey information and **estimated bottom-of-ash contours**.

Therefore:
- do not use 0–38 ft as measured depth anchors;
- do not tune or validate the depth method against those estimated values.

## Why simple before/final subtraction is unsafe

Closure construction did not consist of a clean removal-only excavation. TVA records show CCR and some underlying soil were excavated and relocated, the original west dike was regraded, and soil/material was reused for berm construction, cover, and grading fill.

Therefore a simple 2014-prework minus final-2017 surface can mix:
- CCR excavation,
- native-soil excavation,
- relocated CCR,
- berm construction,
- cover/fill placement,
- final grading.

The actual as-built subgrade surface is required to isolate the relevant geometry.

## Do not repeat

Do not repeat generic searches for:
- John Sevier as-built survey;
- `10W522-04`;
- the Phillips & Jordan 2016-09-23 stacking survey;
- the 98 MB History of Construction Appendix D;
- the published 0–38 ft inspection estimate as if it were measured truth.

## Current status

John Sevier is **HIGH-PRIORITY OPEN but access-blocked**.

A later recovery of the Pre-Closure/Final Closure record drawings or the numerical as-built subgrade surface could make this route executable.

Until then, proceed to another exact elevation-only candidate rather than spending more public-search time on the same missing record.
