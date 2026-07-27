# Huron River Properties cap-depth support result - 2026-07-27

## Decision

**NOT GOOD TO GO**

The Huron Lime Landfill 1 and Landfill 2 reports contain real cap-thickness measurements, exact WGS84 boring coordinates, clayey cap material, and established vegetation. They are useful engineering evidence, but they do not satisfy the approved numerical-depth plan.

The approved plan remains unchanged:

- full-scale vegetated cover zones only;
- at least 30-40 m clean interior width after boundaries and infrastructure;
- final measured as-built depths;
- no small plots and no analyst-invented depth polygons.

## Landfill 1

The approximately 15.6-acre landfill was investigated with 16 borings, about one per acre.

Measured cap thicknesses were:

```text
6.5, 11, 11, 14, 14, 16, 16, 16, 16,
18.5, 18.5, 20.5, 21, 22, 24, and 39.5 inches
```

The report provides an interpolated cap-thickness isopach map, not final construction as-built depth cells.

A coordinate calculation from the published WGS84 boring table shows:

```text
minimum nearest-neighbor spacing = 47.55 m
maximum nearest-neighbor spacing = 75.83 m
```

Therefore a proposed 30-40 m shallow or deep zone cannot be independently bounded by multiple nearby measurements. The colored isopach areas mainly fill the large spaces between sparse borings.

No numerical interpolation uncertainty or isopach-boundary uncertainty is provided.

## Landfill 2

The approximately 14-acre landfill was investigated with 15 borings.

The report states that valid cap thicknesses ranged from 6 to 18 inches and averaged about 10 inches. The valid measured points have nearest-neighbor spacings of approximately 31.13 to 47.10 m.

Several table entries show 60 inches, but the map labels those locations as `Note 1`: fill material was not encountered in the boring. They do not establish surveyed 60-inch cap zones.

The map nevertheless displays greater-than-24-inch interpolated areas near boundaries. Those areas are not supported by measured deep-cap points and cannot be used as depth polygons.

## Fatal problem

These reports are supplemental point-boring investigations, not final construction as-built thickness surveys.

The maps cannot establish conservative, exact 30-40 m depth zones because:

1. measurements are sparse;
2. the colored zones are interpolated;
3. no numerical interpolation or boundary uncertainty is supplied;
4. Landfill 2 has no defensible measured deep zone;
5. converting the colored areas directly to polygons would create unsupported geometry.

## Calibration decision

```text
full-scale vegetated surface = yes
real measured cap thicknesses = yes
exact boring coordinates = yes
final as-built depth grid = no
30-40 m depth zone supported by multiple measurements = no
numerical zone-boundary uncertainty = no
usable calibration row created = no
Earth Engine query executed = no
app depth enabled = no
```

Final decision:

```text
NOT_GOOD_TO_GO_SPARSE_POINT_SUPPORT_AND_NO_FINAL_AS_BUILT_DEPTH_ZONES
```

## Next step

Continue the approved search only with completed full-scale closure packages that provide final construction survey measurements or certified thickness cells wide enough to retain 30-40 m clean interiors after margins.
