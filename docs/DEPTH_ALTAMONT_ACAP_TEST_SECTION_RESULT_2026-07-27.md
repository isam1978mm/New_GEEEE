# Altamont ACAP test-section result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Altamont was checked after Omaha because its published alternative-cover top deck is 30 m by 30 m and therefore does not automatically fail the 20 m width gate.

The recovered record confirms that the alternative test section was constructed in 2000 with:

- 150 mm surface soil;
- 910 mm water-storage soil;
- 300 mm interim cover;
- 1.36 m total profile;
- a mixture of grasses;
- a 30 m by 30 m top deck;
- a central 10 m by 20 m pan lysimeter.

## Fatal problem - not a depth-only comparison

The ACAP comparison at Altamont was not the same buried target installed at two depths.

It compared:

- a monolithic evapotranspiration soil cover; and
- a conventional membrane-composite / compacted-clay cover.

Those systems differ in material, layering, hydraulic behavior and buried interfaces. Therefore a Sentinel-1 difference could not be assigned to cover depth. It could instead reflect the membrane, compacted clay, drainage behavior, moisture distribution or construction differences.

This is a fundamental experimental confounder and cannot be fixed by improving the polygons.

## Geometry and timing

The 30 m by 30 m alternative top deck is nominally large enough in principle. However:

- the authoritative instrumented lysimeter is only 10 m wide;
- exact WGS84 polygons for both original ACAP sections were not recovered;
- numerical boundary uncertainty was not recovered;
- public records do not prove that the original plots remained unchanged through a usable Sentinel-1 period;
- Altamont remained an active landfill with later closure and construction activity.

The regulatory record also says the original ACAP performance was less than desirable and required a later full-scale monitored alternative-cover program. That later cover is not the original side-by-side depth experiment.

## Calibration decision

```text
measured alternative-cover profile = yes
alternative top-deck width = 30 m
same buried material system = no
depth-only contrast = no
instrumented width = 10 m
exact WGS84 pair = no
numerical boundary uncertainty = no
Sentinel-1-era survival = not confirmed
calibration row created = no
Earth Engine query executed = no
app depth enabled = no
```

Final decision:

```text
NOT_GOOD_TO_GO_COVER_ARCHITECTURE_CONFOUNDER_AND_SURVIVAL_UNCONFIRMED
```

## Sources reviewed

- *Field Data and Water-Balance Predictions for a Monolithic Cover in a Semiarid Climate*.
- U.S. EPA, *Evapotranspiration Landfill Cover Systems Fact Sheet*.
- CLU-IN, *Monolithic Evapotranspiration at Altamont Landfill Full Scale, CA*.
- California CIWQS facility and regulatory records for Altamont Landfill.

## Next step

Do not continue through standard ACAP side-by-side trials unless the two sections use the same buried materials and differ primarily in thickness. Most standard trials compare alternative and conventional cover architectures, which is not an honest depth-ordering experiment.

Return to completed remediation or closure projects with large same-surface zones and final as-built depth grids. Prioritize projects where one construction contract used the same soil and vegetation assembly over surveyed cells with materially different measured thicknesses.
