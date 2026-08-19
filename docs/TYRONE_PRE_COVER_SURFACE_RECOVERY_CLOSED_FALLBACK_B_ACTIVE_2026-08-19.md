# Tyrone Pre-Cover Surface Recovery Closed; Stereo Aerial Fallback Active — 2026-08-19

## Decision

The easy/best elevation-difference route that depended on recovering an original Tyrone 3X pre-cover/subgrade electronic survey surface from EMNRD is now **CLOSED as a records-recovery path**.

Numerical depth remains **BLOCKED**. No classifier, UI, or NB formula changes are authorized or made by this decision.

The active fallback is now:

> **Pre-reclamation stereo aerial reconstruction → historical 3D surface → align with modern Tyrone LiDAR → test `after elevation - before elevation` against measured Tyrone depth.**

No numerical depth should be calculated until the historical stereo imagery and vertical-accuracy gate pass.

## EMNRD evidence

A narrow follow-up IPRA request was submitted on 2026-08-19:

- request: `N000031-081926`
- target: original electronic pre-cover/subgrade and final/post-cover survey/design deliverables for Tailing Impoundment 3X
- requested native formats included CAES, GPS, CAD, GIS, TIN, LandXML, point/coordinate tables, surface files, DWG/DXF, shapefiles/geodatabases, plus survey-control and datum/accuracy metadata
- the request explicitly referenced the June 2004 3X Basic Engineering Report and the 2008 CQAR and asked for underlying electronic surfaces rather than duplicate PDFs

EMNRD/MMD replied on 2026-08-19:

> All documents pertaining to this request have been uploaded in request No. N000019-072826. No additional documents exist pertaining to this request.

The earlier request `N000019-072826` had already been used to recover the available Tyrone 3X package. MMD stated on 2026-08-05 that 95 attachments were associated with that request, and on 2026-08-07 confirmed that no additional records existed beyond what had already been provided.

Therefore the project must not keep treating another EMNRD search for the same 3X native electronic surfaces as the active numerical-depth path unless genuinely new evidence identifies a different custodian/archive.

## What remains historically documented

Separate official Tyrone records still establish that suitable historical topographic data once existed:

- `M3, 2004d`: **Basic Engineering Report, Tailing Impoundment #3X Reclamation, Volume 1 BER Summary Report**, prepared for Phelps Dodge Tyrone, Inc., June 2004, before 3X reclamation began.
- Tyrone Supplemental Materials Characterization records state that PDTI Engineering supplied mine-wide topographic data in AutoCAD files for 1995–2004, with annual surveys from 1995 and aerial surveys from 2000–2004.
- Those vector elevation features were used to create TIN surfaces and 25 ft × 25 ft raster elevation grids for topographic/volumetric analysis.

This proves the historical data family existed, but **the project does not possess the needed native pre-cover surface**, and EMNRD has now stated that it has no additional records beyond the already-produced package.

## Fallback B status: pre-2004 stereo aerial reconstruction

### Coverage / program feasibility

The next active route is the pre-reclamation aerial-photogrammetry fallback.

Current metadata findings:

- Grant County, New Mexico has 1996 NAPP2 coverage in the USDA historical aerial imagery catalog.
- USGS documents NAPP photography as vertical mapping photography, nominally 1:40,000, acquired on 9-inch film with a 6-inch focal-length lens.
- Flight lines were flown north-south through east/west halves of 7.5-minute quadrangles.
- Adjacent images have about 60% overlap specifically to support stereoscopic viewing.
- Existing NAPP high-resolution 25-micron scans are free where already available.
- On-demand black-and-white film scans are available at 7 microns for $30 per frame plus the applicable handling fee.

The validated Tyrone 3X reference places the six plots around approximately 32.720–32.723 N, -108.421 to -108.417 W.

The standardized NAPP target position derived for that footprint is:

- target station: `1084E-0280`
- likely adjacent stereo neighbors: `1084E-0279` and `1084E-0281`

These exact accepted 1996 frame/roll/entity identifiers still require archive confirmation.

## Current access blocker

USGS publishes NAPP coverage maps publicly, but the detailed scene inventory used to confirm entity ID, roll, frame, acquisition date, camera metadata, and scan availability is exposed through EarthExplorer/EROS inventory access.

A Gmail draft has been prepared for USGS EROS User Services (`custserv@usgs.gov`) requesting confirmation of the actual 1996 NAPP stereo scenes covering:

- WGS84 point: `32.7215, -108.4193`
- expected target: `1084E-0280`
- expected neighbors: `1084E-0279`, `1084E-0281`

The draft requests acquisition date, entity/project identifiers, roll/frame numbers, camera/focal-length metadata, stereo-overlap confirmation, existing scan resolution, and photogrammetric-quality scan options.

The draft has **not been sent automatically** and should remain unsent until the user explicitly approves sending it.

## Scientific gate before any depth calculation

Obtaining the frames is not enough to validate numerical depth.

Before computing `after - before`, the project must preregister and test whether a 1996 stereo-derived surface can achieve sufficient vertical accuracy for Tyrone cover depths of roughly 0.7–1.3 m.

At minimum the test must include:

1. original overlapping frames and camera calibration;
2. defensible ground control / bundle adjustment;
3. reconstruction of a pre-reclamation surface over the six Tyrone plots;
4. alignment to the modern final-surface LiDAR in a common horizontal and vertical datum;
5. independent vertical-residual checks on stable terrain/control areas;
6. a frozen vertical-error threshold set before comparing reconstructed depth with the measured Tyrone plot depths;
7. only then calculate `final surface elevation - reconstructed historical surface elevation`.

If vertical uncertainty is too large relative to the 0.7–1.3 m target signal, this fallback fails and the project proceeds to the next physically distinct route rather than tuning the result.

## Current route status

| Route | Status | Reason |
|---|---|---|
| Original 3X pre-cover CAES/GPS/electronic survey from EMNRD | **CLOSED / unavailable** | EMNRD states no additional records exist beyond the already-produced package |
| Q1-2004 / 2004 PDTI AutoCAD/TIN/grid recovery from EMNRD | **CLOSED as current EMNRD recovery path** | Historical existence documented, but no additional native file is available from EMNRD |
| 1996 NAPP stereo aerial reconstruction | **ACTIVE** | Pre-reclamation coverage and stereo-capable acquisition are documented; exact frames still need archive confirmation |
| GPR / active local sensing | **HELD** | Physically direct but usually per-AOI field work and not the preferred automatic/free path |
| More independent measured-depth sites / empirical model | **HELD** | Only after the physically direct elevation route is exhausted; requires strict site-level holdout |
| Numerical depth in app | **BLOCKED** | No replacement route has passed validation |

## Exact next action

1. Obtain/confirm the exact 1996 NAPP frames over Tyrone 3X (`1084E-0279/0280/0281` or corrected archive identifiers).
2. Determine scan availability and camera calibration.
3. Preregister the stereo-reconstruction vertical-accuracy gate.
4. Only after that gate passes, reconstruct the pre-reclamation surface and test `after - before` against Tyrone measured depths.

Do not return to random Sentinel/NISAR/NB feature hunting.