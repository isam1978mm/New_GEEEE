# ICESat-2 Campaign 006 — Earth Engine Context Results

Status: Earth Engine context audits completed for Campaign 006 candidates 001–004. Numerical depth remains blocked.

## Finalized survivor set

Campaign 006 produced four context-review survivors after spatial, temporal-recovery, terminal-stability, magnitude, segment-count, and event-window gates:

| Rank | Median rise (m) | Segments | Event window | Earth Engine context |
|---|---:|---:|---|---|
| 001 | 0.688367 | 5 | 2022-11-15 to 2023-08-14 | water-dominated; audit status `context_inconclusive` |
| 002 | 2.774352 | 5 | 2020-03-20 to 2020-12-17 | wooded/shrub context; audit status `context_inconclusive` |
| 003 | 1.671758 | 4 | 2022-03-16 to 2023-06-13 | grass/shrub context; audit status `context_inconclusive` |
| 004 | 1.400732 | 4 | 2022-03-16 to 2023-06-13 | grass/shrub context; audit status `context_inconclusive` |

Candidate 005 remains deferred for insufficient spatial support and does not proceed.

## Candidate 001

Dynamic World mean water probability remained approximately 0.70 in the pre-event, event, and post-event windows. Built, bare, and crop probabilities were all low, and CDL classified the footprint as almost entirely non-cultivated.

Decision:

- do not treat the 0.688 m rise as placed fill;
- deprioritize Candidate 001 for direct-thickness calibration;
- retain only as a water-dominated terrain-change candidate until manual imagery confirms the exact surface.

## Candidate 002

Dynamic World was dominated by trees and shrub/scrub rather than built or bare ground. CDL showed a mixed buffer but stayed below the cultivated-context threshold.

Decision:

- keep Candidate 002 as a secondary manual-review candidate;
- do not start records research;
- exact imagery and parcel/project-footprint matching are still required.

## Candidates 003 and 004

Both candidates are non-cultivated and dominated by grass/shrub context. Built and bare probabilities are low. Their rises remain stable through later ICESat-2 epochs.

Decision:

- Candidate 003 is manual-review priority 1;
- Candidate 004 is manual-review priority 2;
- exact phosphate-mine, reclamation-unit, parcel, and historical-imagery overlap must be tested before records research;
- neither candidate is a depth anchor yet.

## Required next gate

For Candidates 003 and 004 first, then Candidate 002:

1. identify the exact ATL08 support line on historical imagery;
2. test overlap with official Florida DEP phosphate mine and reclamation boundaries;
3. identify the named mine, reclamation unit, clay-settling area, wetland restoration, road, berm, or other project footprint;
4. verify that activity occurred inside the measured event window;
5. locate an as-built or certified placed-material thickness covering the full ATL08 support line;
6. keep `records_research_ready = false` until all footprint and cause gates pass.

## Protection boundary

This result does not modify classifier behavior, frontend pages, Option 5, production numerical-depth output, or `main`. It does not authorize new emails or public-record requests.

## Current decision

```text
candidate_001_manual_priority = low_water_context
candidate_002_manual_priority = secondary
candidate_003_manual_priority = 1
candidate_004_manual_priority = 2
records_research_ready        = false
candidate_is_depth_anchor      = false
numerical_depth_unlocked       = false
```
