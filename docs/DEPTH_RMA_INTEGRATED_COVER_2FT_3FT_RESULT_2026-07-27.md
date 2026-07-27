# RMA Integrated Cover System 2-ft/3-ft depth-pair result - 2026-07-27

## Decision

**NOT GOOD TO GO**

This is the strongest full-scale vegetated depth-pair pattern found in the current search, but it still fails the app's locked calibration gate.

The official annual reports and maps prove that the maintained cover system contains large 2-foot and 3-foot soil-cover polygons. They do not provide coordinate-tied absolute final measured depths for the 2-foot polygons, numerical survey uncertainty, or final proof that the radar-facing upper-soil construction matches between the two cover types.

## Why it looked promising

The recovered 2022-2025 Annual Covers Reports show:

- a completed full-scale Integrated Cover System;
- construction completed in early 2010;
- separate RCRA-equivalent, 2-foot and 3-foot cover polygons;
- a current coordinate-labelled map;
- map projection identified as NAD27/NGVD29, US survey feet, State Plane Colorado North FIPS 0501;
- broad 2-foot and 3-foot zones that are large enough in principle to retain 30-40 m clean interiors;
- the 2-foot and 3-foot covers evaluated together as one vegetation group;
- recurring inspection, vegetation management, percolation monitoring and cover maintenance.

The nominal contrast is:

```text
3.0 ft - 2.0 ft = 1.0 ft
1.0 ft = 0.3048 m
```

## Geometry result

The 2025 Integrated Cover System maintenance map shows the cover-category boundaries against a State Plane coordinate grid.

This is stronger than an approximate site sketch. It demonstrates that large 2-foot and 3-foot polygons exist and that their boundaries are maintained in a coordinate system.

No WGS84 execution polygons were created because the measured-depth gate did not pass.

## Stability result

The annual reports document continuing long-term operation and maintenance. The covers are repeatedly inspected and evaluated for vegetation, drainage, erosion, settlement and percolation.

This supports a potentially stable Sentinel-1 observation period. Local maintenance areas would still need to be excluded from any future execution polygons.

Stability is not the main blocker.

## Fatal blocker 1: the current values are cover categories, not absolute final measurements

The current map labels areas as 2-foot and 3-foot soil covers. Those labels establish the intended or maintained cover category.

The recovered public documents do not publish:

- absolute final measured thickness values for the 2-foot polygons;
- a point-by-point final as-built thickness grid spanning both cover types;
- a coordinate table linking each usable interior cell to an absolute measured depth;
- a final subgrade-versus-finished-grade comparison for both zones.

The nominal labels therefore cannot be entered as measured calibration depths under the locked plan.

## Fatal blocker 2: the monument measurements are loss measurements

The annual reports describe 92 erosion/settlement monuments, generally placed on a 500-foot grid, for the RCRA-equivalent and 3-foot cover areas.

The reported values are localized **cover-soil-thickness loss** measurements. They do not provide the original absolute as-built depth at each point.

The network also does not provide an equivalent absolute measured-depth grid for the 2-foot polygons.

Therefore, the monitoring table cannot be converted into a 2-foot-versus-3-foot calibration dataset.

## Fatal blocker 3: numerical uncertainty is missing

The recovered public records do not state numerical horizontal or vertical survey uncertainty for the mapped depth polygons.

A coordinate grid by itself does not satisfy the app's uncertainty requirement.

## Fatal blocker 4: matching final upper-soil construction is not proven

The 2-foot and 3-foot areas are evaluated together for vegetation, which is encouraging.

However, the recovered public records do not prove that their final radar-facing layers used the same:

- soil source;
- gradation;
- compaction;
- amendment mixture;
- drainage behavior;
- moisture-retention behavior.

The earlier remedy concept described a common upper soil layer, but the final construction/as-built package was not recovered. The app requires final construction proof, not an assumption from the earlier design.

## Public-record recovery result

The search recovered:

- 2022 Annual Covers Report;
- 2023 Annual Covers Report;
- 2024 Annual Covers Report;
- 2025 Annual Covers Report;
- current coordinate-labelled cover and maintenance maps.

The following named records were not recovered:

- *RCRA-Equivalent, 2-, and 3-Foot Covers Long-Term Care Plan*, Revision 3, August 12, 2021;
- the 2000 South Plants environmental remedy modification;
- the 2001 South Plants Phase 2 100 Percent Design Package;
- a final cover construction-completion or as-built survey package.

They were not found through:

- the current Army environmental reports pages;
- the EPA live document table;
- the archived public-site search.

## Calibration decision

```text
full-scale vegetated areas = yes
large 2-ft and 3-ft polygons = yes
30-40 m clean interior possible in principle = yes
coordinate-labelled current map = yes
nominal depth contrast = 1.0 ft / 0.3048 m
shared vegetation assessment group = yes
stable monitored surface supported in principle = yes
coordinate-tied absolute final measured depths = no
absolute measured-depth grid for 2-ft polygons = no
numerical survey uncertainty = no
matching final upper-soil construction proven = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_PUBLIC_ASBUILT_AND_ABSOLUTE_DEPTH_MISSING
```

## Sources reviewed

- 2022 Annual Covers Report for Integrated Cover System.
- 2023 Annual Covers Report for Integrated Cover System.
- 2024 Annual Covers Report for Integrated Cover System.
- 2025 Annual Covers Report for Integrated Cover System.
- Current Army environmental reports index.
- EPA public site document table.
- Temporary GitHub recovery PR #17 artifacts.

## Next step

Continue the approved search unchanged. Advance only a full-scale vegetated pair whose public construction package provides coordinate-tied absolute final measured depths, numerical uncertainty, matching upper-soil construction, at least 30-40 m clean interior and a stable Sentinel-1 period.
