# Keystone Sanitation Landfill cover-grid result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Keystone initially looked unusually promising because the approved remedy required a grid-based investigation of existing cover thickness. Thin areas were to be upgraded to at least two feet while retaining a common vegetated erosion layer.

The candidate fails because the mapped cover did not remain physically stable during the Sentinel-1 period.

## Why it looked promising

The 2000 Record of Decision Amendment required:

- investigation of the existing soil-cover thickness;
- a representative grid sampling approach;
- identification of areas needing upgrades;
- upgrading areas with less than two feet of cover;
- an 18-inch low-permeability soil layer where required;
- a minimum six-inch erosion layer;
- final vegetation.

The landfill is approximately 40 acres, so clean 30-40 m interior areas could exist in principle.

## Fatal blocker

The 2025 Five-Year Review reports:

- ponding on the landfill cover;
- areas of subsidence;
- increasingly large stands of woody vegetation;
- repairs to subsided areas on two occasions;
- continuing cover monitoring;
- further source-control alternatives still under evaluation.

These are not minor documentary gaps. They mean the original grid-defined depth zones and final surface conditions did not remain unchanged.

A radar observation could reflect:

- settlement;
- repair fill;
- changed drainage;
- standing water;
- tree and shrub growth;
- altered soil moisture;
- later construction and monitoring work.

The historical grid therefore cannot be converted into a stable Sentinel-1 calibration map.

## Calibration decision

```text
full-scale vegetated area = yes
historical thickness grid required by design = yes
public final coordinate-tied as-built grid recovered = no
stable Sentinel-1 period = no
mapped zones remained physically unchanged = no
matching surface conditions = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_SENTINEL1_ERA_COVER_CHANGED
```

## Sources reviewed

- EPA 2000 Record of Decision Amendment.
- EPA Sixth Five-Year Review Report, 2025.
- EPA current Keystone Sanitation Landfill site profile.

## Next step

Continue the approved search unchanged. Reject any historical cover-thickness grid whose mapped areas were subsequently repaired, regraded, wooded or otherwise altered during the Sentinel-1 observation period.
