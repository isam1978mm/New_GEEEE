# McMaster Street As-Built Pixel-Support Result — 2026-07-27

## Decision

```text
NOT GOOD TO GO FOR THE CURRENT 20 M SENTINEL-1 DEPTH TEST
```

The official New York DEC Final Engineering Report was recovered and its final as-built summary drawings were inspected. McMaster Street has a uniform Type F crusher-stone upland surface and a documented Phase 3 area where reuse material remains below a geotextile demarcation layer.

The site does not provide a defensible clean 20 m depth pair. The Phase 3 buried-target area is an irregular wedge constrained and crossed by sanitary and storm sewers, multiple manholes, retaining walls, monitoring/NAPL infrastructure, the railroad edge, and the site boundary. Phase 1 does not supply a same-interface shallow condition because complete removal was performed there and no demarcation geotextile was installed.

No Earth Engine query was run and no calibration row was created.

## Evidence recovered

```text
Final Engineering Report = recovered
Final as-built site-layout drawing = recovered
Remaining-impact/reuse-soil/geotextile plan and profiles = recovered
Upland final surface = Type F crusher stone
Phase 3 reuse material = retained below geotextile
Minimum Phase 3 reuse-material depth below final grade = greater than 2 ft
Upland property area = approximately 1.93 acres
```

## Potential comparison checked

The apparent comparison was:

```text
possible shallow/control = Phase 1
possible deep/positive = Phase 3 reuse material beneath geotextile
```

That pair is not valid as a clean depth-ordering pair.

Phase 1 was excavated and restored with imported material. The report states that no demarcation layer was installed there because removal was complete. Phase 3 contains the reuse material and geotextile interface.

Therefore the two areas do not represent the same buried interface at different depths. They represent different subsurface remediation conditions.

## Geometry and infrastructure screen

The as-built Figure 4 plan and profiles show the Phase 3 target as an irregular triangular/wedge-shaped area. The plan also maps:

```text
sanitary sewer
storm sewer
multiple manholes
retaining walls
railroad edge
site boundary
monitoring wells and NAPL infrastructure
```

These features cross or closely constrain the target area. The recovered drawing does not support two separate same-surface, same-interface execution polygons that each contain a clean 20 m Sentinel-1 interior after exclusions and uncertainty margins.

```text
exact clean shallow polygon = no
exact clean deep polygon = no
two clean 20 m depth zones = no
pixel-support decision = HOLD_CLEAN_20M_TARGET_PAIR_NOT_SUPPORTED
```

No analyst-estimated boundary or interpolation outside the documented target was used.

## What remains valid

```text
professional final as-built evidence = yes
uniform crusher-stone surface = yes
Phase 3 buried reuse condition = yes
Phase 3 depth greater than 2 ft = yes
```

## What is not approved

```text
same buried interface in Phase 1 and Phase 3 = no
clean 20 m shallow zone = no
clean 20 m deep zone = no
WGS84 execution geometry = no
Sentinel-1 catalogue query = no
Earth Engine query = no
calibration row = no
numerical depth training = no
app depth output = no
```

## Machine-readable result

```text
data/mcmaster_street_asbuilt_pixel_support_result.json
```

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
mcmaster_same_surface = yes
mcmaster_same_buried_interface_pair = no
mcmaster_clean_20m_pair = no
mcmaster_calibration_row_ready = no
```

## Next step

Continue only with a larger completed site whose final as-built package establishes the same buried interface beneath the same final surface in two broad, non-overlapping depth zones, each wider than 20 metres after all exclusions and uncertainty margins.
