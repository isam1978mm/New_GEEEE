# Tyrone depth — F154 GLAS closure — 2026-08-20

## Purpose

Record the decisive F153 spatial-screen result for the ICESat-1 / GLAS Laser-3A branch and prevent this route from being reopened without genuinely new evidence.

## Context

The direct-elevation numerical-depth plan remains blocked at **Step 4 repair**: recover or build a trustworthy immediate post-grading / pre-cover 3X surface.

The ICESat-1 / GLAS branch was screened because Laser-3A operated during the useful construction window (approximately 3 Oct–8 Nov 2004), and GLAH14 V034 is an independent elevation product.

The screen used the real project-derived 3X WGS84 footprint rather than an approximate Tyrone point.

## Exact CMR query executed

The user executed this NASA CMR granule query from PowerShell:

```powershell
$uri = "https://cmr.earthdata.nasa.gov/search/granules.json?" +
"page_size=2000" +
"&short_name=GLAH14" +
"&version=034" +
"&provider=NSIDC_CPRD" +
"&bounding_box=-108.42141,32.71940,-108.41672,32.72338" +
"&temporal=2004-10-03T00:00:00Z,2004-11-08T23:59:59Z"

$r = Invoke-RestMethod -Uri $uri

Write-Host "=== GLAH14 GRANULES INTERSECTING 3X ==="
Write-Host "COUNT:" @($r.feed.entry).Count
```

## Result

The returned result was:

```text
=== GLAH14 GRANULES INTERSECTING 3X ===
COUNT: 0
```

No granule entries were returned.

## Decision

**ICESat-1 / GLAS Laser-3A is CLOSED as a candidate for the missing 2004 pre-cover 3X surface.**

Reason: NASA CMR returned zero GLAH14 V034 granules intersecting the real 3X bounding box during the Laser-3A campaign window.

Per the previously frozen decision rule, this branch closes immediately. Do not interpolate from distant GLAS tracks and do not proceed to shot-level F154/F155 screening because there is no intersecting granule to inspect.

## Scientific status after closure

- Original unknown-zone direct-elevation plan: **BLOCKED at Step 4 repair**.
- Step 5 alignment: **NOT REACHED**.
- Step 6 subtraction: **NOT REACHED**.
- Step 7 TP5/TP6/TP7 validation: **NOT REACHED for the elevation method**.
- Step 8 TP1/TP2/TP3 + 43-pit validation: **NOT REACHED**.
- 1996 free NAPP reconstruction: **CLOSED**.
- 2005 statewide DTM: **CLOSED as pre-cover source**.
- ICESat-1 / GLAS Laser-3A: **CLOSED by F153 spatial screen (`COUNT: 0`)**.
- Route A recorded known-depth lookup: **separate; do not switch unless explicitly requested**.
- classifier/UI/NB formula: **unchanged**.

## Guard against reopening

Do not repeat the GLAS Laser-3A branch unless genuinely new evidence appears showing that the CMR spatial query was wrong, the 3X geometry was wrong, or a different independent GLAS product contains actual shots over 3X despite the zero-granule CMR result.

Do not use known Tyrone measured depth values to rescue, fit, vertically shift, select, or tune any future Step-4 candidate.

## Exact next action

Continue **Step 4 repair** with the next genuinely independent candidate source that could represent the immediate post-grading / pre-cover 3X surface.

Do not repeat F34–F153. Do not restart the closed BER/CQAR/CAES/GPS/public-archive, 1996 NAPP, 2005 DTM, or GLAS branches from scratch.
