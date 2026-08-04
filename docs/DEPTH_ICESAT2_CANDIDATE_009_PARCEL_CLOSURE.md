# ICESat-2 Candidate 009 — Parcel Context Closure

Status: closed as a direct placed-thickness/depth-anchor candidate.

## Candidate

```text
campaign      = southwest_us_earthwork_pilot_v3_imperial_valley
campaign rank = 9
latitude      = 32.76918983459473
longitude     = -115.41337509155274
median rise   = 0.8083953857421875 m
segments      = 5
spatial span  = approximately 200.6 m
event window  = 2021-05-23 through 2022-05-21
```

Candidate 009 passed the automated temporal-recovery, terminal-stability, and
context-priority screens. The Earth Engine land-cover audit was inconclusive and
therefore required parcel/footprint review before any records research.

## Parcel query result

The complete five-segment support line, queried with a 60 m distance against the
public Imperial parcel service, intersected three active parcels:

| APN | Assessor use code | Acres | Situs / legal context |
| --- | --- | ---: | --- |
| 055-500-006 | BGRC | 44.96 | 1396 E Hunt Ct, Holtville; large tract description |
| 055-490-013 | AGXC | 139.50 | portion of Tract 87; no situs address |
| 055-500-007 | AGXC | 101.17 | portion of Tract 77; no situs address |

Total intersected parcel area:

```text
44.96 + 139.50 + 101.17 = 285.63 acres
```

The exact internal Assessor code definitions are not relied upon as sole proof.
Imperial County cautions that its Assessor use codes are discretionary internal
codes and are not guaranteed for use by other organizations. The closure instead
rests on the combined evidence:

1. the ATL08 support line crosses three separate, very large parcels;
2. two parcels carry `AGXC` assessor codes;
3. the parcel legal descriptions are agricultural-scale tract descriptions;
4. the Earth Engine audit found mixed cultivated, crop, open-space, shrubland,
   and bare-ground context rather than a clear built-project footprint; and
5. no single named engineered project footprint covers all five supporting
   segments.

## Decision

```text
status                              = closed_after_parcel_context
context_review_recommended          = false
records_research_recommended        = false
candidate_is_depth_anchor           = false
candidate_is_placed_thickness       = false
```

Candidate 009 must not be used as:

- a measured placed-material thickness;
- a numerical-depth calibration row;
- proof of buried-object depth;
- proof that the 0.808 m apparent rise was engineered fill; or
- support for radar transfer outside the laser strip.

The parcel evidence does not prove that farming caused the rise. It proves that
the required one-project, one-footprint attribution is absent and that direct
placed-thickness records research is not justified.

## Campaign consequence

Candidate 009 was the only Imperial Valley candidate remaining in the automated
context-review queue. Closing Candidate 009 leaves:

```text
usable depth anchors                 = 0
context-review candidates remaining  = 0
records-research candidates          = 0
numerical depth ready                = no
```

Use `scripts/apply_icesat2_candidate_manual_dispositions.py` with a local
`candidate_manual_dispositions.json` file to produce the authoritative
`campaign_decision_summary.json` without changing the immutable automated scan
or finalizer summaries.

## Protection boundary

This closure does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output; or
- `main`.
