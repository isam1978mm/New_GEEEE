# Vista Pointe Area B-Area C cross-closure depth-pair result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Area B and Area C initially looked like a strong full-scale pair. Both are large vegetated closure areas, and their nominal cover depths differ by 1 foot.

The pair still fails the approved numerical-depth plan because the material immediately below the vegetated surface is different. A Sentinel-1 difference would not isolate depth.

## Why it looked promising

- **Area B:** approximately 12 acres, certified closed in 1993, with 3 feet of vegetative cover soil.
- **Area C:** approximately 16.3 acres, eastern portion certified closed in 2021, with a 2-foot vegetated cap.
- Nominal depth contrast: **1.0 ft / 0.3048 m**.
- Both areas are physically large enough in principle to retain a 30-40 m clean interior after reasonable exclusions.
- Later reports describe post-closure vegetation maintenance.

## Fatal blocker: the cap materials do not match

### Area B profile

The recovered 1993 closure package describes:

- upper 12 inches: a blend of farm/topsoil, sand and composted leaves;
- lower 24 inches: sand.

### Area C profile

The later closure records describe:

- upper 12 inches: vegetative cover soil;
- lower 12 inches: slag fines.

These are not the same near-surface assembly. Soil, sand, compost and slag can differ in moisture retention, texture, drainage and radar response.

Therefore, a radar difference between Area B and Area C could be caused by the different materials rather than the 1-foot cover-depth difference.

This cannot be fixed by drawing different polygons.

## Secondary depth-evidence limitation

The Area B package contains professional closure certification, an aerial survey of the prepared subbase, and coordinate-labelled final-grade drawings.

However, the recovered public package does not publish:

- a point-by-point final cover-thickness grid;
- a coordinate table tying final thickness values to specific interior cells;
- numerical horizontal or vertical survey uncertainty.

The documents support the certified 3-foot construction specification, but not an execution-ready measured-depth polygon under the app's approved calibration gate.

## Calibration decision

```text
full-scale vegetated areas = yes
30-40 m clean interior possible in principle = yes
nominal depth contrast = 1.0 ft / 0.3048 m
same near-surface assembly = no
coordinate-labelled final-grade drawings = yes
pointwise final thickness grid = no
numerical survey uncertainty = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_SURFACE_ASSEMBLY_AND_DEPTH_GRID_FAILED
```

## Sources reviewed

- 1993 Area B landfill closure certification and quality-assurance package.
- 2023 Cleveland-Cliffs Cleveland Works 10-Year Design Demonstration report.
- 2023 and 2025 Vista Pointe/Cleveland Works annual operational and post-closure records.
- Ohio EPA public eDocument records recovered through temporary PR #15.

## Next step

Continue the approved search unchanged. Advance only a full-scale vegetated pair with matching near-surface construction, coordinate-tied final measured depths, at least 30-40 m clean interior, and a stable Sentinel-1 observation period.
