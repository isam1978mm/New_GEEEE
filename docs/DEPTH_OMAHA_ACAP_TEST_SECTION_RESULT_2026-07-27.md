# Omaha ACAP test-section result - 2026-07-27

## Decision

**NOT GOOD TO GO**

The Omaha ACAP facility initially looked unusually strong because it contains side-by-side covers with:

- a thin capillary-barrier cover approximately 0.76 m thick;
- a thick capillary-barrier cover approximately 1.06 m thick;
- a nominal thickness difference of approximately 0.30 m;
- grass vegetation on both test sections.

That is the correct experimental idea for a shallow-versus-deep radar comparison.

## Fatal problem - no clean 20 m radar footprint

Published ACAP geometry describes each test section as:

- 20 m wide;
- 30 m long;
- containing a central pan lysimeter only 10 m wide by 20 m long;
- bounded by berms and monitoring infrastructure.

The project requires a clean 20 m analysis footprint that remains inside one condition after applying boundary and geolocation margins.

The Omaha top deck is exactly 20 m wide. Therefore:

- a 20 m footprint would consume the complete width with zero safety margin;
- any berm, edge, coordinate uncertainty, mixed-pixel effect or inward buffer makes the usable width less than 20 m;
- the authoritative instrumented lysimeter is only 10 m wide.

This is a physical pixel-support failure. Better georeferencing cannot create additional width.

## Other unresolved gates

Even without the width failure, the currently recovered public record does not establish:

- exact WGS84 polygons for the individual test sections;
- numerical boundary uncertainty;
- that the original 2000-era plots remained intact throughout a usable Sentinel-1 observation period;
- freedom from later disturbance at the active landfill facility.

These are secondary because the 20 m width failure already closes the route.

## Calibration decision

```text
measured depth contrast = yes
same broad surface type = yes, grasses
full test-section width = 20 m
clean 20 m interior after margins = no
exact WGS84 polygons = no
Sentinel-1-era survival = not confirmed
calibration row created = no
Earth Engine query executed = no
app depth enabled = no
```

Final decision:

```text
NOT_GOOD_TO_GO_PIXEL_SUPPORT_FAIL
```

## Sources reviewed

- Apiwantragoon, P., Benson, C. H., and Albright, W. H. (2014), *Field Hydrology of Water Balance Covers for Waste Containment*.
- Benson, C. H., Sawangsuriya, A., Trzebiatowski, B., and Albright, W. H. (2007), *Postconstruction Changes in the Hydraulic Properties of Water Balance Cover Soils*.
- U.S. EPA, *Fact Sheet on Evapotranspiration Cover Systems for Waste Containment*.

## Next step

Inspect the Altamont ACAP facility because its published monolithic test section is 30 m by 30 m, so it does not automatically fail the same width gate. It advances only if the conventional comparison section has a comparable grass-facing surface, exact recoverable geometry, and confirmed survival into the Sentinel-1 period.
