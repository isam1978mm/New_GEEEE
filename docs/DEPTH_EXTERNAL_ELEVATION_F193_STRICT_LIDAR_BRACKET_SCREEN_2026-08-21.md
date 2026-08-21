# F193 — strict lidar bracket screen

Date: 2026-08-21

## Purpose

Apply the breadth-first lidar metadata gate to every F192 survivor, with the corrected timing rule added before any elevation values are opened.

A candidate passes F193 only if all three conditions are proven:

1. pre-lidar was acquired **after final waste placement / final waste grade**;
2. pre-lidar was acquired **before target final-cover placement**;
3. post-lidar was acquired **after closure completion** and covers the same target footprint.

The post-closure time gap must also be recorded because settlement can reduce the apparent cover thickness.

## Ground-truth status frozen before testing

Published cap values in this route are **nominal / regulatory cover thicknesses**, not measured mean thicknesses.

If a candidate reaches execution, the comparison can only test whether elevation differencing recovers approximately the specified cover thickness. It must not be reported as agreement with a measured mean unless an independent as-built thickness data set is recovered.

## Fingerprint limit

Maximum three bounded source fingerprints per site. If timing or coverage remains unresolved after that, the site is dropped rather than researched indefinitely.

## Results

| Candidate | Nominal target | Final waste placement -> pre-lidar proven? | Pre-lidar before cover? | Post-lidar after closure + same coverage? | F193 decision |
|---|---:|---|---|---|---|
| CWM Arlington L-12, OR | 3 ft nominal | NO clean pre-cover epoch recovered | NO: the strong 2018 Morrow/Gilliam-area lidar was acquired 2018-10-03 through 2018-11-15, after L-12 final closure in March 2018 | not reached | **DROP** |
| CWM Arlington L-13, OR | nominal multi-foot cover | NOT PROVEN for the 2018 lidar epoch | 2018 lidar is before Dec-2020 closure, but public evidence does not prove L-13 had reached final waste grade before Oct-Nov 2018; cover design was still being modified in 2020 | no later same-footprint public lidar pair was proven within budget | **DROP** |
| Masonville Cove, MD | 2 ft nominal soil cap | NOT PROVEN; public source only says restoration construction completed in 2019 | NOT PROVEN | 2020 Anne Arundel lidar was acquired 2020-12-08 through 2020-12-11, but its published northern bound is 39.2381837 N; the referenced Masonville Cove location is just north of that coverage | **DROP** |
| Tangerine Landfill, AZ | 3 ft nominal soil cover | YES: waste acceptance ended in 2013; 2015 PAG lidar was acquired in March 2015 | YES on timing: final closure/cap was completed in Dec 2016 | NOT PROVEN: a 2021 PAG QL1 acquisition exists, but within the third fingerprint the exact 2021 elevation footprint could not be proven to re-cover the Tangerine landfill | **DROP** |
| Yolo County Central Landfill WMU 4/5, CA — reserve | multi-foot final-cover system; exact placed surface is survey-controlled | NOT PROVEN for any available public lidar tile | NOT PROVEN: 2017 Delta lidar is too early; a 2018-2019 Northern California acquisition includes Yolo County, but the landfill tile acquisition date could not be proven to fall after final waste grade and before cap placement | not reached | **DROP** |

## Important source details

### CWM Arlington L-12 / L-13

The EPA permit record gives final closure dates of March 2018 for L-12 and December 2020 for L-13. The 2018 Oregon lidar metadata gives an acquisition window of 2018-10-03 to 2018-11-15. The lidar DEM was tested at 0.081 m NVA at 95% confidence; the metadata describes the required relationship as RMSEz x 1.96, so this corresponds to roughly 0.041 m RMSEz for that tested DEM. Timing, not accuracy, is the failure here.

For L-12, the 2018 surface is already post-cover. For L-13, the 2018 surface is potentially pre-cover but the newly required condition cannot be established: no bounded source proved final waste placement was complete before that flight.

### Masonville Cove

Maryland documentation states that a two-foot soil cap was required over much of the restoration site and that restoration construction was completed in 2019. That wording is insufficient to establish a final-waste-grade date or a narrow cap-placement window.

The closest strong post candidate recovered was 2020 Anne Arundel County lidar, acquired 2020-12-08 to 2020-12-11. Its published northern extent stops at 39.2381837 N, just south of the referenced Masonville Cove location, so it cannot be promoted to a same-footprint post surface.

### Tangerine Landfill

Pima County states that Tangerine was legally closed in December 2016 and that closure included three feet of soil cover. Other public records place the end of waste acceptance in 2013.

The 2015 PAG lidar was acquired in March 2015, therefore its timing is excellent for a pre-cover surface. Its published vertical-accuracy assessment reports RMSEz = 0.0976 m for 260 checkpoints.

USGS documents a PAG 2021 Regional QL1 acquisition and PAG confirms 2021 lidar is publicly available. However, the USGS project description says the 2021 project includes previously unacquired regions of Pima County, and the publicly accessible metadata inspected here did not prove that the Tangerine footprint itself was re-flown. Under the maximum-three-fingerprint rule, the candidate is dropped rather than assumed to have coverage.

### Yolo reserve

Yolo was re-opened immediately because all four F192 survivors failed.

The official WMU 4/5 closure documents are scientifically interesting: they state that WMUs 4 and 5 resumed waste acceptance to reach final grades, specify a multi-layer final-cover system, require as-built surveys to document protective-cover thickness, and state that cover quantity is measured as the difference between preconstruction/subgrade and final surveys.

That is strong survey provenance, but it does not rescue the lidar route. The public lidar epochs recovered here do not prove the required narrow sequence: final waste grade -> pre-lidar -> cover placement -> post-lidar.

## F193 decision

**FAIL / ZERO SURVIVORS.**

No candidate proves a valid public lidar bracket after adding the final-waste-placement condition.

This is not an accuracy failure. It is a timing/coverage failure.

The filter prevented exactly the failure mode it was designed to stop: subtracting an older surface that still includes later waste placement or grading and then mislabeling the result as cover thickness.

## Next action — F194

Apply the pre-agreed stop rule.

Because F193 produced zero valid lidar pairs, there are zero candidates on which to perform the F194 error-budget arithmetic. Therefore fewer than two sites can survive F194 by definition.

Do not launch another generic cap-site search. Record the route as closed on current free public lidar evidence and keep the separate recorded-measurement / Option 5 paths distinct.
